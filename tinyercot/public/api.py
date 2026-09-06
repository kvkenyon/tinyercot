"""Opt-in DAM price retrieval with explicit credentials and bounded pagination."""

import datetime
import math
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Generic, Self, TypeVar

import httpx
from pydantic import ValidationError

from ._generated import CAPACITY_FIELDS, DAM_FIELDS, DamCapacityPrice, DamPrice
from ._http import (
    _HTTP,
    AuthenticationError,
    Limits,
    Payload,
    Receipt,
    SchemaMismatchError,
    StreamingLimits,
)

BASE = "https://api.ercot.com/api/public-reports"
PRICE_PATH = "/np4-190-cd/dam_stlmnt_pnt_prices"
CAPACITY_PATH = "/np4-188-cd/dam_clear_price_for_cap"
Row = TypeVar("Row", DamPrice, DamCapacityPrice)
TOKEN_URL = "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"


@dataclass(frozen=True)
class Credentials:
    """Public API account credentials, excluded from repr output.

    Attributes:
        username: ERCOT Public API account name.
        password: ERCOT Public API account password.
        subscription_key: Subscription key for the public data product.
    """

    username: str = field(repr=False)
    password: str = field(repr=False)
    subscription_key: str = field(repr=False)

    def __post_init__(self) -> None:
        if not all((self.username, self.password, self.subscription_key)):
            raise AuthenticationError("All three Public API credentials are required")

    @classmethod
    def from_env(cls) -> Self:
        """Read the three legacy ERCOT environment names on explicit request.

        Returns:
            Credentials without loading dotenv files or authenticating.

        Raises:
            AuthenticationError: A required environment value is absent.
        """
        return cls(
            *(
                os.environ.get(name, "")
                for name in (
                    "ERCOT_USERNAME",
                    "ERCOT_PASSWORD",
                    "ERCOT_SUBSCRIPTION_KEY",
                )
            )
        )


@dataclass(frozen=True)
class PricePage(Generic[Row]):
    """Decoded price rows with the original public envelope and receipt.

    Attributes:
        rows: Source rows decoded using declared field names and order.
        meta: Original pagination and query metadata.
        raw: Complete public response bytes; no request credentials or headers.
        receipt: Retrieval time and exact response hash.
    """

    rows: tuple[Row, ...]
    meta: dict
    raw: bytes = field(repr=False)
    receipt: Receipt


def _decode_page(
    payload: Payload,
    *,
    expected_page: int,
    fields: dict,
    row_model: type[Row],
    price_field: str,
) -> PricePage[Row]:
    """Decode the observed five-column schema using response-declared order.

    Args:
        payload: Bounded public JSON bytes and receipt.
        expected_page: Requested one-based page number.
        fields: Pinned response field names and source types.
        row_model: Generated model for this fixed endpoint.
        price_field: Numeric price field in the pinned model.

    Returns:
        Typed non-null rows plus the complete original envelope.

    Raises:
        SchemaMismatchError: Fields, row widths/types, or pagination disagree.
    """
    body = payload.json()
    try:
        declared = body["fields"]
        if not isinstance(declared, list):
            raise TypeError
        names = [entry["name"] for entry in declared]
        if (
            len(names) != len(set(names))
            or {e["name"]: e["dataType"] for e in declared} != fields
        ):
            raise ValueError
        meta = body["_meta"]
        if type(meta["currentPage"]) is not int or meta["currentPage"] != expected_page:
            raise ValueError
        if type(meta["totalPages"]) is not int or meta["totalPages"] < 0:
            raise ValueError
        if meta["totalPages"] and expected_page > meta["totalPages"]:
            raise ValueError
        data = body["data"]
        if not isinstance(data, list):
            raise TypeError
        rows = []
        for row in data:
            if isinstance(row, list):
                if len(row) != len(names):
                    raise ValueError
                row = dict(zip(names, row, strict=True))
            if not isinstance(row, dict) or set(row) != set(fields):
                raise ValueError
            if type(row["deliveryDate"]) is not str or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", row["deliveryDate"]
            ):
                raise ValueError
            if type(row[price_field]) not in (Decimal, int):
                raise ValueError
            model = row_model.model_validate(row)
            if not getattr(model, price_field).is_finite():
                raise ValueError
            rows.append(model)
        if not meta["totalPages"] and rows:
            raise ValueError
        return PricePage(tuple(rows), meta, payload.body, payload.receipt)
    except (KeyError, TypeError, ValueError, ValidationError):
        pass
    raise SchemaMismatchError(
        "DAM price response differs from the observed field/page contract"
    )


def decode_prices(payload: Payload, *, expected_page: int) -> PricePage[DamPrice]:
    """Decode observed DAM settlement prices.

    Args:
        payload: Bounded public JSON bytes and receipt.
        expected_page: Requested one-based page number.

    Returns:
        Typed non-null rows and the original public envelope.

    Raises:
        SchemaMismatchError: Fields, rows, or pagination differ from the contract.
    """
    return _decode_page(
        payload,
        expected_page=expected_page,
        fields=DAM_FIELDS,
        row_model=DamPrice,
        price_field="settlementPointPrice",
    )


class PublicClient:
    """A synchronous client restricted to two observed public DAM price sources.

    Use as a context manager. Credentials and tokens stay on this instance.
    This client has no participant routes, generic raw URL method, or async API.
    """

    def __init__(
        self,
        credentials: Credentials,
        *,
        limits: Limits | StreamingLimits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create a client without making an HTTP request.

        Args:
            credentials: Explicit public-account credentials.
            limits: Per-instance request, byte, pacing, and retry ceilings.
            transport: Optional HTTPX transport for offline tests.
        """
        self._credentials = credentials
        self._http = _HTTP(limits or Limits(), transport)
        self._token: str | None = None
        self._expires_at = 0.0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the transport and discard this instance's cached token."""
        self._token = None
        self._http.close()

    def refresh_token(self) -> None:
        """Acquire a new ID token; ERCOT does not support ID-token refresh.

        Form-encoded acquisition was verified against the public auth service.
        Secret values stay out of request URLs, receipts, and exceptions.

        Raises:
            AuthenticationError: The auth response has no usable token lifetime.
            PublicDataError: Transport, access, or request limits fail.
        """
        with self._http.lock:
            self._token = None
            started = self._http.clock()
            response = self._http.request(
                "POST",
                TOKEN_URL,
                authentication=True,
                data={
                    "username": self._credentials.username,
                    "password": self._credentials.password,
                    "grant_type": "password",
                    "scope": f"openid {CLIENT_ID} offline_access",
                    "client_id": CLIENT_ID,
                    "response_type": "id_token",
                },
            ).json()
            try:
                token = response["id_token"]
                lifetime = float(response["expires_in"])
                if (
                    not isinstance(token, str)
                    or not token
                    or not math.isfinite(lifetime)
                    or lifetime <= 60
                ):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise AuthenticationError("Invalid public ID-token response") from None
            self._token = token
            self._expires_at = started + min(lifetime, 3600) - 60

    def dam_prices(
        self,
        *,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        settlement_point: str,
        page: int = 1,
        size: int = 100,
        oldest_first: bool = False,
    ) -> PricePage[DamPrice]:
        """Fetch one bounded page from the observed DAM price endpoint.

        Args:
            start: Inclusive source delivery-date lower filter.
            end: Inclusive source delivery-date upper filter.
            settlement_point: Exact public settlement point identifier.
            page: One-based page number, not an automatic history traversal.
            size: Client-selected page ceiling, from 1 through 1000.
            oldest_first: Sort by delivery date ascending instead of descending.
                With omitted dates, size=1 gives an oldest-available observation.

        Returns:
            Typed price rows with raw public envelope and retrieval receipt.

        Raises:
            ValueError: Local query bounds are invalid.
            PublicDataError: Authentication, transport, or schema checks fail.
        """
        if not settlement_point or len(settlement_point) > 128:
            raise ValueError("A settlement point is required")
        if (
            type(page) is not int
            or page < 1
            or type(size) is not int
            or not 1 <= size <= 1000
        ):
            raise ValueError("Invalid page or client page-size ceiling")
        if start and end and start > end:
            raise ValueError("start must not follow end")
        params = {
            "settlementPoint": settlement_point,
            "page": page,
            "size": size,
            "sort": "deliveryDate",
            "dir": "asc" if oldest_first else "desc",
        }
        if start:
            params["deliveryDateFrom"] = start.isoformat()
        if end:
            params["deliveryDateTo"] = end.isoformat()
        payload = self._price_payload(PRICE_PATH, params)
        result = decode_prices(payload, expected_page=page)
        if len(result.rows) > size:
            raise SchemaMismatchError("Source exceeded requested page size")
        return result

    def dam_capacity_prices(
        self,
        *,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        ancillary_type: str,
        page: int = 1,
        size: int = 100,
        oldest_first: bool = False,
    ) -> PricePage[DamCapacityPrice]:
        """Fetch one bounded NP4-188-CD capacity-price page.

        Args:
            start: Inclusive source delivery-date lower filter.
            end: Inclusive source delivery-date upper filter.
            ancillary_type: Exact public ancillary-service identifier.
            page: One-based page number.
            size: Client-selected row ceiling, from 1 through 1000.
            oldest_first: Sort delivery date ascending for oldest observations.

        Returns:
            Typed non-null rows and the original public envelope and receipt.

        Raises:
            ValueError: Local query bounds are invalid.
            PublicDataError: Authentication, transport, or schema checks fail.
        """
        if not ancillary_type or len(ancillary_type) > 128:
            raise ValueError("An ancillary-service identifier is required")
        if (
            type(page) is not int
            or page < 1
            or type(size) is not int
            or not 1 <= size <= 1000
        ):
            raise ValueError("Invalid page or client page-size ceiling")
        if start and end and start > end:
            raise ValueError("start must not follow end")
        params = {
            "ancillaryType": ancillary_type,
            "page": page,
            "size": size,
            "sort": "deliveryDate",
            "dir": "asc" if oldest_first else "desc",
        }
        if start:
            params["deliveryDateFrom"] = start.isoformat()
        if end:
            params["deliveryDateTo"] = end.isoformat()
        result = _decode_page(
            self._price_payload(CAPACITY_PATH, params),
            expected_page=page,
            fields=CAPACITY_FIELDS,
            row_model=DamCapacityPrice,
            price_field="MCPC",
        )
        if len(result.rows) > size:
            raise SchemaMismatchError("Source exceeded requested page size")
        return result

    def _price_payload(self, path: str, params: dict) -> Payload:
        """Use the instance token for one fixed public price route.

        Args:
            path: One of the two implemented public price paths.
            params: Validated public query fields.

        Returns:
            Bounded public JSON bytes and receipt.

        Raises:
            PublicDataError: Route, authentication, or transport checks fail.
        """
        if path not in (PRICE_PATH, CAPACITY_PATH):
            raise ValueError("Unsupported price path")
        return self._authenticated_payload(path, params)

    def _authenticated_payload(self, path: str, params: dict) -> Payload:
        """Fetch a route already checked by an opt-in public adapter.

        Args:
            path: Adapter-verified relative public report path.
            params: Validated public query parameters.

        Returns:
            Public bytes after bounded token acquisition and transport retries.

        Raises:
            PublicDataError: Authentication, transport, or budgets fail.
        """
        with self._http.lock:
            for reacquisition in range(2):
                if self._token is None or self._http.clock() >= self._expires_at:
                    self.refresh_token()
                try:
                    return self._http.request(
                        "GET",
                        BASE + path,
                        params=params,
                        headers={
                            "Authorization": f"Bearer {self._token}",
                            "Ocp-Apim-Subscription-Key": self._credentials.subscription_key,
                        },
                    )
                except AuthenticationError:
                    self._token = None
                    if reacquisition:
                        raise AuthenticationError(
                            "Public API rejected the new ID token"
                        ) from None
        raise AuthenticationError("Public API token reacquisition failed")

    def price_pages(
        self,
        *,
        start: datetime.date,
        end: datetime.date,
        settlement_point: str,
        size: int = 100,
        max_pages: int = 2,
    ) -> Iterator[PricePage[DamPrice]]:
        """Yield a bounded selection of pages, preserving each page receipt.

        Args:
            start: Required delivery-date lower filter.
            end: Required delivery-date upper filter, at most 31 days after start.
            settlement_point: Exact public settlement point identifier.
            size: Rows requested per page, subject to the client ceiling.
            max_pages: Explicit sampling limit, from 1 through 10.

        Yields:
            Pages starting at one. Reaching max_pages is a partial selection,
            not a complete-history result; totalPages remains in page metadata.

        Raises:
            ValueError: The caller's window or page bound is invalid.
            PublicDataError: A request or page consistency check fails.
        """
        if (
            type(max_pages) is not int
            or not 1 <= max_pages <= 10
            or not 0 <= (end - start).days <= 31
        ):
            raise ValueError("Pagination requires a window <=31 days and <=10 pages")
        seen = set()
        for page in range(1, max_pages + 1):
            result = self.dam_prices(
                start=start,
                end=end,
                settlement_point=settlement_point,
                page=page,
                size=size,
                oldest_first=True,
            )
            identity = tuple(row.model_dump_json() for row in result.rows)
            if identity and identity in seen:
                raise SchemaMismatchError("Source repeated a page of rows")
            seen.add(identity)
            yield result
            if page >= result.meta["totalPages"]:
                break
