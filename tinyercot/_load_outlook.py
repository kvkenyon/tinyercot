"""Historical load summaries and outlook tables bundled with hourly load files."""

from __future__ import annotations

import re
from collections.abc import Iterator
from decimal import Decimal
from struct import unpack_from
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number

OUTLOOK_FILES = {
    "97frc714.zip",
    "ferc714.zip",
    "1999ferc714.zip",
    "2000ferc714.zip",
    "erceei97.xls",
}
_FORECAST_TEXT = {
    "ERCOTERYPROJ.TXT": ("energy", None),
    "ERCOTSUMDEM.TXT": ("peak_demand", "summer"),
    "ERCOTWINDEM.TXT": ("peak_demand", "winter"),
}


class LoadOutlook(BaseModel):
    """A source-labelled actual, reporting-year or projected quantity.

    Year bounds refer to the printed target period, not a publication date.
    Winter spans stay explicit; a single printed year does not gain an end year.
    Unknown units and unlabelled measures are preserved without inference.
    """

    model_config = ConfigDict(extra="forbid")
    entity: str
    controlArea: str | None = None
    reportingYear: int | None = None
    region: str | None = None
    countryCode: str | None = None
    year: int
    endYear: int | None = None
    month: int | None = None
    periodLabel: str
    measure: Literal["peak_demand", "energy", "net_energy", "unlabelled"]
    season: Literal["summer", "winter"] | None = None
    status: Literal["actual", "projected", "reporting_year", "next_year", "unspecified"]
    value: Decimal | None
    unit: Literal["MW", "MWh", "GWh"] | None
    sourceMember: str
    sourceSheet: str | None = None
    sourceLabel: str


def read_outlook(data: bytes, *, filename: str = "download") -> Iterator[LoadOutlook]:
    """Read saved ZIP/XLS/text outlook files; optional files extra reads OLE files."""
    from ._history import _archive_files

    members = (
        _archive_files(data, "*")
        if data.startswith(b"PK")
        else iter([(filename, data)])
    )
    found = False
    for name, content in members:
        base = name.rsplit("/", 1)[-1].upper()
        try:
            if re.fullmatch(r"[A-Z]+FORE\.96", base):
                text = (
                    _word95(content)
                    if content.startswith(b"\xd0\xcf")
                    else content.decode("ascii")
                )
                yield from _eia(text, name)
            elif base in _FORECAST_TEXT:
                yield from _matrix(content.decode("ascii"), name)
            elif content.startswith(b"\xd0\xcf"):
                yield from _xls(content, name)
            elif base.endswith("LD.EEI") or base in {
                "ERCEEI95.TXT",
                "ERCEEI97.TXT",
                "96LOAD.TXT",
                "ERCOT99HRLD.TXT",
                "ERCOT00HRLD.TXT",
            }:
                continue
            else:
                raise ValueError("Unsupported load outlook file")
            found = True
        except (ValueError, TypeError) as error:
            raise ValueError(f"{name}: {error}") from error
    if not found:
        raise ValueError("Download contains no load outlook tables")


def _word95(data: bytes) -> str:
    # TNPFORE.96 is a simple Word 95 document, not an XLS or ASCII file.
    try:
        from xlrd.compdoc import CompDoc
    except ImportError as error:
        raise ImportError(
            "Install tinyercot[files] to read the Word 95 outlook"
        ) from error
    stream = CompDoc(data).get_named_stream("WordDocument")
    if (
        stream is None
        or len(stream) < 32
        or unpack_from("<HH", stream) != (0xA5DC, 104)
    ):
        raise ValueError("Unsupported Word outlook format")
    if unpack_from("<H", stream, 10)[0] & 0x0104:
        raise ValueError("Complex or encrypted Word outlooks are unsupported")
    start, end = unpack_from("<II", stream, 24)
    if not 32 <= start <= end <= len(stream):
        raise ValueError("Invalid Word outlook text range")
    return stream[start:end].decode("cp1252")


def _period(label: str) -> tuple[int, int | None]:
    match = re.fullmatch(r"(\d{4})(?:/(\d{2}))?", label)
    if not match:
        raise ValueError(f"Unsupported target period: {label}")
    year = int(match[1])
    end = (year // 100 * 100 + int(match[2])) if match[2] else None
    if end is not None and end < year:
        end += 100
    return year, end


def _cells(line: str) -> list[str]:
    return [part.strip().strip('"') for part in line.split("\t")]


def _eia(text: str, filename: str) -> Iterator[LoadOutlook]:
    rows = [_cells(line) for line in text.splitlines()]
    metadata = next(
        (row for row in rows if re.fullmatch(r"\d{4}", row[0]) and len(row) > 3), None
    )
    reporting_year = int(metadata[0]) if metadata else None
    entity = (
        (metadata[3] or metadata[1])
        if metadata
        else filename.rsplit("/", 1)[-1].split("FORE.")[0]
    )
    periods: list[str] = []
    monthly_year: int | None = None
    monthly_status = "unspecified"
    count = 0
    for i, cells in enumerate(rows):
        label = cells[0]
        tail = cells[5:]
        nonempty = [value for value in tail if value]
        if (
            nonempty
            and all(re.fullmatch(r"\d{4}(?:/\d{2})?", v) for v in nonempty)
            and (not label or label == "10 Year Projection")
        ):
            periods = nonempty
            monthly_year = None
            continue
        if label in {"Actual Data:", "Reporting Year:", "Next Year:"}:
            monthly_year = int(cells[3])
            monthly_status = {
                "Actual Data:": "actual",
                "Reporting Year:": "reporting_year",
                "Next Year:": "next_year",
            }[label]
            if nonempty != [
                "Jan.",
                "Feb.",
                "March",
                "April",
                "May",
                "June",
                "July",
                "Aug.",
                "Sept.",
                "Oct.",
                "Nov.",
                "Dec.",
            ]:
                raise ValueError("Unsupported monthly headers")
            periods = [str(monthly_year)] * 12
            continue
        metric = re.fullmatch(
            r"0([1-9]) (Peak Hour Demand - MW(?: - (Summer|Winter)\(3,4\))?|Net Energy - G[wW][hH](?:\(5\))?)",
            label,
        )
        unlabelled = (
            label == "Actual Previous Year and"
            and nonempty
            and re.fullmatch(r"[\d.]+", nonempty[0])
        )
        if not metric and not unlabelled:
            if re.match(r"\d{2} ", label):
                raise ValueError(f"Unsupported EIA measure: {label}")
            continue
        if unlabelled:
            periods = [v for v in rows[i + 1][5:] if v]
            monthly_year = None
        if not periods:
            raise ValueError("Missing target periods")
        if any(tail[len(periods) :]):
            raise ValueError("More values than target periods")
        tail += [""] * (len(periods) - len(tail))
        for j, (period, value) in enumerate(
            zip(periods, tail[: len(periods)], strict=True)
        ):
            year, end = _period(period)
            row: dict[str, object] = {
                "entity": entity,
                "reportingYear": reporting_year,
                "region": metadata[1] or None if metadata else None,
                "countryCode": metadata[2] or None if metadata else None,
                "year": year,
                "endYear": end,
                "month": j + 1 if monthly_year else None,
                "periodLabel": f"{year}-{j + 1:02d}" if monthly_year else period,
                "measure": "unlabelled"
                if unlabelled
                else "peak_demand"
                if metric and metric[2].startswith("Peak")
                else "net_energy",
                "season": metric[3].lower() if metric and metric[3] else None,
                "status": "unspecified"
                if unlabelled
                else monthly_status
                if monthly_year
                else "actual"
                if j == 0
                else "projected",
                "value": _number(value),
                "unit": None
                if unlabelled
                else "MW"
                if metric and metric[2].startswith("Peak")
                else "GWh",
                "sourceMember": filename,
                "sourceLabel": label,
            }
            yield LoadOutlook.model_validate(row)
            count += 1
    if not count:
        raise ValueError("Missing EIA outlook tables")


def _matrix(text: str, filename: str) -> Iterator[LoadOutlook]:
    measure, season = _FORECAST_TEXT[filename.rsplit("/", 1)[-1].upper()]
    years: list[int] = []
    title = text.splitlines()[0].strip()
    for line in text.splitlines()[1:]:
        cells = line.split()
        if not cells:
            continue
        if all(re.fullmatch(r"\d{4}", cell) for cell in cells) and len(cells) > 1:
            years = [int(cell) for cell in cells]
            continue
        if not years:
            continue
        entity = " ".join(cells[: -len(years)])
        if (
            not re.fullmatch(r"[A-Z]+(?: Total)?", entity)
            or len(cells) < len(years) + 1
        ):
            raise ValueError("Missing outlook entity or values")
        for year, value in zip(years, cells[-len(years) :], strict=True):
            yield LoadOutlook.model_validate(
                {
                    "entity": entity,
                    "year": year,
                    "periodLabel": str(year),
                    "measure": measure,
                    "season": season,
                    "status": "projected",
                    "value": _number(value),
                    "unit": None,
                    "sourceMember": filename,
                    "sourceLabel": title,
                }
            )
    if not years:
        raise ValueError("Missing outlook year header")


def _xls(data: bytes, filename: str) -> Iterator[LoadOutlook]:
    try:
        import xlrd
    except ImportError as error:
        raise ImportError(
            "Install tinyercot[files] to read load outlook workbooks"
        ) from error
    contracts = {
        "ANNUAL ENERGY PROJECTION MWH": ("energy", None, "MWh", "MWH"),
        "SUMMER PEAK DEAMND MW": ("peak_demand", "summer", "MW", "Summer MW"),
        "WINTER PEAK DEMAND MW": ("peak_demand", "winter", "MW", "Winter MW"),
    }
    found = False
    with xlrd.open_workbook(file_contents=data) as book:
        for sheet in book.sheets():
            if sheet.name in contracts:
                measure, season, unit, label = contracts[sheet.name]
                if sheet.cell_value(0, 0) != label or sheet.cell_value(2, 1) != "CA":
                    raise ValueError("Unsupported outlook worksheet header")
                years = [int(sheet.cell_value(2, j)) for j in range(2, sheet.ncols)]
                found = True
                for i in range(3, sheet.nrows):
                    entity = str(sheet.cell_value(i, 0))
                    if not entity:
                        if any(v != "" for v in sheet.row_values(i)):
                            raise ValueError("Outlook row has values without an entity")
                        continue
                    for j, year in enumerate(years, 2):
                        yield LoadOutlook.model_validate(
                            {
                                "entity": entity,
                                "controlArea": sheet.cell_value(i, 1) or None,
                                "year": year,
                                "periodLabel": str(year),
                                "measure": measure,
                                "season": season,
                                "status": "projected",
                                "value": _number(sheet.cell_value(i, j)),
                                "unit": unit,
                                "sourceMember": filename,
                                "sourceSheet": sheet.name,
                                "sourceLabel": label,
                            }
                        )
            elif sheet.cell_value(0, 0) == "ERCOT - Composite Load":
                found = True
                year = int(sheet.cell_value(1, 0))
                for i, label, measure, unit in [
                    (0, "Peak =", "peak_demand", "MW"),
                    (1, "Energy", "energy", "GWh"),
                ]:
                    if (
                        sheet.cell_value(i, 12) != label
                        or str(sheet.cell_value(i, 14)).lower() != unit.lower()
                    ):
                        raise ValueError("Unsupported composite summary labels")
                    yield LoadOutlook.model_validate(
                        {
                            "entity": "ERCOT",
                            "year": year,
                            "periodLabel": str(year),
                            "measure": measure,
                            "status": "actual",
                            "value": _number(sheet.cell_value(i, 13)),
                            "unit": unit,
                            "sourceMember": filename,
                            "sourceSheet": sheet.name,
                            "sourceLabel": label,
                        }
                    )
            elif sheet.name != "1998 HOURLY LOAD KW":
                raise ValueError(f"Unsupported outlook worksheet: {sheet.name}")
    if not found:
        raise ValueError("Workbook contains no load outlook tables")
