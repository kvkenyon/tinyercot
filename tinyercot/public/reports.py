"""Shared typed current-report retrieval with complete, opt-in iteration."""

import datetime
import hashlib
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Generic, Literal

import httpx

from ._http import LimitError, Payload, Receipt, SchemaMismatchError, StreamingLimits
from ._schemas import ENDPOINTS
from .api import Credentials, PublicClient
from .schema import Endpoint, FiltersT, RowT


@dataclass(frozen=True)
class DataPage(Generic[RowT]):
    """A typed report page with unchanged source metadata and public bytes.

    Attributes:
        rows: Decoded source rows in source order.
        meta: Source pagination metadata; no completeness is inferred.
        receipt: Exact public response hash and retrieval time.
        raw: Original public envelope without request headers or credentials.
    """

    rows: tuple[RowT, ...]
    meta: dict[str, Any]
    receipt: Receipt
    raw: bytes = field(repr=False)


def query_parameters(
    endpoint: Endpoint[RowT, FiltersT], filters: Mapping[str, object]
) -> dict[str, str]:
    """Validate every filter against the pinned authoritative query metadata.

    Args:
        endpoint: Registered current operation.
        filters: Source filter names and Python values, excluding page controls.

    Returns:
        Public URL values with dates, booleans, and decimals encoded explicitly.

    Raises:
        ValueError: A filter name, type, or paired range is invalid.
    """
    definitions = {
        p["name"]: p["schema"]
        for p in endpoint.contract["query_parameters"]
        if p["name"] not in {"page", "size", "sort", "dir"}
    }
    result = {}
    for name, value in filters.items():
        if name not in definitions:
            raise ValueError("Unknown current query filter")
        schema = definitions[name]
        kind = schema["type"]
        if kind == "string" and schema.get("format") == "yyyy-MM-dd":
            valid = type(value) is datetime.date
            encoded = value.isoformat() if isinstance(value, datetime.date) else ""
        elif kind == "string":
            valid = type(value) is str and len(value) <= 1024
            encoded = str(value)
        elif kind == "boolean":
            valid = type(value) is bool
            encoded = "true" if value else "false"
        elif kind == "integer":
            valid = type(value) is int
            encoded = str(value)
        elif kind == "number":
            valid = (
                isinstance(value, (int, float, Decimal))
                and not isinstance(value, bool)
                and math.isfinite(value)
            )
            encoded = str(value)
        else:
            valid, encoded = False, ""
        if not valid:
            raise ValueError("Current query filter has an invalid type or value")
        result[name] = encoded
    for name, value in filters.items():
        if name.endswith("From") and name[:-4] + "To" in filters:
            other = name[:-4] + "To"
            low, high = result[name], result[other]
            reversed_range = (
                Decimal(low) > Decimal(high)
                if definitions[name]["type"] in {"integer", "number"}
                else low > high
            )
            if reversed_range:
                raise ValueError("Current query lower bound follows upper bound")
    return result


def decode_page(
    payload: Payload, endpoint: Endpoint[RowT, FiltersT], *, page: int, size: int
) -> DataPage[RowT]:
    """Decode by declared field order, with no unknown-type fallback.

    Args:
        payload: Bounded public JSON response and receipt.
        endpoint: Generated row model and pinned field contract.
        page: Requested one-based page.
        size: Requested maximum number of rows.

    Returns:
        Non-null typed rows and complete source pagination metadata.

    Raises:
        SchemaMismatchError: Row fields, types, or pagination metadata disagree.
    """
    body = payload.json()
    expected = {f["name"]: f["dataType"] for f in endpoint.contract["fields"]}
    try:
        fields = body["fields"]
        names = [f["name"] for f in fields]
        if (
            len(set(names)) != len(names)
            or {f["name"]: f["dataType"] for f in fields} != expected
        ):
            raise ValueError
        meta = body["_meta"]
        if any(
            type(meta[k]) is not int or meta[k] < 0
            for k in ("currentPage", "totalPages", "totalRecords", "pageSize")
        ):
            raise ValueError
        raw_rows = body["data"]
        if not isinstance(raw_rows, list) or len(raw_rows) > size:
            raise ValueError
        empty = not raw_rows and meta["totalRecords"] == meta["totalPages"] == 0
        if meta["currentPage"] != page and not (
            empty and page == 1 and meta["currentPage"] == 0
        ):
            raise ValueError
        if not empty and (
            not raw_rows
            or page > meta["totalPages"]
            or meta["pageSize"] < len(raw_rows)
            or meta["totalRecords"] < len(raw_rows)
        ):
            raise ValueError
        rows = []
        for values in raw_rows:
            if isinstance(values, list) and len(values) == len(names):
                values = dict(zip(names, values, strict=True))
            if not isinstance(values, dict) or set(values) != set(expected):
                raise ValueError
            for name, kind in expected.items():
                value = values[name]
                if kind in {"DOUBLE", "FLOAT"}:
                    if (
                        type(value) not in (Decimal, int)
                        or not Decimal(value).is_finite()
                    ):
                        raise ValueError
                elif kind in {"INTEGER", "LONG"}:
                    if type(value) is not int:
                        raise ValueError
                elif kind == "BOOLEAN":
                    if type(value) is not bool:
                        raise ValueError
                elif kind in {"VARCHAR", "DATE", "DATETIME"}:
                    if type(value) is not str:
                        raise ValueError
                    if (
                        kind == "DATE"
                        and datetime.date.fromisoformat(value).isoformat() != value
                    ):
                        raise ValueError
                    if kind == "DATETIME":
                        datetime.datetime.fromisoformat(value)
                else:
                    raise ValueError
            rows.append(endpoint.row_model.model_validate(values))
        return DataPage(tuple(rows), meta, payload.receipt, payload.body)
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError(
        "Current report differs from its verified row/page contract"
    )


class ReportsClient(PublicClient):
    """A typed registry client with optional complete-query iteration.

    Only generated, registered public endpoints are accepted. Unknown schemas
    are not raw adapters. Existing PublicClient methods keep their defaults.
    """

    def __init__(
        self,
        credentials: Credentials,
        *,
        limits: StreamingLimits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create the opt-in streaming client without a network request.

        Args:
            credentials: Explicit Public API account credentials.
            limits: Request budget; max_requests=None allows a complete query.
            transport: Optional mocked transport for offline tests.
        """
        super().__init__(
            credentials, limits=limits or StreamingLimits(), transport=transport
        )

    def page(
        self,
        endpoint: Endpoint[RowT, FiltersT],
        *,
        filters: FiltersT | None = None,
        page: int = 1,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
    ) -> DataPage[RowT]:
        """Fetch one typed page using all supported current filter names.

        Args:
            endpoint: Generated endpoint constant, with a typed filter dictionary.
            filters: Optional source filters from that constant's query contract.
            page: One-based page number.
            size: Rows per response, from 1 through 1000.
            sort: One source-declared sortable field, or source default order.
            direction: Ascending or descending source sort direction.

        Returns:
            Typed rows and source metadata with an exact public receipt.

        Raises:
            ValueError: Local filters or page controls are invalid.
            PublicDataError: Transport, access, budget, or schema checks fail.
        """
        if not any(endpoint is registered for registered in ENDPOINTS):
            raise ValueError("Endpoint has no registered verified public schema")
        if (
            type(page) is not int
            or page < 1
            or type(size) is not int
            or not 1 <= size <= 1000
            or direction not in {"asc", "desc"}
        ):
            raise ValueError("Invalid current page controls")
        parameters: dict[str, str | int] = dict(
            query_parameters(endpoint, filters or {})
        )
        parameters.update({"page": page, "size": size, "dir": direction})
        if sort is not None:
            if sort not in {
                f["name"]
                for f in endpoint.contract["fields"]
                if f.get("sortable") is True
            }:
                raise ValueError("Unknown or unsupported sort field")
            parameters["sort"] = sort
        return decode_page(
            self._authenticated_payload(endpoint.path, parameters),
            endpoint,
            page=page,
            size=size,
        )

    def pages(
        self,
        endpoint: Endpoint[RowT, FiltersT],
        *,
        filters: FiltersT | None = None,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
        max_pages: int | None = 100,
    ) -> Iterator[DataPage[RowT]]:
        """Stream a complete filtered query or raise at an explicit budget.

        Args:
            endpoint: Generated current endpoint constant.
            filters: Source filters, without a fixed date-window restriction.
            size: Maximum rows per response.
            sort: Source-declared sortable field, or source default order.
            direction: Source sort direction.
            max_pages: Positive page budget, or None for all available pages.

        Yields:
            Pages with individual receipts. Budget exhaustion raises instead of
            silently presenting a partial result as complete.

        Raises:
            ValueError: A local bound or query control is invalid.
            PublicDataError: Transport, schema, changing totals, or budgets fail.
        """
        if max_pages is not None and (type(max_pages) is not int or max_pages < 1):
            raise ValueError("max_pages must be positive or None")
        number = 1
        previous = None
        totals = None
        received = 0
        while True:
            if max_pages is not None and number > max_pages:
                raise LimitError("Page budget reached before the query completed")
            result = self.page(
                endpoint,
                filters=filters,
                page=number,
                size=size,
                sort=sort,
                direction=direction,
            )
            current_totals = (result.meta["totalPages"], result.meta["totalRecords"])
            if totals is not None and totals != current_totals:
                raise SchemaMismatchError("Source totals changed during pagination")
            totals = current_totals
            digest = hashlib.sha256(
                "\n".join(row.model_dump_json() for row in result.rows).encode()
            ).hexdigest()
            if result.rows and digest == previous:
                raise SchemaMismatchError("Source repeated the preceding page")
            previous = digest
            received += len(result.rows)
            if received > result.meta["totalRecords"] or (
                number >= result.meta["totalPages"]
                and received != result.meta["totalRecords"]
            ):
                raise SchemaMismatchError("Page rows disagree with source totalRecords")
            yield result
            if number >= result.meta["totalPages"]:
                return
            number += 1

    def iter_rows(
        self,
        endpoint: Endpoint[RowT, FiltersT],
        *,
        filters: FiltersT | None = None,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
        max_pages: int | None = 100,
        max_rows: int | None = 100_000,
    ) -> Iterator[RowT]:
        """Stream typed rows with memory bounded by one response page.

        Args:
            endpoint: Generated current endpoint constant.
            filters: Source filters for the desired complete selection.
            size: Maximum rows retained per response page.
            sort: Source-declared sortable field, or source default order.
            direction: Source sort direction.
            max_pages: Page budget, or None to remove this caller safeguard.
            max_rows: Row budget, or None to remove this caller safeguard.

        Yields:
            Source rows. Exhaustion means the reported query completed; budgets
            raise explicitly. This is not a stable as-of snapshot guarantee.

        Raises:
            ValueError: A local bound is invalid.
            PublicDataError: Retrieval, source consistency, or a budget fails.
        """
        if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
            raise ValueError("max_rows must be positive or None")
        count = 0
        for response in self.pages(
            endpoint,
            filters=filters,
            size=size,
            sort=sort,
            direction=direction,
            max_pages=max_pages,
        ):
            for row in response.rows:
                if max_rows is not None and count >= max_rows:
                    raise LimitError("Row budget reached before the query completed")
                count += 1
                yield row
