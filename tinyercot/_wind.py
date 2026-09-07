"""Published wind integration archives on ercot.com, independent of the API."""

# Report clocks are published without UTC offsets.
# ruff: noqa: DTZ007

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime, time
from decimal import Decimal
from html.parser import HTMLParser
from io import BytesIO
from typing import Literal
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

INDEX_URL = "https://www.ercot.com/gridinfo/generation/ibr-integration-reports"
_NUMBER = r"[\d,]+(?:\.\d+)?"
_DATE = r"\d{2}/\d{2}/(?:\d{4}|\d{2})"
_TIME = r"\d{1,2}:\d{2}(?::\d{2})?"


class WindArchive(BaseModel):
    """An annual or monthly ZIP actually linked by ERCOT's public index."""

    year: int
    month: int | None = None
    url: str


class WindDailyValues(BaseModel):
    """Printed first-page values, in MW and percent, with source-local clocks.

    Older reports publish only a date for the generation record. Their integration
    and penetration labels remain distinct from the modern, explicit metrics.
    Fields absent from a report stay None; chart positions are not estimated.
    """

    model_config = ConfigDict(extra="forbid")
    reportDate: date
    reportDateText: str
    reportType: Literal["Integration", "Penetration"]
    sourceMember: str
    peakLoadLabel: str = "Peak Load"
    peakLoadMW: Decimal
    peakLoadHour: int
    windAtPeakLoadMW: Decimal | None = None
    maxWindLabel: str = "Max Wind"
    maxWindMW: Decimal
    maxWindTime: time
    windIntegrationPercent: Decimal | None = None
    windPenetrationPercent: Decimal | None = None
    penetrationAtMaxWindPercent: Decimal | None = None
    maxWindPenetrationPercent: Decimal | None = None
    maxWindPenetrationTime: time | None = None
    windAtMaxPenetrationMW: Decimal | None = None
    recordWindLabel: str = "Record Wind Generation"
    recordWindMW: Decimal
    recordWindDate: date
    recordWindTime: time | None = None
    penetrationAtRecordWindPercent: Decimal | None = None
    recordWindPenetrationPercent: Decimal | None = None
    recordWindPenetrationTime: datetime | None = None
    windAtRecordPenetrationMW: Decimal | None = None
    sourceNotes: str | None = None


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.archives: dict[str, WindArchive] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        url = urljoin(INDEX_URL, href)
        parts = urlsplit(url)
        match = re.fullmatch(
            r"/files/docs/\d{4}/\d{2}/\d{2}/ERCOTWindIntegrationReport_(Jan)?(\d{4})\.zip",
            parts.path,
        )
        if parts.scheme == "https" and parts.netloc == "www.ercot.com" and match:
            self.archives[url] = WindArchive(
                year=int(match[2]), month=1 if match[1] else None, url=url
            )


class WindIntegration:
    """Discover, download and read public wind PDFs; decoding needs the pdf extra."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[WindArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links()
        links.feed(response.text)
        if not links.archives:
            raise ValueError("No wind archives found in ERCOT's public index")
        return sorted(
            links.archives.values(), key=lambda item: (item.year, item.month or 0)
        )

    def download(self, archive: WindArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[WindDailyValues]:
        """Read linked archives using inclusive report-date bounds.

        Only overlapping ZIPs are downloaded. Missing days and corrected or
        duplicate reports are preserved; report dates come from the PDFs.
        """
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            start = date(archive.year, archive.month or 1, 1)
            end = (
                date(archive.year, 1, 31)
                if archive.month
                else date(archive.year, 12, 31)
            )
            if (date_from and end < date_from) or (date_to and start > date_to):
                continue
            for row in self.read(self.download(archive)):
                if (date_from is None or row.reportDate >= date_from) and (
                    date_to is None or row.reportDate <= date_to
                ):
                    yield row

    def read(self, data: bytes) -> Iterator[WindDailyValues]:
        """Read a saved PDF or ZIP, including nested ZIPs and uppercase .PDF."""
        from ._history import _archive_files

        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ImportError("Install tinyercot[pdf] to read wind reports") from error
        members = (
            iter([("report.pdf", data)])
            if data.startswith(b"%PDF-")
            else _archive_files(data, "*.[pP][dD][fF]")
        )
        found = False
        for filename, content in members:
            found = True
            try:
                book = PdfReader(BytesIO(content))
                text = (
                    " ".join(book.pages[0].extract_text().split()) if book.pages else ""
                )
                yield self._read_text(text, filename)
            except ValueError as error:
                raise ValueError(f"{filename}: {error}") from error
        if not found:
            raise ValueError("Download contains no wind PDF reports")

    @staticmethod
    def _read_text(text: str, filename: str) -> WindDailyValues:
        header = re.search(
            r"Wind (Integration|Penetration) Report\s*:\s*(\d{2}/\d{2}/\d{2,5})(?!\d)",
            text,
        )
        if not header:
            raise ValueError("Unsupported wind report header")
        values: dict[str, object] = {
            "reportDate": _date(header[2]),
            "reportDateText": header[2],
            "reportType": header[1],
            "sourceMember": filename,
        }
        body = re.sub(r"(?<=\d),\s+(?=\d)", ",", text[header.end() :].strip())
        if body.startswith("Current Daily Values:"):
            match = _MODERN.match(body)
        else:
            match = _LEGACY.match(body) or _INTERLEAVED.match(body)
        if not match:
            raise ValueError("Unsupported wind summary table")
        fields = match.groupdict()
        label = fields.pop("percentLabel", None)
        percent = fields.pop("legacyPercent", None)
        if label and percent:
            fields[f"wind{label}Percent"] = percent
        for key, value in fields.items():
            if value is None:
                continue
            if key.endswith("Label"):
                values[key] = value
            elif key == "peakLoadHour":
                values[key] = int(value)
            elif key == "recordWindDate":
                values[key] = _date(value)
            elif key == "recordWindTimestamp":
                stamp = datetime.strptime(value, "%m/%d/%Y %H:%M")
                values["recordWindDate"] = stamp.date()
                values["recordWindTime"] = stamp.time()
            elif key == "recordWindPenetrationTime":
                values[key] = datetime.strptime(value, "%m/%d/%Y %H:%M")
            elif key.endswith("Time"):
                values[key] = time.fromisoformat(
                    value.zfill(8 if value.count(":") == 2 else 5)
                )
            else:
                values[key] = Decimal(value.replace(",", ""))
        remainder = body[match.end() :].strip()
        if remainder.startswith("Note:"):
            values["sourceNotes"] = remainder.split(" 0 ", 1)[0]
        note = re.search(r"(\* Wind Record.*?)(?:System Operations \d+)?$", body)
        if note:
            values["sourceNotes"] = note[1].strip()
        return WindDailyValues.model_validate(values)


def _date(value: str) -> date:
    # The May 14 report prints 12013 in its heading; its chart and filename
    # both specify 2013. Keep the original heading in reportDateText.
    if value == "05/14/12013":
        return date(2013, 5, 14)
    return datetime.strptime(
        value, "%m/%d/%Y" if len(value) == 10 else "%m/%d/%y"
    ).date()


def _mw(field: str) -> str:
    return rf"(?P<{field}>{_NUMBER})\s*MW"


def _percent(field: str) -> str:
    return rf"(?P<{field}>{_NUMBER})\s*%"


_PEAK = (
    rf"(?P<peakLoadLabel>Peak Load|New Record Winter Peak|New Peak Demand Record) {_mw('peakLoadMW')} Load Peak Hour(?: \(HE\))? (?P<peakLoadHour>\d{{1,2}}) "
    rf"(?:Wind [Oo]ver Peak {_mw('windAtPeakLoadMW')} )?"
    rf"(?P<recordWindLabel>(?:Previous )?Wind Record) (?P<recordWindDate>{_DATE}) "
)
_LEGACY = re.compile(
    _PEAK
    + rf"{_mw('recordWindMW')} (?P<maxWindLabel>Max Wind [Vv]alue(?:\*| \((?:Instantaneous|New Record)\))?) {_mw('maxWindMW')} "
    rf"Wind Peak (?:Hour|Time) (?P<maxWindTime>{_TIME}) "
    rf"Wind (?P<percentLabel>Integration|Penetration) % (?P<legacyPercent>{_NUMBER})\s*%?(?= |$)"
)
_INTERLEAVED = re.compile(
    _PEAK
    + rf"(?P<maxWindLabel>Max Wind [Vv]alue|New Wind Record) {_mw('recordWindMW')} {_mw('maxWindMW')} "
    rf"Wind Peak (?:Hour|Time) Wind (?P<percentLabel>Integration|Penetration) % "
    rf"(?P<maxWindTime>{_TIME}) (?P<legacyPercent>{_NUMBER})\s*%?(?= |$)"
)
_MODERN = re.compile(
    rf"Current Daily Values: Peak Load {_mw('peakLoadMW')} "
    rf"Peak Load Hour \(HE\) (?P<peakLoadHour>\d{{1,2}}) "
    rf"Wind at Peak Load Hour {_mw('windAtPeakLoadMW')} Max Wind {_mw('maxWindMW')} "
    rf"Max Wind Time (?P<maxWindTime>{_TIME}) "
    rf"Penetration at Max Wind Time {_percent('penetrationAtMaxWindPercent')} "
    rf"Max Wind Penetration {_percent('maxWindPenetrationPercent')} "
    rf"Max Wind Penetration Time (?P<maxWindPenetrationTime>{_TIME}) "
    rf"Wind Generation at Max Wind Penetration Time {_mw('windAtMaxPenetrationMW')} "
    rf"All Time Record Values: Record Wind Generation {_mw('recordWindMW')} "
    rf"Record Wind Generation Time (?P<recordWindTimestamp>{_DATE} {_TIME}) "
    rf"Penetration at Record Wind Generation Time {_percent('penetrationAtRecordWindPercent')} "
    rf"Record Wind Penetration {_percent('recordWindPenetrationPercent')} "
    rf"Record Wind Penetration Time (?P<recordWindPenetrationTime>{_DATE} {_TIME}) "
    rf"Wind Generation at Record Wind Penetration {_mw('windAtRecordPenetrationMW')}(?= |$)"
)
