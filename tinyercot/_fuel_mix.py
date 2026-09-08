"""Public settlement fuel-mix workbooks, including the pre-API annual archive."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from html.parser import HTMLParser
from time import strptime
from typing import Literal
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks

INDEX_URL = "https://www.ercot.com/gridinfo/generation"
_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


class FuelMixArchive(BaseModel):
    """A linked file; year bounds describe its index label."""

    yearFrom: int
    yearTo: int
    title: str
    url: str


class FuelMixInterval(BaseModel):
    """One published column; midnight ends the operating day.

    DST-labelled columns remain in their original position, including blank
    cells on ordinary days. No UTC offset or chronological ordering is inferred.
    """

    model_config = ConfigDict(extra="forbid")
    ending: time | None
    dst: bool
    sourceHeader: str
    sourceColumn: int
    energyMWh: Decimal | None
    sourceError: Literal["1/0/1900 0:00", "1.00E", "6.00E"] | None = None


class FuelMixDay(BaseModel):
    """A source row for one fuel/day, with its total and ordered interval cells."""

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    fuel: str
    settlementType: Literal["INITIAL", "FINAL"] | None
    totalMWh: Decimal | None
    intervals: list[FuelMixInterval]
    sourceMember: str
    sourceSheet: str


class FuelMixTotal(BaseModel):
    """A printed monthly or annual total; month=None denotes the annual/YTD column."""

    model_config = ConfigDict(extra="forbid")
    year: int
    month: int | None
    fuel: str | None
    energy: Decimal | None
    unit: Literal["MWh", "GWh"]
    sourcePeriod: str
    sourceMember: str
    sourceSheet: str


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.href: str | None = None
        self.title = ""
        self.files: dict[str, FuelMixArchive] = {}

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
        match = re.fullmatch(r"Fuel Mix Report: (\d{4})(?: - (\d{4}))?", title)
        url = urljoin(INDEX_URL, self.href)
        parts = urlsplit(url)
        if (
            match
            and parts.scheme == "https"
            and parts.netloc == "www.ercot.com"
            and parts.path.startswith("/files/docs/")
        ):
            self.files[url] = FuelMixArchive(
                yearFrom=int(match[1]),
                yearTo=int(match[2] or match[1]),
                title=title,
                url=url,
            )
        self.href = None


class FuelMix:
    """Anonymous historical generation by fuel, retaining original fuel labels."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[FuelMixArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links()
        links.feed(response.text)
        if not links.files:
            raise ValueError("No fuel-mix files found in ERCOT's public index")
        return sorted(links.files.values(), key=lambda item: (item.yearFrom, item.url))

    def download(self, archive: FuelMixArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[FuelMixDay]:
        """Stream daily fuel rows, filtered by inclusive operating dates.

        Older years share a ZIP download. Original fuel codes and all source
        columns are retained; missing interval cells are not converted to zero.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            if (date_from and archive.yearTo < date_from.year) or (
                date_to and archive.yearFrom > date_to.year
            ):
                continue
            for name, content in _selected_workbooks(
                self.download(archive),
                archive.url.rsplit("/", 1)[-1],
                date_from.year if date_from else None,
                date_to.year if date_to else None,
            ):
                for row in self.read(content, filename=name):
                    if (date_from is None or row.operatingDay >= date_from) and (
                        date_to is None or row.operatingDay <= date_to
                    ):
                        yield row

    def read(self, data: bytes, *, filename: str = "workbook") -> Iterator[FuelMixDay]:
        """Read XLS, XLSX or their ZIP archive, using tinyercot[files]."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content):
                if not re.fullmatch(
                    r"(?:" + "|".join(_MONTHS) + r")(?:\d{2}|\d{4})?", sheet
                ):
                    continue
                found = True
                try:
                    yield from _daily(rows, member, sheet)
                except (ValueError, TypeError) as error:
                    raise ValueError(f"{member}/{sheet}: {error}") from error
        if not found:
            raise ValueError("No monthly fuel-mix worksheets found")

    def summaries(
        self, *, year_from: int | None = None, year_to: int | None = None
    ) -> Iterator[FuelMixTotal]:
        """Read printed monthly and annual/YTD totals, with inclusive year bounds."""
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not be after year_to")
        for archive in self.archives():
            if (year_from is not None and archive.yearTo < year_from) or (
                year_to is not None and archive.yearFrom > year_to
            ):
                continue
            for name, content in _selected_workbooks(
                self.download(archive),
                archive.url.rsplit("/", 1)[-1],
                year_from,
                year_to,
            ):
                for row in self.read_summaries(content, filename=name):
                    if (year_from is None or row.year >= year_from) and (
                        year_to is None or row.year <= year_to
                    ):
                        yield row

    def read_summaries(
        self, data: bytes, *, filename: str = "workbook"
    ) -> Iterator[FuelMixTotal]:
        """Read published totals; standalone modern XLSX needs its original filename."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content):
                monthly = sheet[:3] in _MONTHS
                if not monthly and not re.fullmatch(
                    r"Summary|\d{4}(?: Summary)?", sheet
                ):
                    continue
                found = True
                year = re.search(r"(?:19|20)\d{2}", sheet + " " + member)
                if year is None:
                    raise ValueError(
                        "Supply the original filename to identify the summary year"
                    )
                if monthly:
                    total, _ = _columns(next(rows, ()))
                    for row in rows:
                        if _unlabelled_total(row, total):
                            yield FuelMixTotal(
                                year=int(year[0]),
                                month=_MONTHS.index(sheet[:3]) + 1,
                                fuel=None,
                                energy=_number(row[total]),
                                unit="MWh",
                                sourcePeriod=sheet,
                                sourceMember=member,
                                sourceSheet=sheet,
                            )
                else:
                    yield from _totals(rows, int(year[0]), member, sheet)
        if not found:
            raise ValueError("No fuel-mix summary worksheet found")


def _selected_workbooks(
    data: bytes, filename: str, year_from: int | None, year_to: int | None
) -> Iterator[tuple[str, bytes]]:
    for member, content in _workbooks(data):
        name = filename if member in {"workbook.xls", "workbook.xlsx"} else member
        match = re.fullmatch(
            r"IntGenByFuel(\d{4})\.xlsx?", name.rsplit("/", 1)[-1], re.IGNORECASE
        )
        if match and (
            (year_from is not None and int(match[1]) < year_from)
            or (year_to is not None and int(match[1]) > year_to)
        ):
            continue
        yield name, content


def _clock(value: object) -> tuple[time | None, bool, str]:
    if re.fullmatch(r"DST\d+", str(value), re.IGNORECASE):
        return None, True, str(value)
    if isinstance(value, datetime):
        return value.time(), False, str(value)
    if isinstance(value, timedelta):
        ending, dst, _ = _clock(value.total_seconds() / 86400)
        return ending, dst, str(value)
    if isinstance(value, (int, float)):
        minutes = round(value * 1440)
        if not 0 <= minutes <= 1440 or abs(value * 1440 - minutes) > 0.001:
            raise ValueError(f"Unsupported interval header: {value!r}")
        value = time(minutes // 60 % 24, minutes % 60)
    if isinstance(value, time):
        return value, False, value.strftime("%H:%M")
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?: \(?(DST)\)?)?", str(value).strip())
    if match:
        return time(int(match[1]), int(match[2])), bool(match[3]), str(value)
    raise ValueError(f"Unsupported interval header: {value!r}")


def _columns(header: tuple[object, ...]) -> tuple[int, int | None]:
    names = [str(v).strip() if v is not None else "" for v in header]
    if names[:4] in (
        ["Date", "Fuel", "Settlement Type", "Total"],
        ["Date", "Fuel Type", "Settlement Type", "Total"],
    ):
        total, settlement = 3, 2
    elif names[:3] == ["Date", "Fuel", "Total"]:
        total, settlement = 2, None
    elif names[0] in {"Date - Fuel", "Date-Fuel", "DateFuel"} and names[1] in {
        "Daily MWH",
        "Total",
    }:
        total, settlement = 1, None
    else:
        raise ValueError(f"Unsupported fuel-mix header: {names[:4]}")
    return total, settlement


def _unlabelled_total(row: tuple[object, ...], total: int) -> bool:
    return (
        len(row) > total
        and row[total] not in (None, "")
        and all(value in (None, "") for i, value in enumerate(row) if i != total)
    )


def _daily(
    rows: Iterator[tuple[object, ...]], member: str, sheet: str
) -> Iterator[FuelMixDay]:
    header = next(rows, ())
    total, settlement = _columns(header)
    columns = {
        i: _clock(v) for i, v in enumerate(header) if i > total and v not in (None, "")
    }
    for row in rows:
        if all(v in (None, "") for v in row) or _unlabelled_total(row, total):
            continue
        if total == 1:
            match = re.fullmatch(r"(\d{2}/\d{2}/\d{2})\s*[-_]\s*(.+)", str(row[0]))
            if not match:
                raise ValueError(f"Unsupported date/fuel label: {row[0]!r}")
            day, fuel = date(*strptime(match[1], "%m/%d/%y")[:3]), match[2]
        else:
            if not isinstance(row[0], (date, datetime)):
                raise ValueError(f"Unsupported operating date: {row[0]!r}")
            day = row[0].date() if isinstance(row[0], datetime) else row[0]
            fuel = str(row[1])
        intervals = []
        indices = set(columns) | {
            i for i in range(total + 1, len(row)) if row[i] not in (None, "")
        }
        for i in sorted(indices):
            ending, dst, label = columns.get(i, (None, False, ""))
            value = row[i] if i < len(row) else None
            error = value if value in {"1/0/1900 0:00", "1.00E", "6.00E"} else None
            intervals.append(
                FuelMixInterval.model_validate(
                    {
                        "ending": ending,
                        "dst": dst,
                        "sourceHeader": label,
                        "sourceColumn": i + 1,
                        "energyMWh": None if error else _number(value),
                        "sourceError": error,
                    }
                )
            )
        yield FuelMixDay.model_validate(
            {
                "operatingDay": day,
                "fuel": fuel,
                "settlementType": row[settlement] if settlement is not None else None,
                "totalMWh": _number(row[total]),
                "intervals": intervals,
                "sourceMember": member,
                "sourceSheet": sheet,
            }
        )


def _totals(
    rows: Iterator[tuple[object, ...]], year: int, member: str, sheet: str
) -> Iterator[FuelMixTotal]:
    header = next(
        (r for r in rows if r and r[0] in {"Fuel Totals", "Energy, GWh"}), None
    )
    if header is None:
        raise ValueError(f"{member}/{sheet}: Missing fuel-mix summary header")
    unit = "GWh" if header[0] == "Energy, GWh" else "MWh"
    columns: list[tuple[int, int | None, str]] = []
    for i, value in enumerate(header[1:], 1):
        if value in (None, ""):
            continue
        label = str(value)
        if label.rstrip("*") in _MONTHS:
            month = _MONTHS.index(label.rstrip("*")) + 1
        elif label == "Total" or re.fullmatch(r"(?:\d{4} )?MWH", label):
            month = None
        else:
            raise ValueError(f"Unsupported fuel-mix period: {label}")
        columns.append((i, month, label))
    for row in rows:
        if (
            not row
            or row[0] in (None, "")
            or not any(i < len(row) and row[i] not in (None, "") for i, _, _ in columns)
        ):
            continue
        for i, month, label in columns:
            yield FuelMixTotal.model_validate(
                {
                    "year": year,
                    "month": month,
                    "fuel": str(row[0]),
                    "energy": _number(row[i] if i < len(row) else None),
                    "unit": unit,
                    "sourcePeriod": label,
                    "sourceMember": member,
                    "sourceSheet": sheet,
                }
            )
