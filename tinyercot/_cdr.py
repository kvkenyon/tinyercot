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
    errors = {"#REF!", "#N/A", "#DIV/0!", "#VALUE!", "#NAME?", "#NUM!", "#NULL!"}
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
            isinstance(row[c], (int, float)) or row[c] in errors for c in columns
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
                value=None if row[c] in errors else _number(row[c]),
                sourceError=str(row[c]) if row[c] in errors else None,
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
