"""Hourly modeled wind and solar generation published for planning studies."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import BytesIO, TextIOWrapper
from itertools import islice
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict

from ._generation_keys import GenerationProfileKey, read_keys
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
    tracking: str | None = None
    sourceMember: str
    sourceSheet: str
    sourceBlock: int = 1


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
    sourceBlock: int = 1


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


@dataclass
class _Block:
    start: int
    stop: int
    clock: str
    sites: list[GenerationProfileSite]


def _headers(
    rows: Iterator[tuple[object, ...]], member: str, sheet: str
) -> list[_Block]:
    metadata: list[tuple[object, ...]] = []
    for row in islice(rows, 32):
        starts = [
            i + 2
            for i, label in enumerate(row[:-1])
            if label in ("DATE", "YYYYMMDD")
            and row[i + 1] in ("TIME", "TIME_CST", "HHMM(CST)")
        ]
        if starts:
            if starts[0] not in (2, 3):
                raise ValueError(f"{member}: unexpected profile date/time columns")
            blocks = []
            stops = [start - 2 for start in starts[1:]] + [len(row)]
            for block_number, (start, stop) in enumerate(
                zip(starts, stops, strict=True), 1
            ):
                columns = [str(cell) for cell in row[start:stop]]
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
                        sourceBlock=block_number,
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
                        elif label == "Tracking":
                            site.tracking = text
                    sites.append(site)
                blocks.append(_Block(start, stop, str(row[start - 1]), sites))
            return blocks
        metadata.append(row)
    raise ValueError(f"{member} {sheet}: no supported date/time profile table")


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

    def key_files(self) -> list[PublicFile]:
        """Discover the separately published wind/solar site-key workbooks."""
        return [
            file
            for file in _year_files(
                self._http, self.index_url, r"(?i).*profiles?.*key.*"
            )
            if file.url.lower().endswith(".xlsx")
        ]

    def read_keys(
        self, data: bytes, *, filename: str = "profile-key.xlsx"
    ) -> Iterator[GenerationProfileKey]:
        """Read saved site keys and their published summaries without joining vintages."""
        yield from read_keys(data, filename)

    def sites(
        self, data: bytes, *, filename: str = "profiles"
    ) -> Iterator[GenerationProfileSite]:
        """Read embedded column metadata; separate key workbooks are not joined."""
        for member, sheet, rows in _tables(data, filename):
            for block in _headers(rows, member, sheet):
                yield from block.sites

    def _read(self, data: bytes, filename: str) -> Iterator[GenerationProfileHour]:
        found = False
        for member, sheet, rows in _tables(data, filename):
            blocks = _headers(rows, member, sheet)
            found = True
            for row in rows:
                if not row or all(value in (None, "") for value in row):
                    continue
                if len(row) > blocks[-1].stop:
                    raise ValueError(f"{member}: profile row width differs from header")
                for number, block in enumerate(blocks, 1):
                    start, stop = block.start, block.stop
                    if all(value in (None, "") for value in row[start - 2 : stop]):
                        continue
                    if len(row) < stop:
                        raise ValueError(f"{member}: profile block has missing columns")
                    clock = str(row[start - 1])
                    yield GenerationProfileHour(
                        profileDate=date.fromisoformat(str(row[start - 2])),
                        timeHHMM=int(clock),
                        sourceTime=clock,
                        sourceTimeColumn=block.clock,
                        sourceYear=int(str(row[0])) if start == 3 else None,
                        generationMW={
                            site.column: _number(value)
                            for site, value in zip(
                                block.sites, row[start:stop], strict=True
                            )
                        },
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceBlock=number,
                    )
        if not found:
            raise ValueError(f"{filename}: no profile CSV or workbook found")
