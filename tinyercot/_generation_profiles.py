"""Hourly modeled wind and solar generation published for planning studies."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from io import BytesIO, TextIOWrapper
from itertools import islice
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets
from ._public_tables import PublicFile, _PublicTable, _year_files


class GenerationProfileSite(BaseModel):
    """A profile column and its published metadata, without inferred site joins."""

    model_config = ConfigDict(extra="forbid")
    column: str
    siteId: str
    capacityMW: Decimal | None = None
    commonName: str | None = None
    county: str | None = None
    cdrZone: str | None = None
    newFor: str | None = None
    newForLabel: str | None = None
    plantStatus: str | None = None
    sourceMember: str
    sourceSheet: str


class GenerationProfileHour(BaseModel):
    """Modeled MW by source column, not metered generation or a historical fleet.

    The source's DATE and HHMM clock are retained without assigning a timezone
    or guessing whether the hour begins or ends then. Repeated clocks survive.
    Site identifiers vary by publication; use sites() on the same file for its
    metadata. These retrospective profiles are not point-in-time forecasts.
    """

    model_config = ConfigDict(extra="forbid")
    profileDate: date
    timeHHMM: int
    sourceTime: str
    sourceTimeColumn: str
    sourceYear: int | None = None
    generationMW: dict[str, Decimal | None]
    sourceMember: str
    sourceSheet: str


def _tables(
    data: bytes, filename: str
) -> Iterator[tuple[str, str, Iterator[tuple[object, ...]]]]:
    if data.startswith(b"PK"):
        with ZipFile(BytesIO(data)) as archive:
            if "[Content_Types].xml" in archive.namelist():
                for sheet, rows in _sheets(data, date_columns=()):
                    yield filename, sheet, rows
            else:
                for name in archive.namelist():
                    if name.lower().endswith((".csv", ".xlsx", ".zip")):
                        yield from _tables(archive.read(name), f"{filename}/{name}")
    else:
        with TextIOWrapper(BytesIO(data), encoding="utf-8-sig", newline="") as stream:
            yield filename, "", (tuple(row) for row in csv.reader(stream))


def _header(
    rows: Iterator[tuple[object, ...]], member: str, sheet: str
) -> tuple[int, str, list[GenerationProfileSite]]:
    metadata: list[tuple[object, ...]] = []
    for row in islice(rows, 32):
        clock_column = next(
            (label for label in ("TIME", "TIME_CST") if label in row), None
        )
        if "DATE" in row and clock_column:
            start = row.index(clock_column) + 1
            if row.index("DATE") != start - 2 or start not in (2, 3):
                raise ValueError(f"{member}: unexpected profile date/time columns")
            columns = [str(cell) for cell in row[start:]]
            if not columns or len(set(columns)) != len(columns):
                raise ValueError(f"{member}: missing or duplicate profile columns")
            sites = []
            for i, column in enumerate(columns, start):
                site_id, _, capacity = column.partition(":capacity=")
                site = GenerationProfileSite(
                    column=column,
                    siteId=site_id,
                    capacityMW=_number(capacity) if capacity else None,
                    sourceMember=member,
                    sourceSheet=sheet,
                )
                for cells in metadata:
                    value = cells[i] if i < len(cells) else None
                    label = str(cells[1] or "").strip() if len(cells) > 1 else ""
                    text = str(value) if value is not None else None
                    if not label and text:
                        site.siteId = text
                    elif label == "MWAC":
                        site.capacityMW = _number(value)
                    elif label == "Common Name":
                        site.commonName = text
                    elif label == "County":
                        site.county = text
                    elif label == "CDR Zone":
                        site.cdrZone = text
                    elif label.startswith("New for "):
                        site.newFor, site.newForLabel = text, label
                    elif label == "Plant Status":
                        site.plantStatus = text
                sites.append(site)
            return start, clock_column, sites
        metadata.append(row)
    raise ValueError(f"{member} {sheet}: no supported DATE/TIME profile table")


class GenerationProfiles(_PublicTable[GenerationProfileHour]):
    """Public planning profiles; CSV needs no extra dependencies, XLSX uses [files].

    Select a publication with files()/download()/read() to avoid downloading
    multiple large, overlapping vintages. Earlier ZIP layouts are not all verified.
    """

    index_url = "https://www.ercot.com/gridinfo/resource"
    title_pattern = r"(?i).*(?:wind.*(?:profiles|shapes|operational)|solar.*(?:profiles|data sets)|photovoltaic.*data sets).*"

    def files(self) -> list[PublicFile]:
        """Discover direct profile datasets across linked resource archive indexes."""
        return [
            file
            for file in _year_files(self._http, self.index_url, self.title_pattern)
            if file.url.lower().endswith((".csv", ".xlsx", ".zip"))
            and "key" not in file.title.lower()
        ]

    def sites(
        self, data: bytes, *, filename: str = "profiles"
    ) -> Iterator[GenerationProfileSite]:
        """Read embedded column metadata; separate key workbooks are not joined."""
        for member, sheet, rows in _tables(data, filename):
            _, _, sites = _header(rows, member, sheet)
            yield from sites

    def _read(self, data: bytes, filename: str) -> Iterator[GenerationProfileHour]:
        found = False
        for member, sheet, rows in _tables(data, filename):
            start, clock_column, sites = _header(rows, member, sheet)
            found = True
            columns = [site.column for site in sites]
            for row in rows:
                if not row or all(value in (None, "") for value in row):
                    continue
                if len(row) != start + len(columns):
                    raise ValueError(f"{member}: profile row width differs from header")
                clock = str(row[start - 1])
                yield GenerationProfileHour(
                    profileDate=date.fromisoformat(str(row[start - 2])),
                    timeHHMM=int(clock),
                    sourceTime=clock,
                    sourceTimeColumn=clock_column,
                    sourceYear=int(str(row[0])) if start == 3 else None,
                    generationMW={
                        column: _number(value)
                        for column, value in zip(columns, row[start:], strict=True)
                    },
                    sourceMember=member,
                    sourceSheet=sheet,
                )
        if not found:
            raise ValueError(f"{filename}: no profile CSV or workbook found")
