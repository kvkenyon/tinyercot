"""Retain bounded public HTTP receipts, including failed transfers."""

import datetime
import hashlib
from dataclasses import dataclass

import httpx

from ._http import (
    _HTTP,
    AccessDeniedError,
    AuthenticationError,
    LimitError,
    Payload,
    RateLimitError,
    Receipt,
    SchemaMismatchError,
    SourceUnavailableError,
)


@dataclass(frozen=True)
class Exchange:
    """Identify one public HTTP attempt without headers or response text.

    Attributes:
        receipt: Hash and byte count of the retained decoded prefix.
        method: HTTP verb.
        content_type: Response media type without parameters.
        complete: Whether the hash covers the complete response.
        document_ids: Explicit public POST selection, if present.
    """

    receipt: Receipt
    method: str
    content_type: str
    complete: bool
    document_ids: tuple[int, ...] = ()


class EvidenceHTTP(_HTTP):
    """Check public media types and retain receipts for each bounded attempt."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exchanges: list[Exchange] = []

    def request(
        self,
        method,
        url,
        *,
        params=None,
        headers=None,
        data=None,
        json_body=None,
        authentication=False,
    ) -> Payload:
        """Fetch public bytes with receipts or use the existing secret auth flow.

        Args:
            method: Public GET or archive POST verb.
            url: Fixed public adapter URL.
            params: Public query filters.
            headers: Authentication headers; never retained.
            data: Authentication form; never retained.
            json_body: Public document selection.
            authentication: Use the existing auth path without receipts.

        Returns:
            Complete bounded bytes after status and media type checks.

        Raises:
            PublicDataError: Transport, status, media type, or limits fail.
        """
        if authentication:
            return super().request(
                method,
                url,
                params=params,
                headers=headers,
                data=data,
                json_body=json_body,
                authentication=True,
            )
        expected = "application/zip" if method == "POST" else "application/json"
        with self.lock:
            for attempt in range(self.limits.attempts):
                self._pace()
                raw = bytearray()
                status = 0
                media = ""
                complete = False
                oversized = False
                retry_after = None
                source = str(httpx.URL(url, params=params))
                try:
                    with self.client.stream(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        json=json_body,
                        follow_redirects=False,
                    ) as response:
                        status = response.status_code
                        media = (
                            response.headers.get("content-type", "")
                            .split(";", 1)[0]
                            .strip()
                            .lower()
                        )
                        retry_after = response.headers.get("retry-after")
                        for chunk in response.iter_bytes(chunk_size=65536):
                            remaining = self.limits.max_bytes - len(raw)
                            raw.extend(chunk[:remaining])
                            if len(chunk) > remaining:
                                oversized = True
                                break
                        complete = not oversized
                except httpx.HTTPError:
                    pass
                receipt = Receipt(
                    source,
                    datetime.datetime.now(datetime.UTC),
                    hashlib.sha256(raw).hexdigest(),
                    len(raw),
                    status,
                )
                self.exchanges.append(
                    Exchange(
                        receipt,
                        method,
                        media,
                        complete,
                        tuple((json_body or {}).get("docIds", ())),
                    )
                )
                if oversized:
                    raise LimitError("Public response byte budget exceeded")
                if status == 401:
                    raise AuthenticationError("Public API authentication failed")
                if status == 403:
                    raise AccessDeniedError("Source denied public access")
                if status == 200 and complete:
                    if media != expected:
                        raise SchemaMismatchError(
                            "Public response content type differs"
                        )
                    return Payload(bytes(raw), receipt)
                retryable = not complete or status in (429, 502, 503, 504)
                if not retryable or attempt + 1 == self.limits.attempts:
                    if status == 429:
                        raise RateLimitError(
                            "Public rate-limit attempt budget exhausted"
                        )
                    raise SourceUnavailableError(
                        f"Public transfer failed (HTTP {status})"
                    )
                self.sleep(self._retry_delay(retry_after, attempt))
        raise AssertionError("Unreachable request state")
