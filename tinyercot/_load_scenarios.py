"""Regional hourly load predictions under published historical weather years."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from typing import Literal

from ._hourly_forecasts import _ZONES, _column, _forecast_clock
from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._load_forecasts import _ForecastRow, _ForecastTable
from ._weather import WeatherZone


class HourlyLoadScenario(_ForecastRow):
    """One forecast hour with separate weather-year predictions and adjustments."""

    forecastDate: date
    hour: int
    sourceDate: date | None
    weatherZone: WeatherZone
    sourceWeatherZone: str
    sourceWeatherZoneColumn: str | None
    weatherYearPredictions: dict[int, Decimal | None]
    electricVehicles: Decimal | None = None
    rooftopPV: Decimal | None = None
    largeFlexibleLoad: Decimal | None = None
    contractedLoad: Decimal | None = None
    officerLetterLoad: Decimal | None = None
    unit: Literal["MW"] | None = None
    sourceLabels: dict[str, str]
    sourceMarkers: dict[str, str]


def _scenario_value(
    value: object, label: str, markers: dict[str, str]
) -> Decimal | None:
    try:
        return _number(value)
    except ValueError:
        if not isinstance(value, str):
            raise
        markers[label] = value
        return None


class HourlyLoadScenarios(_ForecastTable[HourlyLoadScenario]):
    title_pattern = r"Coast|East|Far West|North Central|North|South Central|South|West"
    extensions = (".xlsx",)

    def _read(self, data: bytes, filename: str) -> Iterator[HourlyLoadScenario]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for name, source in _sheets(content, date_columns=()):
                rows = enumerate(source, 1)
                _, raw_header = next(rows)
                header_values = list(raw_header)
                while header_values and header_values[-1] in (None, ""):
                    header_values.pop()
                header = [str(v) for v in header_values]
                clock_columns = {
                    label.lower(): i
                    for i, label in enumerate(header)
                    if label.lower() in {"year", "month", "day", "hour", "date"}
                }
                if not {"year", "month", "day", "hour"} <= clock_columns.keys():
                    raise ValueError(f"{member}/{name}: missing forecast clock columns")
                predictions = {
                    i: int(match[1])
                    for i, label in enumerate(header)
                    if (match := re.fullmatch(r"Pred_(\d{4})", label))
                }
                if not predictions or len(set(predictions.values())) != len(
                    predictions
                ):
                    raise ValueError(
                        f"{member}/{name}: missing or duplicate weather-year columns"
                    )
                zone_column = header.index("wzone") if "wzone" in header else None
                components = [
                    (i, *_column(label))
                    for i, label in enumerate(header)
                    if i not in clock_columns.values()
                    and i not in predictions
                    and i != zone_column
                ]
                labels = {
                    f"weatherYearPredictions.{year}": header[i]
                    for i, year in predictions.items()
                }
                labels.update({field: header[i] for i, field, _ in components})
                if len(labels) != len(predictions) + len(components):
                    raise ValueError(f"{member}/{name}: duplicate load components")
                for line, values in rows:
                    if not any(v not in (None, "") for v in values):
                        continue
                    if any(v not in (None, "") for v in values[len(header) :]):
                        raise ValueError(f"{member}/{name}: unlabelled forecast values")
                    markers: dict[str, str] = {}

                    source_zone = (
                        str(values[zone_column]) if zone_column is not None else name
                    )
                    zone = _ZONES[source_zone.lower()]
                    if any(
                        component_zone != zone for _, _, component_zone in components
                    ):
                        raise ValueError(
                            f"{member}/{name}: load component and source weather zone disagree"
                        )
                    calendar = [
                        values[clock_columns[label]]
                        for label in ("year", "month", "day", "hour")
                    ]
                    if "date" in clock_columns:
                        calendar.insert(0, values[clock_columns["date"]])
                    day, hour, source_date = _forecast_clock(
                        calendar, int("date" in clock_columns)
                    )
                    found = True
                    yield HourlyLoadScenario.model_validate(
                        dict(
                            forecastDate=day,
                            hour=hour,
                            sourceDate=source_date,
                            weatherZone=source_zone.upper(),
                            sourceWeatherZone=source_zone,
                            sourceWeatherZoneColumn=header[zone_column]
                            if zone_column is not None
                            else None,
                            weatherYearPredictions={
                                year: _scenario_value(values[i], header[i], markers)
                                for i, year in predictions.items()
                            },
                            sourceLabels=labels,
                            sourceMarkers=markers,
                            sourceMember=member,
                            sourceSheet=name,
                            sourceRow=line,
                            **{
                                field: _scenario_value(values[i], header[i], markers)
                                for i, field, _ in components
                            },
                        )
                    )
        if not found:
            raise ValueError("No hourly weather-year load scenarios found")
