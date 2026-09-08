"""Public seasonal and weekly peak-demand tables by weather zone."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from time import strptime
from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._load_forecasts import _ForecastRow, _ForecastTable

_ZONES = {
    "coast": "coast",
    "east": "east",
    "fwest": "farWest",
    "ncent": "northCentral",
    "north": "north",
    "scent": "southCentral",
    "south": "south",
    "west": "west",
}


class WeatherZonePeakValues(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coast: Decimal | None
    east: Decimal | None
    farWest: Decimal | None
    northCentral: Decimal | None
    north: Decimal | None
    southCentral: Decimal | None
    south: Decimal | None
    west: Decimal | None
    total: Decimal | None


def _peaks(
    cells: tuple[object, ...], labels: tuple[object, ...]
) -> WeatherZonePeakValues:
    values = {
        _ZONES[str(label).lower()]: _number(v)
        for label, v in zip(labels[:8], cells[:8], strict=True)
    }
    return WeatherZonePeakValues(**values, total=_number(cells[8]))


class _ZonalPeakRow(_ForecastRow):
    kind: Literal["forecast", "historical"]
    peaks: WeatherZonePeakValues
    unit: Literal["MW"] | None
    percentile: int | None
    sourcePercentileLabel: str | None
    sourceTotalLabel: str


T = TypeVar("T", bound=_ZonalPeakRow)


class _ZonalPeakTable(_ForecastTable[T]):
    def rows(self, *, where: Callable[[T], bool] | None = None) -> Iterator[T]:
        for row in super().rows():
            if (
                row.kind == "forecast"
                and row.percentile is None
                and row.sourceFile
                and re.search(r"\b(?:90th|P90)\b", row.sourceFile.title, re.IGNORECASE)
            ):
                row.percentile = 90
                row.sourcePercentileLabel = row.sourceFile.title
            if where is None or where(row):
                yield row


class SeasonalPeakForecast(_ZonalPeakRow):
    """A forecast or historical section; winter periods retain both years."""

    year: int
    endYear: int | None
    season: Literal["summer", "winter"] | None
    demandBasis: Literal["gross", "net", "rooftop_pv", "unspecified"]
    coincident: bool | None
    scenario: Literal["tsp_provided", "ercot_adjusted"] | None
    sourcePeriod: str
    sourceTitle: str
    sourceColumn: int
    sourceNotes: list[str]


class SeasonalPeakForecasts(_ZonalPeakTable[SeasonalPeakForecast]):
    title_pattern = (
        r"Weather Zone Non-Coincident Peak Forecast\.?|"
        r"90th [Pp]ercentile Summer (?:Non-Coincident Peak by Weather Zone|NCP by weather zone)|"
        r"Summer and Winter Peaks|Winter Peak Loads"
    )

    def _read(self, data: bytes, filename: str) -> Iterator[SeasonalPeakForecast]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, iterator in _sheets(content, date_columns=()):
                rows = list(iterator)
                notes = [
                    v
                    for row in rows
                    for v in row
                    if isinstance(v, str) and v.startswith("This includes ")
                ]
                titles: dict[int, str] = {}
                blocks: list[tuple[int, tuple[object, ...]]] = []
                historical = False
                percentile_label: str | None = None
                for line, cells in enumerate(rows, 1):
                    if cells and str(cells[0]).startswith("This includes "):
                        continue
                    if cells and cells[0] == "Historical":
                        historical, percentile_label, blocks = True, None, []
                        continue
                    if cells and str(cells[0]).lower() == "90th percentile":
                        percentile_label = str(cells[0])
                        continue
                    new_titles = {
                        i: v
                        for i, v in enumerate(cells)
                        if isinstance(v, str)
                        and "peak" in v.lower()
                        and ("forecast" in v.lower() or "(MW)" in v)
                    }
                    if new_titles:
                        titles, blocks = new_titles, []
                        if any("Forecast" in title for title in titles.values()):
                            historical = False
                        continue
                    starts = [
                        i - 1
                        for i in range(1, max(1, len(cells) - 8))
                        if {str(v).lower() for v in cells[i : i + 8]} == set(_ZONES)
                    ]
                    if starts:
                        blocks = [(i, cells[i + 1 : i + 10]) for i in starts]
                        continue
                    for start, labels in blocks:
                        values = cells[start : start + 10]
                        if not any(v not in (None, "") for v in values):
                            continue
                        period = str(values[0]).removesuffix(".0")
                        match = re.fullmatch(r"(\d{4})(?:-(\d{4}))?", period)
                        if match is None or len(values) < 10:
                            raise ValueError(
                                f"{member}/{sheet}:{line}: invalid peak period or values"
                            )
                        title = titles[start]
                        lower = title.lower()
                        basis: Literal["gross", "net", "rooftop_pv", "unspecified"] = (
                            "unspecified"
                        )
                        if "rooftop pv" in lower:
                            basis = "rooftop_pv"
                        elif "gross" in lower:
                            basis = "gross"
                        elif "net" in lower:
                            basis = "net"
                        season: Literal["summer", "winter"] | None = None
                        if "summer" in lower:
                            season = "summer"
                        elif "winter" in lower:
                            season = "winter"
                        scenario: Literal["tsp_provided", "ercot_adjusted"] | None = (
                            None
                        )
                        if "TSP Provided" in title:
                            scenario = "tsp_provided"
                        elif "ERCOT Adjusted" in title:
                            scenario = "ercot_adjusted"
                        probability_label = (
                            title if "90th" in lower else percentile_label
                        )
                        found = True
                        yield SeasonalPeakForecast(
                            year=int(match[1]),
                            endYear=int(match[2]) if match[2] else None,
                            kind="historical" if historical else "forecast",
                            season=season,
                            demandBasis=basis,
                            scenario=scenario,
                            coincident=False
                            if re.search(r"non[ -]coincident", lower)
                            else True
                            if "coincident" in lower
                            else None,
                            peaks=_peaks(values[1:], labels),
                            unit="MW" if "(MW)" in title else None,
                            percentile=90 if probability_label else None,
                            sourcePercentileLabel=probability_label,
                            sourceTotalLabel=str(labels[8]),
                            sourcePeriod=period,
                            sourceTitle=title,
                            sourceColumn=start + 1,
                            sourceNotes=notes,
                            sourceMember=member,
                            sourceSheet=sheet,
                            sourceRow=line,
                        )
        if not found:
            raise ValueError("No seasonal peak-demand tables found")


class WeeklyPeakForecast(_ZonalPeakRow):
    beginDate: date
    endDate: date
    peakDate: date
    peakHour: int


def _day(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    return date(*strptime(str(value), "%d%b%Y")[:3])


class WeeklyPeakForecasts(_ZonalPeakTable[WeeklyPeakForecast]):
    title_pattern = r"\d{4} Weekly P90 Peaks"

    def _read(self, data: bytes, filename: str) -> Iterator[WeeklyPeakForecast]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                header = next(rows, ())
                if header[:4] != ("Begin_Date", "End_Date", "Peak_Date", "Peak_Hour"):
                    raise ValueError(
                        f"{member}/{sheet}: unsupported weekly peak header"
                    )
                for line, cells in enumerate(rows, 2):
                    if not any(v not in (None, "") for v in cells):
                        continue
                    found = True
                    yield WeeklyPeakForecast(
                        kind="forecast",
                        beginDate=_day(cells[0]),
                        endDate=_day(cells[1]),
                        peakDate=_day(cells[2]),
                        peakHour=int(str(cells[3]).removesuffix(".0")),
                        peaks=_peaks(cells[4:], header[4:]),
                        unit=None,
                        percentile=None,
                        sourcePercentileLabel=None,
                        sourceTotalLabel=str(header[12]),
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=line,
                    )
        if not found:
            raise ValueError("No weekly peak-demand tables found")
