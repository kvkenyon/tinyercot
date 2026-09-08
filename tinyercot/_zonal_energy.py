"""Original zonal-market generation and load energy, before the nodal market."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from time import strptime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._energy import EnergyInterval
from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._loss_factors import _interval_label
from ._public_tables import PublicFile, _PublicFiles, _year_files

_Kind = Literal["generation", "load"]


class ZonalSourceNumber(BaseModel):
    """A numeric source cell whose header does not establish its meaning/unit."""

    model_config = ConfigDict(extra="forbid")
    column: int
    value: Decimal
    sourceHeader: str | None


class ZonalEnergyDay(BaseModel):
    """One original zone/day; zone codes retain their historical definitions.

    Values, blanks and reported totals are never reconciled. Extra source
    numbers are not assumed to be interval energy. Unknown clock labels on
    extended load rows remain None. Source timestamps are not publication times.
    """

    model_config = ConfigDict(extra="forbid")
    kind: _Kind
    operatingDay: date
    zone: str
    totalMWh: Decimal | None
    intervals: list[EnergyInterval]
    recorder: str | None
    channel: int | None
    origin: str | None
    sourceTimestamp: datetime | None
    sourceNumbers: list[ZonalSourceNumber]
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceFile: PublicFile | None = None


class ZonalEnergyTotal(BaseModel):
    """A published summary or detail subtotal, separate from daily observations.

    share is the original fractional value, even under a percent-formatted
    header. Cached totals are not recomputed. The original label, header and
    notes retain unlabeled grand totals and source inconsistencies.
    """

    model_config = ConfigDict(extra="forbid")
    kind: _Kind
    year: int | None
    scope: Literal["summary", "detail_total"]
    zone: str | None
    totalMWh: Decimal | None
    share: Decimal | None
    intervals: list[EnergyInterval]
    sourceNumbers: list[ZonalSourceNumber]
    sourceLabel: str | None
    sourceTotalHeader: str
    sourceShareHeader: str | None
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceFile: PublicFile | None = None


class ZonalEnergy(_PublicFiles):
    """Discover original generation/load MWh files with optional [files] parsing."""

    index_url = "https://www.ercot.com/mktinfo/data_agg"
    title_pattern = r"\d{4} (?:Generation|Load) MWh by CM ?Zone"

    def files(self) -> list[PublicFile]:
        return _year_files(self._http, self.index_url, self.title_pattern)

    def rows(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        where: Callable[[ZonalEnergyDay], bool] | None = None,
    ) -> Iterator[ZonalEnergyDay]:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for file in self.files():
            yield from self.read(
                self.download(file),
                filename=file.url.rsplit("/", 1)[-1],
                source_file=file,
                date_from=date_from,
                date_to=date_to,
                where=where,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        kind: _Kind | None = None,
        source_file: PublicFile | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        where: Callable[[ZonalEnergyDay], bool] | None = None,
    ) -> Iterator[ZonalEnergyDay]:
        """Read daily tables; bare unnamed files require an explicit kind.

        Duplicated generation 'raw data' sheets remain in the download. The
        published daily tables retain all their original intervals and totals.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, sheet, rows in _tables(data, filename):
            header = _header(rows[0])
            if not _date_column(header):
                continue
            found = True
            family = _kind(kind, member, source_file)
            for record in _days(rows, header, family, member, sheet, source_file):
                day = record.operatingDay
                if (date_from and day < date_from) or (date_to and day > date_to):
                    continue
                if where is None or where(record):
                    yield record
        if not found:
            raise ValueError("Download contains no zonal energy daily tables")

    def totals(
        self, *, where: Callable[[ZonalEnergyTotal], bool] | None = None
    ) -> Iterator[ZonalEnergyTotal]:
        for file in self.files():
            yield from self.read_totals(
                self.download(file),
                filename=file.url.rsplit("/", 1)[-1],
                source_file=file,
                where=where,
            )

    def read_totals(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        kind: _Kind | None = None,
        source_file: PublicFile | None = None,
        where: Callable[[ZonalEnergyTotal], bool] | None = None,
    ) -> Iterator[ZonalEnergyTotal]:
        """Read cached summary and detail totals, preserving their differences."""
        found = False
        for member, sheet, rows in _tables(data, filename):
            family = _kind(kind, member, source_file)
            for record in _totals(rows, family, member, sheet, source_file):
                found = True
                if where is None or where(record):
                    yield record
        if not found:
            raise ValueError("Download contains no zonal energy totals")


def _tables(
    data: bytes, filename: str
) -> Iterator[tuple[str, str, list[tuple[object, ...]]]]:
    for member, content in _workbooks(data):
        member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
        for sheet, values in _zonal_sheets(content):
            if sheet.lower() == "raw data":
                continue
            rows = list(values)
            if rows:
                yield member, sheet, rows


def _zonal_sheets(data: bytes) -> Iterator[tuple[str, Iterator[tuple[object, ...]]]]:
    if not data.startswith(b"\xd0\xcf\x11\xe0"):
        yield from _sheets(data, date_columns=(), preserve_types=True)
        return
    try:
        import xlrd
    except ImportError as error:
        raise ImportError(
            "Install tinyercot[files] to read zonal energy workbooks"
        ) from error
    with xlrd.open_workbook(file_contents=data) as book:
        for sheet in book.sheets():
            rows: list[list[object]] = [
                list(sheet.row_values(i)) for i in range(sheet.nrows)
            ]
            if not rows:
                continue
            for j, cell in enumerate(sheet.row(0)):
                if cell.ctype == xlrd.XL_CELL_DATE:
                    rows[0][j] = xlrd.xldate_as_datetime(
                        float(cell.value), book.datemode
                    )
            header = _header(tuple(rows[0]))
            date_name = _date_column(header)
            if date_name:
                day = header.index(date_name)
                _, end = _layout(header)
                for i, row in enumerate(rows[1:], 1):
                    # Some source energy cells are accidentally date-formatted.
                    # Decode dates only in the operating-date and trailing metadata.
                    for j in [day, *range(end, len(row))]:
                        if sheet.cell_type(i, j) == xlrd.XL_CELL_DATE:
                            row[j] = xlrd.xldate_as_datetime(
                                float(sheet.cell_value(i, j)), book.datemode
                            )
            yield sheet.name, iter(tuple(row) for row in rows)


def _kind(kind: _Kind | None, member: str, source: PublicFile | None) -> _Kind:
    if kind is not None:
        return kind
    label = (member + " " + (source.title if source else "")).lower()
    if "generation" in label:
        return "generation"
    if "load" in label:
        return "load"
    raise ValueError("Supply kind='generation' or 'load' for an unnamed zonal workbook")


def _header(row: tuple[object, ...]) -> list[str]:
    return [str(v).strip().upper() for v in row]


def _date_column(header: list[str]) -> str | None:
    return next((h for h in header if h in {"DATE", "TRADE DATE", "START TIME"}), None)


def _day(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    return date(*strptime(str(value), "%m/%d/%y")[:3])


def _zone(value: object) -> str | None:
    match = re.match(r"^([A-Z]\d{2})(?:\s|$)", str(value))
    return match[1] if match else None


def _layout(header: list[str]) -> tuple[int, int]:
    start = next(
        i for i, h in enumerate(header) if h.startswith(("INTERVAL ", "1899-", "1900-"))
    )
    end = header.index("TIMESTAMP") if "TIMESTAMP" in header else len(header)
    return start, end


def _intervals(
    row: tuple[object, ...],
    header: tuple[object, ...],
    start: int,
    end: int,
    *,
    unlabeled: bool = False,
) -> list[EnergyInterval]:
    return [
        EnergyInterval(
            interval=i,
            energyMWh=_number(row[j]),
            sourceLabel=None
            if unlabeled
            else str(header[j])
            if isinstance(header[j], str)
            else _interval_label(header[j]),
        )
        for i, j in enumerate(range(start, end), 1)
    ]


def _source_number(
    column: int, value: object, header: tuple[object, ...]
) -> ZonalSourceNumber:
    return ZonalSourceNumber.model_validate(
        {
            "column": column + 1,
            "value": _number(value),
            "sourceHeader": str(header[column])
            if header[column] not in (None, "")
            else None,
        }
    )


def _days(
    rows: list[tuple[object, ...]],
    header: list[str],
    kind: _Kind,
    member: str,
    sheet: str,
    source: PublicFile | None,
) -> Iterator[ZonalEnergyDay]:
    date_column = header.index(_date_column(header) or "")
    start, end = _layout(header)
    zone_column = next(
        (i for i, h in enumerate(header) if h.replace(" ", "") in {"ZONE", "CMZONE"}),
        None,
    )
    for line, row in enumerate(rows[1:], 2):
        day = _day(row[date_column])
        if day is None:
            continue

        def cell(name: str, values: tuple[object, ...] = row) -> object:
            return values[header.index(name)] if name in header else None

        numeric_tail = [
            j for j in range(end, len(row)) if isinstance(row[j], (int, float, Decimal))
        ]
        extended = (
            kind == "load"
            and len(numeric_tail) == 4
            and numeric_tail == list(range(end, end + 4))
        )
        numbers = (
            []
            if extended
            else [_source_number(j, row[j], rows[0]) for j in numeric_tail]
        )
        origin = cell("ORIGIN")
        if isinstance(origin, (int, float, Decimal)):
            numbers.insert(0, _source_number(header.index("ORIGIN"), origin, rows[0]))
        total = next(
            (row[i] for i, h in enumerate(header) if h in {"TOTAL", "TOTAL MWH"}), None
        )
        yield ZonalEnergyDay.model_validate(
            {
                "kind": kind,
                "operatingDay": day,
                "zone": row[zone_column] if zone_column is not None else sheet,
                "totalMWh": _number(total),
                "intervals": _intervals(
                    row,
                    rows[0],
                    start,
                    end + 4 if extended else end,
                    unlabeled=extended,
                ),
                "recorder": cell("RECORDER") or cell("CUTNAME"),
                "channel": cell("CHANNEL"),
                "origin": origin if isinstance(origin, str) and origin else None,
                "sourceTimestamp": next(
                    (v for v in row[end:] if isinstance(v, datetime)), None
                ),
                "sourceNumbers": numbers,
                "sourceMember": member,
                "sourceSheet": sheet,
                "sourceRow": line,
                "sourceFile": source,
            }
        )


def _totals(
    rows: list[tuple[object, ...]],
    kind: _Kind,
    member: str,
    sheet: str,
    source: PublicFile | None,
) -> Iterator[ZonalEnergyTotal]:
    first = next(
        (i for i, row in enumerate(rows) if any(v not in (None, "") for v in row)), None
    )
    if first is None:
        return
    raw_header = rows[first]
    header = _header(raw_header)
    date_name = _date_column(header)
    summary = date_name is None and len(header) == 3 and "%" in header[2]
    if not summary and date_name is None:
        return
    notes = [
        str(row[0])
        for row in rows[first + 1 :]
        if isinstance(row[0], str) and row[0] and all(v in (None, "") for v in row[1:])
    ]
    start, end = (0, 0) if summary else _layout(header)
    year = re.search(r"\d{4}", member.rsplit("/", 1)[-1])
    for line, row in enumerate(rows[first + 1 :], first + 2):
        if not any(isinstance(v, (int, float, Decimal)) for v in row):
            continue
        if date_name and _day(row[header.index(date_name)]) is not None:
            continue
        column = 1 if summary else start - 1
        label = next((v for v in row[:column] if isinstance(v, str) and v), None)
        known_total = summary or header[column] in {"TOTAL", "TOTAL MWH"}
        yield ZonalEnergyTotal.model_validate(
            {
                "kind": kind,
                "year": int(year[0]) if year else None,
                "scope": "summary" if summary else "detail_total",
                "zone": _zone(label) or _zone(sheet),
                "totalMWh": _number(row[column]) if known_total else None,
                "share": _number(row[2]) if summary else None,
                "intervals": _intervals(row, raw_header, start, end)
                if not summary and any(v not in (None, "") for v in row[start:end])
                else [],
                "sourceNumbers": [_source_number(column, row[column], raw_header)]
                if not known_total and row[column] not in (None, "")
                else [],
                "sourceLabel": label,
                "sourceTotalHeader": str(raw_header[column]),
                "sourceShareHeader": str(raw_header[2]) if summary else None,
                "sourceNotes": notes,
                "sourceMember": member,
                "sourceSheet": sheet,
                "sourceRow": line,
                "sourceFile": source,
            }
        )
