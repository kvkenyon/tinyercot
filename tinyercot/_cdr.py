"""Historical capacity, demand and reserves forecasts from public workbooks."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Literal
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import PublicFile, _ResourceFiles

Season = Literal["summer", "winter", "spring", "fall"]
_ERRORS = {"#REF!", "#N/A", "#DIV/0!", "#VALUE!", "#NAME?", "#NUM!", "#NULL!"}


class CdrSummaryValue(BaseModel):
    """One published forecast value, without recalculation or sign changes.

    Labels retain distinctions between gross/firm load and resource scenarios.
    Fractions are stored as published, not multiplied by 100. A difference
    column compares peak-load and peak-net-load results; it has no clock hour.
    reportingGroup retains TDSP or other block labels, including system totals.
    Installed-capacity columns have no annual period; sourceColumnLabel retains
    qualifications such as cumulative ratings by a future year.
    """

    model_config = ConfigDict(extra="forbid")
    season: Season
    period: str | None
    kind: Literal["forecast", "installed_capacity"]
    metric: str
    reportingGroup: str | None
    loadServingEntity: str | None
    controlArea: str | None
    reserveBasis: str | None
    hourBasis: Literal["peak_load", "peak_net_load", "difference"] | None
    hour: int | None
    value: Decimal | None
    sourceError: str | None
    unit: Literal["MW", "fraction"] | None
    sourceSheet: str
    sourceRow: int
    sourceColumn: int
    sourceColumnLabel: str | None


class CdrNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceSheet: str
    sourceRow: int
    sourceColumn: int
    text: str


class CdrCountyValue(BaseModel):
    """A county/period source cell. None county preserves an unlabelled row."""

    model_config = ConfigDict(extra="forbid")
    county: str | None
    period: str
    valueMW: Decimal | None
    sourceError: str | None
    sourceRow: int
    sourceColumn: int


class CdrCountyTable(BaseModel):
    """A historical planning table, not measured county demand or energy flows.

    generation_minus_load is ERCOT's illustrative balance: negative values
    indicate import needs; positive values indicate export potential. Capacity
    assumptions and load bases change by vintage and are retained in notes.
    County spellings/case and unlabelled numeric rows are not normalized.
    """

    model_config = ConfigDict(extra="forbid")
    sourceFile: PublicFile | None
    sourceMember: str
    sourceSheet: str
    season: Season
    metric: Literal[
        "load", "coincident_demand", "generation_capacity", "generation_minus_load"
    ]
    loadBasis: Literal["coincident", "noncoincident"] | None
    values: list[CdrCountyValue]
    notes: list[CdrNote]


class CdrSummary(BaseModel):
    """One report's summary tables and original qualifications.

    Different publications may forecast the same period. URL dates can reflect
    website migrations, so this reader does not infer report or issue dates.
    Summary tables do not cover the workbook's unit/county/ELCC detail tables.
    """

    model_config = ConfigDict(extra="forbid")
    sourceFile: PublicFile | None
    sourceMember: str
    values: list[CdrSummaryValue]
    notes: list[CdrNote]


def _period(value: object) -> str | None:
    if (
        isinstance(value, (int, float))
        and int(value) == value
        and 1990 <= value <= 2100
    ):
        return str(int(value))
    if isinstance(value, str) and re.fullmatch(r"20\d\d/(?:20)?\d\d", value.strip()):
        return value.strip()
    return None


def _season(text: str) -> Season:
    for season in ("summer", "winter", "spring", "fall"):
        if season in text.lower():
            return season
    raise ValueError(f"No CDR season in {text!r}")


def _values(sheet: str, rows: list[tuple[object, ...]]) -> Iterator[CdrSummaryValue]:
    width = max(map(len, rows), default=0)
    rows = [tuple(row) + (None,) * (width - len(row)) for row in rows]
    modern = any("Peak Load Hour:" in row for row in rows[:6])
    header = next(
        i
        for i, row in enumerate(rows[:8])
        if sum(_period(v) is not None for v in row) >= 3
    )
    columns = {c: p for c, v in enumerate(rows[header]) if (p := _period(v))}
    start = min(columns)
    seasons = (
        {c: _season(sheet if sheet != "Summary" else str(rows[1])) for c in columns}
        if sheet != "Seasonal Summary"
        else {}
    )
    if modern:
        period = ""
        season = _season(sheet) if sheet != "Seasonal Summary" else "summer"
        for c, label in enumerate(rows[header + 1]):
            if c < start or not isinstance(label, str) or not label.strip():
                continue
            period = _period(rows[header][c]) or period
            if sheet == "Seasonal Summary" and rows[header - 1][c]:
                season = _season(str(rows[header - 1][c]))
            columns[c] = period
            seasons[c] = season
    entity_table = any("LSE" in row for row in rows[:4])
    group_table = any("TDSP" in row for row in rows[:4])
    ratings = {
        c: v
        for row in rows
        for c, v in enumerate(row)
        if isinstance(v, str) and "Installed Capacity Ratings" in v
    }
    group: str | None = None
    reserve_basis: str | None = None
    for r, row in enumerate(rows[header:], header):
        left = [
            (c, str(v))
            for c, v in enumerate(row[:start])
            if isinstance(v, str) and v.strip()
        ]
        if not left:
            continue
        label = left[-1][1]
        if all(_period(row[c]) == p for c, p in columns.items()):
            if group_table:
                group = str(row[0])
                reserve_basis = None
            continue
        if not any(
            isinstance(row[c], (int, float)) or row[c] in _ERRORS for c in columns
        ):
            continue
        if modern and r < header + 4:
            continue
        if label.strip().startswith("Reserve Based on"):
            reserve_basis = label.strip()
        unit: Literal["MW", "fraction"] | None = (
            "fraction" if "margin" in label.lower() else "MW"
        )
        output_columns: list[tuple[int, str | None]] = list(columns.items())
        output_columns.extend(
            (c, None) for c in sorted(ratings) if isinstance(row[c], (int, float))
        )
        for c, value_period in output_columns:
            basis: Literal["peak_load", "peak_net_load", "difference"] | None = None
            hour = None
            if modern:
                text = str(rows[header + 1][c]).strip()
                if text.startswith("Difference"):
                    basis = "difference"
                else:
                    basis = "peak_net_load" if "Net Load" in text else "peak_load"
                    hour = int(str(rows[header + 2][c]))
            yield CdrSummaryValue(
                season=seasons[c] if value_period is not None else _season(sheet),
                kind="forecast" if value_period is not None else "installed_capacity",
                period=value_period,
                metric=label,
                reportingGroup=group,
                loadServingEntity=str(row[0]) if entity_table else None,
                controlArea=str(row[1]) if entity_table else None,
                reserveBasis=reserve_basis,
                hourBasis=basis,
                hour=hour,
                value=None if row[c] in _ERRORS else _number(row[c]),
                sourceError=str(row[c]) if row[c] in _ERRORS else None,
                unit=unit,
                sourceSheet=sheet,
                sourceRow=r + 1,
                sourceColumn=c + 1,
                sourceColumnLabel=ratings.get(c),
            )


class CdrHistory(_ResourceFiles):
    """Public historical CDR reports; Excel reading needs tinyercot[files]."""

    title_pattern = r"(?i)Capacity.*Demand.*Reserve.*"

    def summaries(
        self, *, where: Callable[[CdrSummary], bool] | None = None
    ) -> Iterator[CdrSummary]:
        for file in self.files():
            yield from self.read_summaries(
                self.download(file), source_file=file, where=where
            )

    def read_summaries(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[CdrSummary], bool] | None = None,
    ) -> Iterator[CdrSummary]:
        found = False
        for member, content in _workbooks(data):
            if member in {"workbook.xls", "workbook.xlsx"}:
                member = (
                    unquote(source_file.url.rsplit("/", 1)[-1])
                    if source_file
                    else filename
                )
            document = CdrSummary(
                sourceFile=source_file, sourceMember=member, values=[], notes=[]
            )
            for sheet, source in _sheets(content, date_columns=(), preserve_types=True):
                summary = sheet.replace(" ", "").lower() in {
                    "summary",
                    "summersummary",
                    "wintersummary",
                    "seasonalsummary",
                }
                if not summary and sheet not in {
                    "TitlePage",
                    "Disclaimer",
                    "Definitions",
                    "Changes",
                }:
                    continue
                rows = list(source)
                if summary:
                    document.values.extend(_values(sheet, rows))
                for r, row in enumerate(rows, 1):
                    for c, value in enumerate(row, 1):
                        if isinstance(value, str) and value.strip():
                            document.notes.append(
                                CdrNote(
                                    sourceSheet=sheet,
                                    sourceRow=r,
                                    sourceColumn=c,
                                    text=value,
                                )
                            )
            if not document.values:
                raise ValueError(f"{member}: no CDR summary tables")
            found = True
            if where is None or where(document):
                yield document
        if not found:
            raise ValueError("Download contains no CDR workbooks")

    def county_tables(
        self, *, where: Callable[[CdrCountyTable], bool] | None = None
    ) -> Iterator[CdrCountyTable]:
        """Read county tables in all report vintages; reports without them yield none."""
        for file in self.files():
            yield from self.read_county_tables(
                self.download(file), source_file=file, where=where
            )

    def read_county_tables(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[CdrCountyTable], bool] | None = None,
    ) -> Iterator[CdrCountyTable]:
        """Read source county tables in saved workbooks/ZIPs without joining vintages."""
        metrics: dict[
            str,
            Literal[
                "load",
                "coincident_demand",
                "generation_capacity",
                "generation_minus_load",
            ],
        ] = {
            "LoadbyCounty": "load",
            "CoincidentDemandbyCounty": "coincident_demand",
            "GenerationbyCounty": "generation_capacity",
            "Import-ExportbyCounty": "generation_minus_load",
        }
        for member, content in _workbooks(data):
            if member in {"workbook.xls", "workbook.xlsx"}:
                member = (
                    unquote(source_file.url.rsplit("/", 1)[-1])
                    if source_file
                    else filename
                )
            for sheet, source in _sheets(content, date_columns=(), preserve_types=True):
                suffix = re.sub(r"^(Summer|Winter)", "", sheet)
                if suffix not in metrics:
                    continue
                rows = list(source)
                header = next(i for i, row in enumerate(rows) if "County" in row)
                county_column = rows[header].index("County")
                periods = {
                    c: p for c, v in enumerate(rows[header]) if (p := _period(v))
                }
                if not periods:
                    raise ValueError(f"{member}/{sheet}: no county forecast periods")
                notes = [
                    CdrNote(
                        sourceSheet=sheet, sourceRow=r + 1, sourceColumn=c + 1, text=v
                    )
                    for r, row in enumerate(rows[:header])
                    for c, v in enumerate(row)
                    if isinstance(v, str) and v.strip()
                ]
                text = " ".join(note.text for note in notes).lower()
                basis: Literal["coincident", "noncoincident"] | None = None
                if suffix == "CoincidentDemandbyCounty":
                    basis = "coincident"
                elif suffix in {"LoadbyCounty", "Import-ExportbyCounty"}:
                    if "non-coincident" in text:
                        basis = "noncoincident"
                    elif "coincident" in text:
                        basis = "coincident"
                table = CdrCountyTable(
                    sourceFile=source_file,
                    sourceMember=member,
                    sourceSheet=sheet,
                    season=_season(sheet),
                    metric=metrics[suffix],
                    loadBasis=basis,
                    notes=notes,
                    values=[],
                )
                for r, row in enumerate(rows[header + 1 :], header + 2):
                    if not any(v not in (None, "") for v in row):
                        continue
                    county = row[county_column]
                    for c, period in periods.items():
                        value = row[c] if c < len(row) else None
                        table.values.append(
                            CdrCountyValue(
                                county=str(county)
                                if county not in (None, "")
                                else None,
                                period=period,
                                valueMW=None if value in _ERRORS else _number(value),
                                sourceError=str(value) if value in _ERRORS else None,
                                sourceRow=r,
                                sourceColumn=c + 1,
                            )
                        )
                if where is None or where(table):
                    yield table
