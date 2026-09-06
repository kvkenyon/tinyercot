"""Typed identities for verified public contracts; no network access on import."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from .reports import DataPage, ReportsClient

RowT = TypeVar("RowT", bound=BaseModel)
FiltersT = TypeVar("FiltersT", bound=Mapping[str, object])


@dataclass(frozen=True)
class Endpoint(Generic[RowT, FiltersT]):
    """A generated public data operation and its pinned query/row evidence.

    Attributes:
        path: Verified Public Reports data path.
        row_model: Generated model for observed non-null rows.
        contract_name: Bundled compact source projection key.
    """

    path: str
    row_model: type[RowT]
    contract_name: str

    @property
    def contract(self) -> dict[str, Any]:
        """Return a fresh copy of the bundled source-backed contract.

        Returns:
            Query descriptors, row fields, and public source receipts.
        """
        bundle = json.loads(
            files("tinyercot.public").joinpath("_contracts.json").read_text()
        )
        return dict(bundle[self.contract_name])

    def page(
        self,
        client: ReportsClient,
        *,
        filters: FiltersT | None = None,
        page: int = 1,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
    ) -> DataPage[RowT]:
        """Fetch one page with filter types bound to this endpoint identity.

        Args:
            client: Explicit authenticated public client.
            filters: This endpoint's generated optional filter dictionary.
            page: One-based page number.
            size: Maximum source rows in the response.
            sort: A source-declared sortable field, or source default order.
            direction: Source sort direction.

        Returns:
            Typed rows, source metadata, raw public bytes, and a receipt.

        Raises:
            ValueError: Filters or query controls are invalid.
            PublicDataError: Retrieval, budget, or source checks fail.
        """
        return client.page(
            self, filters=filters, page=page, size=size, sort=sort, direction=direction
        )

    def pages(
        self,
        client: ReportsClient,
        *,
        filters: FiltersT | None = None,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
        max_pages: int | None = 100,
    ) -> Iterator[DataPage[RowT]]:
        """Stream complete filtered pages or raise at the caller's budget.

        Args:
            client: Explicit authenticated public client.
            filters: This endpoint's generated optional filter dictionary.
            size: Maximum source rows per response.
            sort: A source-declared sortable field, or source default order.
            direction: Source sort direction.
            max_pages: Page budget, or None to permit all available pages.

        Returns:
            An iterator of typed pages with separate receipts.

        Raises:
            PublicDataError: Iteration encounters a source or budget failure.
        """
        return client.pages(
            self,
            filters=filters,
            size=size,
            sort=sort,
            direction=direction,
            max_pages=max_pages,
        )

    def iter_rows(
        self,
        client: ReportsClient,
        *,
        filters: FiltersT | None = None,
        size: int = 1000,
        sort: str | None = None,
        direction: Literal["asc", "desc"] = "asc",
        max_pages: int | None = 100,
        max_rows: int | None = 100_000,
    ) -> Iterator[RowT]:
        """Stream typed rows with endpoint-specific filter checking.

        Args:
            client: Explicit authenticated public client.
            filters: This endpoint's generated optional filter dictionary.
            size: Maximum rows retained per response.
            sort: A source-declared sortable field, or source default order.
            direction: Source sort direction.
            max_pages: Page budget, or None for a complete query.
            max_rows: Row budget, or None for a complete query.

        Returns:
            A typed row iterator. Budgets raise instead of hiding truncation.

        Raises:
            PublicDataError: Iteration encounters a source or budget failure.
        """
        return client.iter_rows(
            self,
            filters=filters,
            size=size,
            sort=sort,
            direction=direction,
            max_pages=max_pages,
            max_rows=max_rows,
        )
