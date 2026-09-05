import datetime
from email.utils import format_datetime

import httpx
import pytest

from tinyercot.public import LimitError, Limits, RateLimitError, SourceUnavailableError
from tinyercot.public._http import _HTTP


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_bounded_retry_honors_wait_and_no_terminal_sleep(status):
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Retry-After": "3"})

    client = _HTTP(
        Limits(min_interval=0), httpx.MockTransport(handler), sleep=sleeps.append
    )
    try:
        with pytest.raises(RateLimitError if status == 429 else SourceUnavailableError):
            client.request("GET", "https://www.ercot.com/test")
        assert len(calls) == 3 and sleeps == [3, 3]
    finally:
        client.close()


def test_retry_after_http_date_and_excessive_wait():
    client = _HTTP(Limits())
    try:
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=20)
        assert 18 <= client._retry_delay(format_datetime(future, usegmt=True), 0) <= 20
        with pytest.raises(RateLimitError):
            client._retry_delay("120", 0)
        with pytest.raises(RateLimitError):
            client._retry_delay("NaN", 0)
    finally:
        client.close()


def test_request_budget_byte_budget_and_pacing():
    sleeps, calls = [], []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=b"1234")

    client = _HTTP(
        Limits(max_requests=2, max_bytes=3),
        httpx.MockTransport(handler),
        clock=lambda: 0,
        sleep=sleeps.append,
    )
    try:
        for _ in range(2):
            with pytest.raises(LimitError, match="byte"):
                client.request("GET", "https://www.ercot.com/test")
        with pytest.raises(LimitError, match="request"):
            client.request("GET", "https://www.ercot.com/test")
        assert sleeps == [2.1] and len(calls) == 2
    finally:
        client.close()


def test_transport_error_is_redacted():
    def error(request):
        raise httpx.ReadTimeout("synthetic-secret", request=request)

    client = _HTTP(Limits(attempts=1), httpx.MockTransport(error))
    try:
        with pytest.raises(SourceUnavailableError) as caught:
            client.request(
                "POST",
                "https://example.test/token",
                data={"password": "synthetic-secret"},
                authentication=True,
            )
        assert "synthetic-secret" not in str(caught.value)
        assert caught.value.__context__ is None
    finally:
        client.close()


def test_interrupted_auth_body_retries_without_retaining_partial_token():
    class BrokenBody(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"id_token":"synthetic-partial'
            raise httpx.ReadTimeout("synthetic-secret")

    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, stream=BrokenBody())
        return httpx.Response(200, json={"id_token": "synthetic-complete"})

    client = _HTTP(
        Limits(min_interval=0), httpx.MockTransport(handler), sleep=sleeps.append
    )
    try:
        result = client.request(
            "POST", "https://example.test/token", authentication=True
        )
        assert result.json() == {"id_token": "synthetic-complete"}
        assert result.receipt.sha256 == "" and result.receipt.byte_count == 0
        assert len(calls) == 2 and sleeps == [1]
    finally:
        client.close()


def test_redirect_is_not_followed():
    calls = []

    def redirect(request):
        calls.append(request)
        return httpx.Response(
            302, headers={"Location": "https://restricted.example.test"}
        )

    client = _HTTP(Limits(), httpx.MockTransport(redirect))
    try:
        with pytest.raises(SourceUnavailableError):
            client.request("GET", "https://www.ercot.com/test")
        assert len(calls) == 1
    finally:
        client.close()
