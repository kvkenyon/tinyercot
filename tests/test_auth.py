import asyncio
import logging
import unittest
from urllib.parse import parse_qs

import httpx

import tinyercot
from tinyercot import _client


class TestAuthFormBody(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_client = _client._client
        self._orig_async_client = _client._async_client
        _client.configure(username=None, password=None, subscription_key=None)

    def tearDown(self) -> None:
        _client._client = self._orig_client
        _client._async_client = self._orig_async_client
        _client.configure(username=None, password=None, subscription_key=None)

    def test_token_sends_credentials_in_form_body_not_url_or_httpx_logs(self) -> None:
        captured: list[httpx.Request] = []
        secret_user = "alice+ercot@example.com"
        secret_pass = "p@ss&w0rd#100%+secret"

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"id_token": "tok-abc"})

        _client._client = httpx.Client(transport=httpx.MockTransport(handler))
        tinyercot.configure(
            username=secret_user,
            password=secret_pass,
            subscription_key="sub-key-secret",
        )

        with self.assertLogs("httpx", level=logging.INFO) as logs:
            token = _client._token()

        self.assertEqual(token, "tok-abc")
        self.assertEqual(len(captured), 1)
        req = captured[0]

        # URL must have no query string or credentials
        self.assertEqual(req.method, "POST")
        self.assertEqual(str(req.url), _client.TOKEN_URL)
        self.assertEqual(req.url.query, b"")
        self.assertNotIn(secret_user, str(req.url))
        self.assertNotIn(secret_pass, str(req.url))

        # Body must be application/x-www-form-urlencoded with expected OAuth2 ROPC fields
        self.assertEqual(
            req.headers["content-type"], "application/x-www-form-urlencoded"
        )
        form = parse_qs(req.content.decode("utf-8"), strict_parsing=True)
        self.assertEqual(
            form,
            {
                "username": [secret_user],
                "password": [secret_pass],
                "grant_type": ["password"],
                "scope": [f"openid {_client.CLIENT_ID} offline_access"],
                "client_id": [_client.CLIENT_ID],
                "response_type": ["id_token"],
            },
        )

        # httpx logs must not leak username, password, or subscription key
        combined_logs = "\n".join(logs.output)
        self.assertIn(_client.TOKEN_URL, combined_logs)
        self.assertNotIn(secret_user, combined_logs)
        self.assertNotIn(secret_pass, combined_logs)
        self.assertNotIn("sub-key-secret", combined_logs)

    def test_token_http_error_raises_without_leaking_credentials_or_caching_none(
        self,
    ) -> None:
        secret_user = "bob@example.com"
        secret_pass = "super-secret-password"
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(400, json={"error": "invalid_grant"})

        _client._client = httpx.Client(transport=httpx.MockTransport(handler))
        tinyercot.configure(
            username=secret_user,
            password=secret_pass,
            subscription_key="sub-key",
        )

        with self.assertRaises(httpx.HTTPStatusError) as ctx:
            _client._token()

        err_text = str(ctx.exception)
        self.assertNotIn(secret_user, err_text)
        self.assertNotIn(secret_pass, err_text)
        self.assertEqual(len(_client._tok_cache), 0)
        self.assertEqual(calls, 1)

    def test_get_and_aget_send_auth_in_headers_only(self) -> None:
        requests_seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests_seen.append(request)
            if request.url.host == "ercotb2c.b2clogin.com":
                return httpx.Response(200, json={"id_token": "jwt-token-123"})
            return httpx.Response(200, json={"data": [["HB_HOUSTON", 42.5]]})

        _client._client = httpx.Client(transport=httpx.MockTransport(handler))
        _client._async_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )
        tinyercot.configure(
            username="u@example.com",
            password="p-secret",
            subscription_key="sub-secret",
        )

        sync_resp = _client._get(
            "np4-190-cd/dam_stlmnt_pnt_prices",
            schema={"settlementPoint": "VARCHAR", "price": "DOUBLE"},
            settlementPoint="HB_HOUSTON",
        )
        async_resp = asyncio.run(
            _client._aget(
                "np4-190-cd/dam_stlmnt_pnt_prices",
                schema={"settlementPoint": "VARCHAR", "price": "DOUBLE"},
                settlementPoint="HB_HOUSTON",
            )
        )

        self.assertEqual(
            sync_resp["data"], [{"settlementPoint": "HB_HOUSTON", "price": 42.5}]
        )
        self.assertEqual(async_resp["data"], sync_resp["data"])

        # Token fetched once (cached), followed by sync GET and async GET
        self.assertEqual(len(requests_seen), 3)
        for req in requests_seen:
            url_str = str(req.url)
            self.assertNotIn("u@example.com", url_str)
            self.assertNotIn("p-secret", url_str)
            self.assertNotIn("sub-secret", url_str)
            self.assertNotIn("jwt-token-123", url_str)

        for api_req in requests_seen[1:]:
            self.assertEqual(api_req.headers["authorization"], "Bearer jwt-token-123")
            self.assertEqual(api_req.headers["ocp-apim-subscription-key"], "sub-secret")


if __name__ == "__main__":
    unittest.main()
