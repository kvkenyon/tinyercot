"""Exercise the client's real retry policy with a mocked network transport."""

import json

import httpx
import pytest
from httpx_retries import RetryTransport

from tinyercot import Client


@pytest.mark.parametrize("kind", ["archive", "bundle"])
@pytest.mark.parametrize("status", [429, 503])
def test_download_retries_keep_ids_and_respect_retry_after(monkeypatch, kind, status):
    attempts = []
    sleeps = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        assert request.method == "POST"
        assert request.url.path == f"/api/public-reports/{kind}/np4-745-cd/download"
        attempts.append(json.loads(request.content))
        if len(attempts) == 1:
            return httpx.Response(status, headers={"Retry-After": "2"})
        return httpx.Response(200, content=b"downloaded archive")

    monkeypatch.setattr(
        "tinyercot._client.RetryTransport",
        lambda *, retry: RetryTransport(httpx.MockTransport(handler), retry=retry),
    )
    monkeypatch.setattr("httpx_retries.retry.time.sleep", sleeps.append)
    with Client("u", "p", "k") as client:
        assert (
            client.download("np4-745-cd", [12, 34], kind=kind) == b"downloaded archive"
        )
    assert attempts == [{"docIds": [12, 34]}] * 2
    assert sleeps == [2.0]


@pytest.mark.parametrize("status,expected_attempts", [(429, 6), (400, 1)])
def test_download_failures_remain_bounded(monkeypatch, status, expected_attempts):
    attempts = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        attempts.append(request.content)
        return httpx.Response(status, headers={"Retry-After": "1"})

    monkeypatch.setattr(
        "tinyercot._client.RetryTransport",
        lambda *, retry: RetryTransport(httpx.MockTransport(handler), retry=retry),
    )
    monkeypatch.setattr("httpx_retries.retry.time.sleep", lambda _: None)
    with (
        Client("u", "p", "k") as client,
        pytest.raises(httpx.HTTPStatusError) as error,
    ):
        client.download("np4-745-cd", [12])
    assert error.value.response.status_code == status
    assert len(attempts) == expected_attempts
