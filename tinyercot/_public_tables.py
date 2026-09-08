"""Typed tables published as direct downloads on ERCOT's public website."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from time import strptime
from typing import Generic, Literal, TypeVar
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks

T = TypeVar("T", bound=BaseModel)


class PublicFile(BaseModel):
    """An actual public download link, with no inferred coverage dates."""

    title: str
    url: str


class _FileLinks(HTMLParser):
    def __init__(self, index_url: str, title_pattern: str) -> None:
        super().__init__()
        self.index_url = index_url
        self.title_pattern = title_pattern
        self.href: str | None = None
        self.title = ""
        self.files: dict[str, PublicFile] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.title = ""

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.title += data

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self.href is None:
            return
        title = " ".join(self.title.split())
        url = urljoin(self.index_url, self.href)
        parts = urlsplit(url)
        if (
            re.fullmatch(self.title_pattern, title)
            and parts.scheme == "https"
            and parts.netloc == "www.ercot.com"
            and parts.path.startswith("/files/docs/")
        ):
            self.files[url] = PublicFile(title=title, url=url)
        self.href = None


class _PublicFiles:
    index_url: str
    title_pattern: str

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def files(self) -> list[PublicFile]:
        """Discover current download links; labels do not establish coverage."""
        response = self._http.get(self.index_url, follow_redirects=True)
        response.raise_for_status()
        links = _FileLinks(self.index_url, self.title_pattern)
        links.feed(response.text)
        if not links.files:
            raise ValueError(f"No matching public files found at {self.index_url}")
        return list(links.files.values())

    def download(self, file: PublicFile) -> bytes:
        response = self._http.get(file.url, follow_redirects=True)
        response.raise_for_status()
        return response.content


class _YearLinks(_FileLinks):
    def __init__(self, index_url: str, title_pattern: str) -> None:
        super().__init__(index_url, title_pattern)
        self.years: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        super().handle_starttag(tag, attrs)
        if tag == "a" and self.href:
            url = urljoin(self.index_url, self.href)
            parts = urlsplit(url)
            if (
                parts.scheme == "https"
                and parts.netloc == "www.ercot.com"
                and re.fullmatch(
                    rf"{re.escape(urlsplit(self.index_url).path)}/\d{{4}}", parts.path
                )
            ):
                self.years.add(url)


def _year_files(
    client: httpx.Client, index_url: str, title_pattern: str
) -> list[PublicFile]:
    """Collect actual download links from an index and its linked annual pages."""

    def links(url: str) -> _YearLinks:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        parser = _YearLinks(url, title_pattern)
        parser.feed(response.text)
        return parser

    current = links(index_url)
    files = dict(current.files)
    for url in sorted(current.years):
        files.update(links(url).files)
    if not files:
        raise ValueError(f"No matching public files found at {index_url}")
    return sorted(files.values(), key=lambda f: f.url)


class _ResourceFiles(_PublicFiles):
    index_url = "https://www.ercot.com/gridinfo/resource"

    def files(self) -> list[PublicFile]:
        """Discover resource workbooks in current and linked historical indexes."""
        workbooks = [
            f
            for f in _year_files(self._http, self.index_url, self.title_pattern)
            if urlsplit(f.url).path.lower().endswith((".xlsx", ".xls"))
        ]
        if not workbooks:
            raise ValueError(
                "No matching resource workbooks found in ERCOT's public indexes"
            )
        return workbooks


class _PublicTable(_PublicFiles, ABC, Generic[T]):
    def rows(self, *, where: Callable[[T], bool] | None = None) -> Iterator[T]:
        """Read every linked file with an optional typed predicate."""
        for file in self.files():
            yield from self.read(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[T], bool] | None = None,
    ) -> Iterator[T]:
        """Read saved source files or ZIPs, keeping overlapping files distinct."""
        for record in self._read(data, filename):
            if where is None or where(record):
                yield record

    @abstractmethod
    def _read(self, data: bytes, filename: str) -> Iterator[T]: ...


class CrrTimeOfUse(BaseModel):
    """One delivery month and the source's CRR time-of-use hour counts."""

    model_config = ConfigDict(extra="forbid")
    month: date
    offPeakHours: int
    peakWDHours: int
    peakWEHours: int
    totalHours: int
    sourceMember: str
    sourceSheet: str


class CrrHours(_PublicTable[CrrTimeOfUse]):
    """Monthly CRR trading-hour calendars; parsing uses tinyercot[files]."""

    index_url = "https://www.ercot.com/mktinfo/crr"
    title_pattern = r"CRR Time of Use Hours"

    def _read(self, data: bytes, filename: str) -> Iterator[CrrTimeOfUse]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                for cells in rows:
                    if cells == (
                        "Year",
                        "Month",
                        "OffPeak",
                        "PeakWD",
                        "PeakWE",
                        "Total",
                    ):
                        break
                else:
                    raise ValueError(f"{member}/{sheet}: Missing CRR hour header")
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != 6:
                        raise ValueError(f"{member}/{sheet}: Unexpected CRR row width")
                    year = str(cells[0]).removesuffix(".0")
                    month = date(*strptime(f"{year} {cells[1]}", "%Y %B")[:3])
                    yield CrrTimeOfUse.model_validate(
                        {
                            "month": month,
                            "offPeakHours": cells[2],
                            "peakWDHours": cells[3],
                            "peakWEHours": cells[4],
                            "totalHours": cells[5],
                            "sourceMember": member,
                            "sourceSheet": sheet,
                        }
                    )
        if not found:
            raise ValueError("Download contains no CRR hour tables")


class PolrUsage(BaseModel):
    """Retail territory/class totals with separate count and energy periods.

    Counts describe active ESIIDs with usage on snapshotDate. Energy describes
    all ESIIDs active during the inclusive energy period, not just that snapshot.
    """

    model_config = ConfigDict(extra="forbid")
    territory: str
    premiseType: Literal[
        "Residential",
        "Small Non-Residential",
        "Medium Non-Residential",
        "Large Non-Residential",
    ]
    snapshotDate: date
    energyPeriodStart: date
    energyPeriodEnd: date
    activeEsiids: int
    energyKWh: Decimal | None
    sourceMember: str
    sourceSheet: str
    sourceNotes: list[str]


class PolrHistory(_PublicTable[PolrUsage]):
    """Public provider-of-last-resort counts and energy, using tinyercot[files]."""

    index_url = "https://www.ercot.com/mktinfo/retail"
    title_pattern = r"POLR Counts Energy \d{4} Report(?: Final)?"

    def _read(self, data: bytes, filename: str) -> Iterator[PolrUsage]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            # Cover notes may precede or follow the table in a saved workbook.
            tables = [
                (sheet, list(rows)) for sheet, rows in _sheets(content, date_columns=())
            ]
            notes = [
                c
                for sheet, rows in tables
                if sheet == "PUCT_Even_Year_Cover_Page"
                for cells in rows
                for c in cells
                if isinstance(c, str) and c
            ]
            for sheet, table in tables:
                if sheet == "PUCT_Even_Year_Cover_Page":
                    continue
                rows = iter(table)
                for cells in rows:
                    if cells[:2] == ("POLR Territory", "Premise Type"):
                        break
                else:
                    raise ValueError(f"{member}/{sheet}: Missing POLR header")
                count = re.fullmatch(r"# Active ESIIDs Total \((.+)\)", str(cells[2]))
                energy = re.fullmatch(r"Annual kWh \((.+) - (.+)\)", str(cells[3]))
                if not count or not energy:
                    raise ValueError(
                        f"{member}/{sheet}: Missing POLR reporting periods"
                    )
                snapshot = date(*strptime(count[1], "%m/%d/%Y")[:3])
                start = date(*strptime(energy[1], "%m/%d/%Y")[:3])
                end = date(*strptime(energy[2], "%m/%d/%Y")[:3])
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != 4:
                        raise ValueError(f"{member}/{sheet}: Unexpected POLR row width")
                    yield PolrUsage.model_validate(
                        {
                            "territory": cells[0],
                            "premiseType": cells[1],
                            "snapshotDate": snapshot,
                            "energyPeriodStart": start,
                            "energyPeriodEnd": end,
                            "activeEsiids": cells[2],
                            "energyKWh": _number(cells[3]),
                            "sourceMember": member,
                            "sourceSheet": sheet,
                            "sourceNotes": notes,
                        }
                    )
        if not found:
            raise ValueError("Download contains no POLR tables")


class LoadShedShare(BaseModel):
    """An operator's published load share, not shed MW or outage probability.

    The effective start comes from the workbook note; no end date is assumed.
    """

    model_config = ConfigDict(extra="forbid")
    season: Literal["summer", "winter"]
    transmissionOperator: str
    loadSharePercent: Decimal | None
    effectiveFrom: date
    sourceHeader: str
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str


class LoadShed(_PublicTable[LoadShedShare]):
    """Published seasonal operator load shares, read with tinyercot[files]."""

    index_url = "https://www.ercot.com/gridinfo/load"
    title_pattern = r"(?:Summer|Winter) Load Shed Table"

    def _read(self, data: bytes, filename: str) -> Iterator[LoadShedShare]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, source in _sheets(content, date_columns=()):
                rows = list(source)
                header = str(rows[0][1]) if rows else ""
                match = re.fullmatch(
                    r"(Summer|Winter) Total Transmission Operator Load \(% MW\)", header
                )
                if not match or rows[0][0] != "Transmission Operator":
                    raise ValueError(
                        f"{member}/{sheet}: Missing load-shed share header"
                    )
                notes = [
                    str(row[0])
                    for row in rows
                    if row and str(row[0]).startswith(("*", "Note:"))
                ]
                effective = re.search(
                    r"goes into effect on (\d{2}/\d{2}/\d{4})", "\n".join(notes)
                )
                if effective is None:
                    raise ValueError(
                        f"{member}/{sheet}: Missing load-shed effective date"
                    )
                found = True
                for row in rows[1:]:
                    if (
                        not row
                        or row[0] in (None, "")
                        or str(row[0]).startswith(("*", "Note:"))
                    ):
                        continue
                    yield LoadShedShare(
                        season="summer" if match[1] == "Summer" else "winter",
                        transmissionOperator=str(row[0]),
                        loadSharePercent=_number(row[1]),
                        effectiveFrom=date(*strptime(effective[1], "%m/%d/%Y")[:3]),
                        sourceHeader=header,
                        sourceNotes=notes,
                        sourceMember=member,
                        sourceSheet=sheet,
                    )
        if not found:
            raise ValueError("Download contains no operator load-share tables")
