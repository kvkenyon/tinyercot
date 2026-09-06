"""Bounded HTTP and safe errors for the opt-in public adapters."""

import datetime
import hashlib
import json
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


class PublicDataError(Exception):
    """An opt-in retrieval cannot return a verified public result."""


class AuthenticationError(PublicDataError):
    """Public API authentication failed without disclosing response details."""


class AccessDeniedError(PublicDataError):
    """The source denied access; no entitlement workaround is attempted."""


class SchemaMismatchError(PublicDataError):
    """A response differs from the supported observed source contract."""


class LimitError(PublicDataError):
    """A request, byte, page, or archive limit was reached."""


class RateLimitError(PublicDataError):
    """The rate limit exceeds the configured retry budget."""


class SourceUnavailableError(PublicDataError):
    """A source did not return the requested public data."""


@dataclass(frozen=True)
class Limits:
    """Caller-selected ceilings for one adapter instance.

    Attributes:
        max_requests: Total HTTP attempts, including authentication and retries.
        max_bytes: Maximum decoded bytes in each HTTP response.
        attempts: Maximum attempts per HTTP operation.
        min_interval: Minimum seconds between request starts.
        max_retry_wait: Maximum accepted server-directed retry delay.
    """

    max_requests: int = 20
    max_bytes: int = 4_000_000
    attempts: int = 3
    min_interval: float = 2.1
    max_retry_wait: float = 60.0

    def __post_init__(self) -> None:
        if (
            type(self.max_requests) is not int
            or type(self.attempts) is not int
            or not 1 <= self.max_requests <= 100
            or not 1 <= self.attempts <= 5
        ):
            raise ValueError("Request limits must be positive and bounded")
        if type(self.max_bytes) is not int or not 1 <= self.max_bytes <= 16_000_000:
            raise ValueError("max_bytes must be between 1 and 16000000")
        if not math.isfinite(self.min_interval) or self.min_interval < 0:
            raise ValueError("min_interval must be finite and nonnegative")
        if not math.isfinite(self.max_retry_wait) or self.max_retry_wait < 0:
            raise ValueError("max_retry_wait must be finite and nonnegative")


@dataclass(frozen=True)
class StreamingLimits:
    """Opt-in transport limits without a permanent total-request ceiling.

    Attributes:
        max_requests: Attempt budget, or None to permit complete caller queries.
        max_bytes: Per-response decoded byte ceiling.
        attempts: Attempts per request, including retries.
        min_interval: Seconds between request starts.
        max_retry_wait: Maximum server-directed wait in seconds.
    """

    max_requests: int | None = 100
    max_bytes: int = 4_000_000
    attempts: int = 3
    min_interval: float = 2.1
    max_retry_wait: float = 60.0

    def __post_init__(self) -> None:
        if self.max_requests is not None and (
            type(self.max_requests) is not int or self.max_requests < 1
        ):
            raise ValueError("max_requests must be positive or None")
        Limits(1, self.max_bytes, self.attempts, self.min_interval, self.max_retry_wait)


@dataclass(frozen=True)
class Receipt:
    """Public payload identity without credentials or response headers.

    Attributes:
        source_url: Public source URL with public query parameters only.
        retrieved_at: UTC retrieval time, separate from source publication time.
        sha256: Hash of the decoded response bytes.
        byte_count: Number of decoded bytes hashed.
        status: HTTP success status.
    """

    source_url: str
    retrieved_at: datetime.datetime
    sha256: str
    byte_count: int
    status: int = 200


@dataclass(frozen=True)
class Payload:
    """Bounded bytes and their receipt for internal source decoding.

    Attributes:
        body: Complete decoded response bytes within the byte ceiling.
        receipt: Public source identity and retrieval time.
    """

    body: bytes = field(repr=False)
    receipt: Receipt

    def json(self) -> Any:
        """Decode JSON without including source bytes in an error.

        Returns:
            The decoded JSON value, with decimals preserved.

        Raises:
            SchemaMismatchError: The response is not valid JSON.
        """
        from decimal import Decimal

        try:
            return json.loads(self.body, parse_float=Decimal)
        except (ValueError, UnicodeError):
            pass
        raise SchemaMismatchError("Source returned invalid JSON")


class _HTTP:
    """Own a synchronous transport with a finite shared attempt budget."""

    def __init__(
        self,
        limits: Limits | StreamingLimits,
        transport: httpx.BaseTransport | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create the bounded transport without a network request.

        Args:
            limits: Attempt, byte, and wait ceilings for this instance.
            transport: Optional mocked HTTPX transport.
            sleep: Wait function, replaceable by an offline test.
            clock: Monotonic clock used for pacing and token lifetime.
        """
        self.limits = limits
        self.client = httpx.Client(transport=transport, timeout=30, trust_env=False)
        self.sleep = sleep
        self.clock = clock
        self.requests = 0
        self.last_start: float | None = None
        self.lock = threading.RLock()
        self.closed = False

    def close(self) -> None:
        """Close connections and prevent further requests."""
        self.closed = True
        self.client.close()

    def _pace(self) -> None:
        """Wait for the next request slot and charge one attempt.

        Raises:
            PublicDataError: This instance is closed or has used its budget.
        """
        if self.closed:
            raise PublicDataError("Adapter is closed")
        if (
            self.limits.max_requests is not None
            and self.requests >= self.limits.max_requests
        ):
            raise LimitError("HTTP request budget exhausted")
        if self.last_start is not None:
            delay = self.last_start + self.limits.min_interval - self.clock()
            if delay > 0:
                self.sleep(delay)
        self.last_start = self.clock()
        self.requests += 1

    def _retry_delay(self, value: str | None, attempt: int) -> float:
        """Resolve the source wait header within the configured limit.

        Args:
            value: Retry-After seconds or an HTTP date, if present.
            attempt: Zero-based attempt index for the fallback wait.

        Returns:
            A nonnegative wait in seconds.

        Raises:
            RateLimitError: The header is invalid or exceeds the wait budget.
        """
        delay = min(2**attempt, self.limits.max_retry_wait)
        if value:
            try:
                delay = float(value)
            except ValueError:
                try:
                    stamp = parsedate_to_datetime(value)
                    delay = (
                        stamp - datetime.datetime.now(datetime.UTC)
                    ).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    raise RateLimitError("Unsupported Retry-After value") from None
        if not math.isfinite(delay) or delay > self.limits.max_retry_wait:
            raise RateLimitError("Retry-After exceeds the wait budget")
        return max(0.0, delay)

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        data: dict | None = None,
        authentication: bool = False,
    ) -> Payload:
        """Fetch within limits without retaining sensitive HTTP error objects.

        Args:
            method: GET for public data or POST for ID-token acquisition.
            url: Fixed adapter source URL; never a caller-provided redirect.
            params: Public query parameters only.
            headers: Authentication headers, when needed.
            data: Form-encoded auth fields; never placed in a URL or receipt.
            authentication: Whether to suppress auth payload provenance.

        Returns:
            Bounded response bytes and a credential-free receipt.

        Raises:
            PublicDataError: Status, transport, schema, or budget failure.
        """
        with self.lock:
            for attempt in range(self.limits.attempts):
                self._pace()
                failure = None
                retry_after = None
                status = 0
                try:
                    with self.client.stream(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        data=data,
                        follow_redirects=False,
                    ) as response:
                        status = response.status_code
                        if status == 200:
                            raw = bytearray()
                            for chunk in response.iter_bytes(chunk_size=65_536):
                                raw.extend(chunk)
                                if len(raw) > self.limits.max_bytes:
                                    raise LimitError("Response byte budget exceeded")
                            body = bytes(raw)
                            receipt = Receipt(
                                url if authentication else str(response.url),
                                datetime.datetime.now(datetime.UTC),
                                ""
                                if authentication
                                else hashlib.sha256(body).hexdigest(),
                                0 if authentication else len(body),
                            )
                            return Payload(body, receipt)
                        retry_after = response.headers.get("retry-after")
                except httpx.HTTPError:
                    # Raise outside the except block to discard the HTTPX context.
                    failure = "transport"
                if status == 401 or (
                    authentication
                    and failure is None
                    and status not in (0, 429, 502, 503, 504)
                ):
                    raise AuthenticationError("Public API authentication failed")
                if status == 403:
                    raise AccessDeniedError("Source denied public access")
                retryable = failure is not None or status in (429, 502, 503, 504)
                if not retryable:
                    raise SourceUnavailableError(f"Source returned HTTP {status}")
                if attempt + 1 == self.limits.attempts:
                    if status == 429:
                        raise RateLimitError("Rate-limit attempt budget exhausted")
                    raise SourceUnavailableError("HTTP attempt budget exhausted")
                self.sleep(self._retry_delay(retry_after, attempt))
        raise AssertionError("Unreachable request state")
