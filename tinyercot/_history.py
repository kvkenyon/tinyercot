"""Typed rows from ERCOT's historical CSV files and nested ZIP downloads."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterator, Sequence
from datetime import date, datetime
from fnmatch import fnmatchcase
from io import BytesIO, TextIOWrapper
from time import strptime
from typing import TYPE_CHECKING, Generic, Literal, TypeVar
from zipfile import ZipFile

from pydantic import BaseModel

if TYPE_CHECKING:
    from ._client import Transport

T = TypeVar("T", bound=BaseModel)


def _csv_files(data: bytes, pattern: str = "*.csv") -> Iterator[tuple[str, bytes]]:
    with ZipFile(BytesIO(data)) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            if member.filename.lower().endswith(".zip"):
                yield from _csv_files(archive.read(member), pattern)
            elif member.filename.lower().endswith(".csv") and fnmatchcase(
                member.filename.rsplit("/", 1)[-1], pattern
            ):
                yield member.filename, archive.read(member)


class Archive(Generic[T]):
    """Historical files decoded into the same row type as a report's API.

    Publication bounds select documents, not delivery dates. A typed predicate
    can further select rows. Files are processed one document at a time.
    """

    def __init__(
        self,
        client: Transport,
        product: str,
        row: type[T],
        columns: dict[str, str],
        dates: dict[str, str],
        *,
        member: str = "*.csv",
        datetimes: dict[str, str] | None = None,
        variants: tuple[dict[str, str], ...] = (),
    ) -> None:
        self._client = client
        self._product = product
        self._row = row
        self._layouts = (columns, *variants)
        self._member = member
        self._dates = dates
        self._datetimes = datetimes or {}

    def read(self, data: bytes) -> Iterator[T]:
        """Read CSV members in a downloaded ZIP, including nested ZIPs.

        A mismatched schema raises instead of silently dropping historical data.
        """
        found = False
        for filename, content in _csv_files(data, self._member):
            found = True
            reader = csv.DictReader(
                TextIOWrapper(BytesIO(content), encoding="utf-8-sig", newline="")
            )
            fields = reader.fieldnames or []
            columns = next(
                (layout for layout in self._layouts if set(fields) == set(layout)), None
            )
            if columns is None:
                raise ValueError(f"{filename}: unexpected CSV columns {fields!r}")
            for line, values in enumerate(reader, 2):
                try:
                    converted: dict[str, object] = {}
                    for source, target in columns.items():
                        value = values[source]
                        if value is None or None in values:
                            raise ValueError("CSV row has the wrong number of cells")
                        value = value.strip()
                        converted[target] = (
                            date(*strptime(value, self._dates[target])[:3])
                            if value and target in self._dates
                            else value or None
                        )
                    for target, format in self._datetimes.items():
                        value = converted.get(target)
                        if isinstance(value, str):
                            # Preserve the local timestamp and separate repeated-hour flag.
                            converted[target] = datetime.strptime(value, format)  # noqa: DTZ007
                    yield self._row.model_validate(converted)
                except ValueError as error:
                    raise ValueError(f"{filename}:{line}: {error}") from error
        if not found:
            raise ValueError(
                f"Download contains no CSV files matching {self._member!r}"
            )

    def download(
        self,
        doc_ids: Sequence[int],
        *,
        kind: Literal["archive", "bundle"] = "archive",
    ) -> Iterator[T]:
        """Download selected documents or bundles and yield typed rows."""
        for doc_id in doc_ids:
            yield from self.read(
                self._client.download(self._product, [doc_id], kind=kind)
            )

    def rows(
        self,
        *,
        posted_from: datetime | None = None,
        posted_to: datetime | None = None,
        where: Callable[[T], bool] | None = None,
    ) -> Iterator[T]:
        """Read every matching archive document, without a history cutoff.

        Bounds are inclusive ERCOT publication timestamps. No ordering or
        deduplication of rows is imposed; corrected publications are preserved.
        """
        if (
            posted_from is not None
            and posted_to is not None
            and posted_from > posted_to
        ):
            raise ValueError("posted_from must not be after posted_to")
        for document in self._client.iter_documents(
            self._product, posted_from=posted_from, posted_to=posted_to
        ):
            for row in self.download([document.docId]):
                if where is None or where(row):
                    yield row
