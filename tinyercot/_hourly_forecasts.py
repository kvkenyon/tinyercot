"""Hourly long-term load forecasts, preserving published components and hours."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _workbooks
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
    "ercot": "total",
    "total": "total",
}
_COMPONENTS = {
    "": "forecast",
    "gross": "gross",
    "base": "baseLoad",
    "baseeconomic": "baseLoad",
    "ev": "electricVehicles",
    "pv": "rooftopPV",
    "pvpred": "rooftopPV",
    "lflforecast": "largeFlexibleLoad",
    "lfl15%": "largeFlexibleLoad",
    "contracts": "contractedLoad",
    "officerletters": "officerLetterLoad",
    "contractedlfl": "contractedFlexibleLoad",
    "officerletterslfl": "officerLetterFlexibleLoad",
    "net": "net",
    "net15": "net",
}


class WeatherZoneForecastValues(BaseModel):
    """Published regional values; absent zones and totals stay None."""

    model_config = ConfigDict(extra="forbid")
    coast: Decimal | None = None
    east: Decimal | None = None
    farWest: Decimal | None = None
    northCentral: Decimal | None = None
    north: Decimal | None = None
    southCentral: Decimal | None = None
    south: Decimal | None = None
    west: Decimal | None = None
    total: Decimal | None = None


class HourlyLoadForecast(_ForecastRow):
    """A source hour, without timezone, DST or hour-ending inference."""

    forecastDate: date
    hour: int
    sourceDate: date | None
    unit: Literal["MW"] | None
    scenario: Literal["tsp_provided", "ercot_adjusted"] | None = None
    forecast: WeatherZoneForecastValues | None = None
    gross: WeatherZoneForecastValues | None = None
    baseLoad: WeatherZoneForecastValues | None = None
    electricVehicles: WeatherZoneForecastValues | None = None
    rooftopPV: WeatherZoneForecastValues | None = None
    largeFlexibleLoad: WeatherZoneForecastValues | None = None
    contractedLoad: WeatherZoneForecastValues | None = None
    officerLetterLoad: WeatherZoneForecastValues | None = None
    contractedFlexibleLoad: WeatherZoneForecastValues | None = None
    officerLetterFlexibleLoad: WeatherZoneForecastValues | None = None
    net: WeatherZoneForecastValues | None = None
    sourceLabels: dict[str, str]
    sourceNotes: list[str]


def _column(label: str) -> tuple[str, str]:
    key = re.sub(r"[_\s]", "", label.lower())
    for zone, field in _ZONES.items():
        if key.startswith(zone):
            component = key[len(zone) :]
        elif key.endswith(zone):
            component = key[: -len(zone)]
        else:
            continue
        if component in _COMPONENTS:
            return _COMPONENTS[component], field
    raise ValueError(f"Unknown hourly forecast column: {label!r}")


class HourlyLoadForecasts(_ForecastTable[HourlyLoadForecast]):
    title_pattern = r"\d{4} ERCOT Hourly Forecast|TSP Provided Hourly Forecast|ERCOT Adjusted Forecast"
    extensions = (".xlsx", ".xlsb")

    def rows(
        self, *, where: Callable[[HourlyLoadForecast], bool] | None = None
    ) -> Iterator[HourlyLoadForecast]:
        for row in super().rows():
            if row.sourceFile:
                if row.sourceFile.title == "TSP Provided Hourly Forecast":
                    row.scenario = "tsp_provided"
                elif row.sourceFile.title == "ERCOT Adjusted Forecast":
                    row.scenario = "ercot_adjusted"
            if where is None or where(row):
                yield row

    def _read(self, data: bytes, filename: str) -> Iterator[HourlyLoadForecast]:
        try:
            from python_calamine import CalamineWorkbook
        except ImportError as error:
            raise ImportError(
                "Install tinyercot[files] to read hourly forecast workbooks"
            ) from error
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            with CalamineWorkbook.from_filelike(BytesIO(content)) as book:
                notes = [
                    str(value)
                    for name in book.sheet_names
                    if name == "Description"
                    for cells in book.get_sheet_by_name(name).iter_rows()
                    for value in cells
                    if value != ""
                ]
                for name in book.sheet_names:
                    if name == "Description":
                        continue
                    sheet = book.get_sheet_by_name(name)
                    cells = enumerate(sheet.iter_rows(), 1)
                    preamble: list[tuple[int, list[object]]] = []
                    for line, raw in cells:
                        row = list[object](raw)
                        offset = 1 if row and str(row[0]).lower() == "date" else 0
                        if [str(v).lower() for v in row[offset : offset + 4]] == [
                            "year",
                            "month",
                            "day",
                            "hour",
                        ]:
                            break
                        preamble.append((line, row))
                    else:
                        continue
                    start = offset + 4
                    columns = [_column(str(label)) for label in row[start:]]
                    labels = {
                        f"{component}.{zone}": str(label)
                        for (component, zone), label in zip(
                            columns, row[start:], strict=True
                        )
                    }
                    if len(labels) != len(columns):
                        raise ValueError(f"{member}/{name}: duplicate forecast columns")
                    # The 2023 workbook explicitly merges MW over every value column.
                    unit: Literal["MW"] | None = None
                    for unit_line, unit_values in preamble:
                        if (
                            len(unit_values) > start
                            and unit_values[start] == "MW"
                            and ((unit_line - 1, start), (unit_line - 1, len(row) - 1))
                            in (sheet.merged_cell_ranges or [])
                        ):
                            unit = "MW"
                    for line, values in cells:
                        if not any(v != "" for v in values):
                            continue
                        components: dict[str, dict[str, Decimal | None]] = {}
                        for (component, zone), value in zip(
                            columns, values[start:], strict=True
                        ):
                            components.setdefault(component, {})[zone] = _number(value)
                        source_date = values[0] if offset else None
                        if isinstance(source_date, datetime):
                            source_date = source_date.date()
                        elif isinstance(source_date, str):
                            source_date = date.fromisoformat(source_date)
                        if source_date is not None and not isinstance(
                            source_date, date
                        ):
                            raise ValueError(
                                f"Unsupported source date: {source_date!r}"
                            )
                        found = True
                        yield HourlyLoadForecast.model_validate(
                            dict(
                                forecastDate=date(
                                    *(
                                        int(str(v).removesuffix(".0"))
                                        for v in values[offset : offset + 3]
                                    )
                                ),
                                hour=int(str(values[offset + 3]).removesuffix(".0")),
                                sourceDate=source_date,
                                unit=unit,
                                sourceLabels=labels,
                                sourceNotes=notes,
                                sourceMember=member,
                                sourceSheet=name,
                                sourceRow=line,
                                **{
                                    key: WeatherZoneForecastValues(**value)
                                    for key, value in components.items()
                                },
                            )
                        )
        if not found:
            raise ValueError("No hourly load forecast tables found")
