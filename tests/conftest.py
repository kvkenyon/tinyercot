"""Unit tests use synthetic credentials and forbid network connections."""

import socket

import pytest

from tinyercot import _client


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Keep each test isolated from real credentials, tokens, and sockets.

    Args:
        monkeypatch: Pytest patch manager for test-scoped state.

    Yields:
        Control with network connections disabled.
    """

    def deny_network(*args, **kwargs):
        raise AssertionError("Network access is forbidden in offline tests")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    for name in ("ERCOT_USERNAME", "ERCOT_PASSWORD", "ERCOT_SUBSCRIPTION_KEY"):
        monkeypatch.delenv(name, raising=False)
    _client.configure()
    yield
    _client.configure()
