"""Public hourly load files, independent of the Public Reports API."""

from __future__ import annotations

import re
from collections.abc import Iterator
from copy import copy
from datetime import date, datetime, timedelta
from decimal import Decimal
from html.parser import HTMLParser
from io import BytesIO
from struct import unpack
from time import strptime
from typing import Literal
from urllib.parse import urljoin, urlsplit
from zipfile import BadZipFile, ZipFile, ZipInfo

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import LegacyHourlyLoad, read_legacy

INDEX_URL = "https://www.ercot.com/gridinfo/load/load_hist"
_COLUMNS = (
    "coast",
    "east",
    "farWest",
    "north",
    "northC",
    "southern",
    "southC",
    "west",
    "total",
)
_HEADERS = (
    (
        "Hour_End",
        "COAST",
        "EAST",
        "FAR_WEST",
        "NORTH",
        "NORTH_C",
        "SOUTHERN",
        "SOUTH_C",
        "WEST",
        "ERCOT",
    ),
    (
        "Hour Ending",
        "COAST",
        "EAST",
        "FWEST",
        "NORTH",
        "NCENT",
        "SOUTH",
        "SCENT",
        "WEST",
        "ERCOT",
    ),
    (
        "HourEnding",
        "COAST",
        "EAST",
        "FWEST",
        "NORTH",
        "NCENT",
        "SOUTH",
        "SCENT",
        "WEST",
        "ERCOT",
    ),
)


class LoadArchive(BaseModel):
    """An actual index link; year is the published label, not a coverage guarantee."""

    year: int
    title: str
    url: str


class WeatherZoneLoad(BaseModel):
    """One published hour, keeping weather zones and the ERCOT total distinct.

    Hour ending is 1–24 on operatingDay. The source's literal DST suffix is kept
    without interpreting it as a UTC offset or the API's repeat-hour flag.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    hourEnding: int
    dstLabel: Literal["DST"] | None = None
    sourceHourEnding: str
    sourceMember: str
    sourceSheet: str
    coast: Decimal | None
    east: Decimal | None
    farWest: Decimal | None
    north: Decimal | None
    northC: Decimal | None
    southern: Decimal | None
    southC: Decimal | None
    west: Decimal | None
    total: Decimal | None


class _Links(HTMLParser):
    def __init__(
        self,
        *,
        index_url: str = INDEX_URL,
        title_pattern: str = r"(\d{4}) ERCOT Hourly Load Data(?: \(Raw\))?",
    ) -> None:
        super().__init__()
        self.index_url = index_url
        self.title_pattern = title_pattern
        self.href: str | None = None
        self.title = ""
        self.archives: dict[str, LoadArchive] = {}

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
        match = re.fullmatch(self.title_pattern, title)
        url = urljoin(self.index_url, self.href)
        parts = urlsplit(url)
        if (
            match
            and parts.scheme == "https"
            and parts.netloc == "www.ercot.com"
            and parts.path.startswith("/files/docs/")
        ):
            self.archives[url] = LoadArchive(year=int(match[1]), title=title, url=url)
        self.href = None


class HourlyLoad:
    """Public hourly loads across system, control-area and weather-zone formats."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[LoadArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links()
        links.feed(response.text)
        if not links.archives:
            raise ValueError("No hourly load archives found in ERCOT's public index")
        return sorted(links.archives.values(), key=lambda item: (item.year, item.url))

    def download(self, archive: LoadArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def legacy(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[LegacyHourlyLoad]:
        """Read pre-2002 system, control-area and LSE hourly files.

        Date bounds apply to file contents. All older files are considered because
        index year labels disagree with their contents. Overlaps remain visible.
        Companion forecast tables are not included in this hourly reader.
        """
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            if archive.year >= 2002:
                continue
            for row in self.read_legacy(
                self.download(archive),
                filename=urlsplit(archive.url).path.rsplit("/", 1)[-1],
            ):
                if (date_from is None or row.operatingDay >= date_from) and (
                    date_to is None or row.operatingDay <= date_to
                ):
                    yield row

    def read_legacy(
        self, data: bytes, *, filename: str = "download"
    ) -> Iterator[LegacyHourlyLoad]:
        """Read saved legacy files; EEI text needs its original filename."""
        yield from read_legacy(data, filename=filename)

    def weather_zones(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[WeatherZoneLoad]:
        """Read weather-zone archives with inclusive operating-date bounds.

        Older control-area/system-only sources use different formats and are not
        included. Source errors propagate; missing years are never synthesized.
        """
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            if (
                archive.year < 2002
                or (date_from and archive.year < date_from.year)
                or (date_to and archive.year > date_to.year)
            ):
                continue
            yield from (
                row
                for row in self.read_weather_zones(self.download(archive))
                if (date_from is None or row.operatingDay >= date_from)
                and (date_to is None or row.operatingDay <= date_to)
            )

    def read_weather_zones(self, data: bytes) -> Iterator[WeatherZoneLoad]:
        """Read an XLS/XLSX workbook or ZIP with the optional ``files`` extra."""
        found = False
        for filename, content in _workbooks(data):
            for sheet, lines in _sheets(content):
                header = next(lines, ())
                while header and header[-1] in (None, ""):
                    header = header[:-1]
                if header not in _HEADERS:
                    raise ValueError(
                        f"{filename}/{sheet}: unsupported weather-zone header"
                    )
                found = True
                for line, cells in enumerate(lines, 2):
                    while cells and cells[-1] in (None, ""):
                        cells = cells[:-1]
                    if not cells:
                        continue
                    try:
                        if len(cells) > 10:
                            raise ValueError(
                                "Expected hour ending and nine load columns"
                            )
                        cells += (None,) * (10 - len(cells))
                        day, hour, dst = _clock(cells[0])
                        values: dict[str, object] = {
                            "operatingDay": day,
                            "hourEnding": hour,
                            "dstLabel": dst,
                            "sourceHourEnding": str(cells[0]),
                            "sourceMember": filename,
                            "sourceSheet": sheet,
                        }
                        for name, value in zip(_COLUMNS, cells[1:], strict=True):
                            if value is None or value == "":
                                values[name] = None
                                continue
                            if not isinstance(
                                value, (int, float, Decimal)
                            ) or isinstance(value, bool):
                                raise TypeError(f"Missing or nonnumeric load in {name}")
                            values[name] = Decimal(str(value))
                        yield WeatherZoneLoad.model_validate(values)
                    except (ValueError, TypeError) as error:
                        raise ValueError(
                            f"{filename}/{sheet}:{line}: {error}"
                        ) from error
        if not found:
            raise ValueError("Download contains no weather-zone workbooks")


def _workbooks(data: bytes) -> Iterator[tuple[str, bytes]]:
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        yield "workbook.xls", data
        return
    with ZipFile(BytesIO(data)) as archive:
        if "[Content_Types].xml" in archive.namelist():
            yield "workbook.xlsx", data
            return
        for member in archive.infolist():
            name = member.filename
            if name.lower().endswith((".xls", ".xlsx")):
                yield name, _workbook_member(archive, member, data)
            elif name.lower().endswith(".zip"):
                yield from _workbooks(_workbook_member(archive, member, data))


def _workbook_member(archive: ZipFile, member: ZipInfo, data: bytes) -> bytes:
    try:
        return archive.read(member)
    except BadZipFile:
        # ERCOT's 2026 annual ZIP has stale directory sizes/CRC, but a complete
        # local header and intact workbook. Retry using that header; ZipFile
        # still verifies the filename, member boundaries and local CRC.
        header = data[member.header_offset : member.header_offset + 30]
        if len(header) != 30 or header[:4] != b"PK\x03\x04":
            raise
        _, _, flags, method, _, _, crc, compressed, size, _, _ = unpack(
            "<4s5H3I2H", header
        )
        if (
            flags != member.flag_bits
            or flags & 9  # Encrypted entries or sizes supplied by a descriptor.
            or method != member.compress_type
            or max(compressed, size) == 0xFFFFFFFF  # ZIP64 needs extra fields.
            or (crc, compressed, size)
            == (member.CRC, member.compress_size, member.file_size)
        ):
            raise
        local = copy(member)
        local.CRC, local.compress_size, local.file_size = crc, compressed, size
        content = archive.read(local)
        if len(content) != size:
            raise BadZipFile(f"{member.filename}: local uncompressed size mismatch")
        return content


def _sheets(
    data: bytes, *, date_columns: tuple[int, ...] = (0,), preserve_types: bool = False
) -> Iterator[tuple[str, Iterator[tuple[object, ...]]]]:
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        try:
            import xlrd
        except ImportError as error:
            raise ImportError(
                "Install tinyercot[files] to read XLS archives"
            ) from error
        with xlrd.open_workbook(file_contents=data) as book:
            for sheet in book.sheets():

                def rows(
                    sheet: xlrd.sheet.Sheet = sheet,
                ) -> Iterator[tuple[object, ...]]:
                    for i in range(sheet.nrows):
                        values: list[object] = list(sheet.row_values(i))
                        if preserve_types:
                            for j, cell in enumerate(sheet.row(i)):
                                if cell.ctype == xlrd.XL_CELL_DATE:
                                    values[j] = xlrd.xldate_as_datetime(
                                        float(cell.value), book.datemode
                                    )
                                elif cell.ctype == xlrd.XL_CELL_ERROR:
                                    values[j] = xlrd.error_text_from_code[
                                        int(cell.value)
                                    ]
                                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                                    values[j] = bool(cell.value)
                        for column in date_columns:
                            value = values[column] if len(values) > column else None
                            if i and isinstance(value, float):
                                values[column] = xlrd.xldate_as_datetime(
                                    value, book.datemode
                                )
                        yield tuple(values)

                yield sheet.name, rows()
    else:
        try:
            from openpyxl import load_workbook
        except ImportError as error:
            raise ImportError(
                "Install tinyercot[files] to read XLSX archives"
            ) from error
        book_xlsx = load_workbook(BytesIO(data), read_only=True, data_only=True)
        try:
            for sheet_xlsx in book_xlsx:
                sheet_xlsx.reset_dimensions()
                yield sheet_xlsx.title, sheet_xlsx.values
        finally:
            book_xlsx.close()


def _clock(value: object) -> tuple[date, int, Literal["DST"] | None]:
    if isinstance(value, datetime):
        # Old Excel serials have millisecond noise despite displaying whole hours.
        stamp = (value + timedelta(milliseconds=500)).replace(microsecond=0)
        if stamp.minute or stamp.second:
            raise ValueError("Expected a whole hour-ending value")
        return (stamp - timedelta(hours=1)).date(), stamp.hour or 24, None
    if isinstance(value, str):
        match = re.fullmatch(r"(\d{2}/\d{2}/\d{4}) (\d{2}):00( DST)?", value)
        if match and 1 <= int(match[2]) <= 24:
            return (
                date(*strptime(match[1], "%m/%d/%Y")[:3]),
                int(match[2]),
                "DST" if match[3] else None,
            )
    raise ValueError(f"Unsupported hour ending: {value!r}")
