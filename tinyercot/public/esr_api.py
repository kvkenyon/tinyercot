"""Bounded raw access to the separate public ESR REST operation.

The primary operation example has generic fields and data, not a row schema.
This module preserves raw data and validates only the response envelope.
It does not infer rows from the separate website ESR dashboard.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from ._http import Limits, Receipt, SchemaMismatchError
from .api import Credentials, PublicClient
from .archive_http import EvidenceHTTP, Exchange

BASE = "https://api.ercot.com/api/public-data"
PATH = "/rptesr-m/4_sec_esr_charging_mw"


@dataclass(frozen=True)
class RawESRPage:
    """Preserve an untyped public ESR page and its exact source identity.

    Attributes:
        envelope: Original decoded public JSON; no typed row claim.
        receipt: Exact received byte identity.
        raw: Original bounded response bytes.
        row_schema: Unknown until actual source fields and types are verified.
    """

    envelope: dict[str, Any] = field(repr=False)
    receipt: Receipt
    raw: bytes = field(repr=False)
    row_schema: Literal["unknown"] = "unknown"


class ESRAPIClient(PublicClient):
    """Fetch only the documented ESR data route using public credentials.

    Subscription access is service-specific. A denial stops the request.
    No alternate key, service, or entitlement route is tried.
    """

    def __init__(
        self,
        credentials: Credentials,
        *,
        limits: Limits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create the separate ESR client without a request.

        Args:
            credentials: Authorized public ESR account and subscription.
            limits: Request, byte, retry, and pacing budgets.
            transport: Optional offline transport.
        """
        self._credentials = credentials
        self._http = EvidenceHTTP(limits or Limits(), transport)
        self._token = None
        self._expires_at = 0.0

    @property
    def exchanges(self) -> tuple[Exchange, ...]:
        """Return public attempt receipts without authentication payloads."""
        return tuple(self._http.exchanges)

    def current(self, *, size: int = 1) -> RawESRPage:
        """Fetch one page sorted by the documented AGC execution time.

        Args:
            size: Maximum requested raw records, from 1 through 1000.

        Returns:
            Raw source envelope with unknown row schema and exact receipt.

        Raises:
            ValueError: The page size is invalid.
            PublicDataError: Status, content type, envelope, or limits fail.
        """
        if type(size) is not int or not 1 <= size <= 1000:
            raise ValueError("size must be between 1 and 1000")
        with self._http.lock:
            if self._token is None or self._http.clock() >= self._expires_at:
                self.refresh_token()
            payload = self._http.request(
                "GET",
                BASE + PATH,
                params={"page": 1, "size": size, "sort": "AGCExecTime", "dir": "desc"},
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Ocp-Apim-Subscription-Key": self._credentials.subscription_key,
                },
            )
        body = payload.json()
        try:
            if not isinstance(body, dict):
                raise TypeError
            meta = body["_meta"]
            if any(
                type(meta[k]) is not int or meta[k] < 0
                for k in (
                    "currentPage",
                    "totalPages",
                    "pageSize",
                    "totalRecords",
                )
            ):
                raise ValueError
            if meta["currentPage"] != 1 or not 1 <= meta["pageSize"] <= size:
                raise ValueError
            if not isinstance(body["report"], dict) or not isinstance(
                body["fields"], list
            ):
                raise TypeError
            if body["report"].get("reportProductId", "").lower() != "rptesr-m":
                raise ValueError
            if not isinstance(body["data"], (dict, list)):
                raise TypeError
            if isinstance(body["data"], list) and len(body["data"]) > size:
                raise ValueError
            fields = body["fields"]
            names = [f["name"] for f in fields]
            if (
                not names
                or any(type(n) is not str or not n for n in names)
                or len(set(names)) != len(names)
            ):
                raise ValueError
            for row in body["data"] if isinstance(body["data"], list) else ():
                if not isinstance(row, list) or len(row) != len(names):
                    raise ValueError
        except (KeyError, TypeError, ValueError, AttributeError):
            raise SchemaMismatchError(
                "ESR raw envelope differs; row schema remains unknown"
            ) from None
        return RawESRPage(body, payload.receipt, payload.body)
