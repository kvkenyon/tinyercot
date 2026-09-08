"""Winter hourly and peak load forecasts by transmission operator."""

import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from typing import Literal

from ._hourly_forecasts import _forecast_clock
from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._load_forecasts import _ForecastRow, _ForecastTable


class WinterLoadForecast(_ForecastRow):
    """System forecasts and operator allocations; operators exclude LL additions."""

    kind: Literal["hourly", "peak"]
    forecastDate: date
    hour: int
    sourceDate: date | None
    baseLoad: Decimal | None
    loadWithLargeLoads: Decimal | None
    largeLoadAdditions: Decimal | None
    transmissionOperators: dict[str, Decimal | None]
    percentile: int | None
    sourceNotes: list[str]


class WinterLoadForecasts(_ForecastTable[WinterLoadForecast]):
    title_pattern = r"ERCOT Adjusted Load Forecast Winter .* for RS Magnitude"
    extensions = (".xlsx",)

    def _read(self, data: bytes, filename: str) -> Iterator[WinterLoadForecast]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member == "workbook.xlsx" else member
            sheets = {
                name: list(rows)
                for name, rows in _sheets(content, date_columns=(), preserve_types=True)
            }
            notes = [
                str(row[0]) for row in sheets.get("Explanation", []) if row and row[0]
            ]
            notes.extend(
                str(row[0])
                for row in sheets.get("Peak", [])
                if row and isinstance(row[0], str) and row[0].startswith("*")
            )
            match = re.search(r"(\d+)(?:st|nd|rd|th) percentile", " ".join(notes))
            percentile = int(match[1]) if match else None
            for name in ("Forecast", "Peak"):
                rows = sheets.get(name, [])
                if not rows:
                    continue
                peak = name == "Peak"
                prefix = (
                    [
                        "Forecasted Peak Date",
                        "Forecasted Peak Hour",
                        "ERCOT System Base Load (No LLs)",
                        "Large Load Additions*",
                        "ERCOT System Base Load (With LLs)",
                    ]
                    if peak
                    else [
                        "Date",
                        "Year",
                        "Month",
                        "Day",
                        "Hour",
                        "ERCOT System Base Load (No Large Loads)",
                        "ERCOT System Base Load (With Large Loads)",
                    ]
                )
                header = rows[0]
                if list(header[: len(prefix)]) != prefix:
                    raise ValueError(
                        f"{member}/{name}: unknown winter forecast columns"
                    )
                operators = [str(v or "") for v in header[len(prefix) :]]
                if len(set(operators)) != len(operators) or not all(operators):
                    raise ValueError(f"{member}/{name}: duplicate or empty operator")
                for line, values in enumerate(rows[1:], 2):
                    if (
                        not values
                        or values[0] is None
                        or str(values[0]).startswith("*")
                    ):
                        continue
                    if peak:
                        day = date.fromisoformat(str(values[0])[:10])
                        hour = int(str(values[1]).removesuffix(".0"))
                        source_date: date | None = day
                    else:
                        day, hour, source_date = _forecast_clock(values, 1)
                    found = True
                    yield WinterLoadForecast(
                        kind="peak" if peak else "hourly",
                        forecastDate=day,
                        hour=hour,
                        sourceDate=source_date,
                        baseLoad=_number(values[2 if peak else 5]),
                        loadWithLargeLoads=_number(values[4 if peak else 6]),
                        largeLoadAdditions=_number(values[3]) if peak else None,
                        transmissionOperators={
                            operator: _number(value)
                            for operator, value in zip(
                                operators, values[len(prefix) :], strict=True
                            )
                        },
                        percentile=percentile,
                        sourceNotes=notes,
                        sourceMember=member,
                        sourceSheet=name,
                        sourceRow=line,
                    )
        if not found:
            raise ValueError("No winter load forecast tables found")
