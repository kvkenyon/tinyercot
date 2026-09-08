"""Public summer peak-demand forecasts under historical weather scenarios."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from typing import Literal

from pydantic import Field

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._load_forecasts import _ForecastRow, _ForecastTable

_SUMMARIES = {
    "Official Forecast 50/50": "p50MW",
    "P50": "p50MW",
    "90th Percentile": "p90MW",
    "P90": "p90MW",
    "ercot_90th": "p90MW",
    "Forecast": "forecastMW",
    "Contracts": "contractsMW",
    "Officer Letters": "officerLettersMW",
    "Total Large Loads": "totalLargeLoadsMW",
}


class PeakDemandForecast(_ForecastRow):
    """One source forecast year/table; weather years are scenarios, not vintages."""

    forecastYear: int
    demandBasis: Literal["gross", "net", "rooftop_pv", "unspecified"]
    weatherYearMW: dict[int, Decimal | None]
    forecastMW: Decimal | None = None
    p50MW: Decimal | None = None
    p90MW: Decimal | None = None
    contractsMW: Decimal | None = None
    officerLettersMW: Decimal | None = None
    totalLargeLoadsMW: Decimal | None = None
    sourceSummaryLabels: dict[str, str]
    # Unlabelled auxiliary numeric cells have no inferred weather year or unit.
    sourceExtraValues: dict[int, Decimal | None] = Field(default_factory=dict)
    sourceTitle: str
    sourceNotes: list[str]


class PeakDemandForecasts(_ForecastTable[PeakDemandForecast]):
    title_pattern = "ERCOT Peak Demand Scenarios"

    def _read(self, data: bytes, filename: str) -> Iterator[PeakDemandForecast]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, iterator in _sheets(content, date_columns=()):
                if sheet == "Compatibility Report":
                    continue
                rows = list(iterator)
                notes = [
                    v
                    for row in rows
                    for v in row
                    if isinstance(v, str) and v.startswith("This includes ")
                ]
                title = ""
                header: tuple[object, ...] = ()
                for line, cells in enumerate(rows, 1):
                    for value in cells:
                        if (
                            isinstance(value, str)
                            and "Peak Demand (MW) based on" in value
                        ):
                            title, header = value, ()
                    if cells and cells[0] in ("Forecast Year", "year"):
                        header = cells
                        if not title:
                            raise ValueError(
                                f"{member}/{sheet}: missing peak-demand title"
                            )
                        continue
                    if not cells or not isinstance(cells[0], (int, float)):
                        continue
                    if not header:
                        raise ValueError(
                            f"{member}/{sheet}:{line}: missing forecast header"
                        )
                    basis: Literal["gross", "net", "rooftop_pv", "unspecified"] = (
                        "unspecified"
                    )
                    if title.startswith("Gross "):
                        basis = "gross"
                    elif title.startswith("Net "):
                        basis = "net"
                    elif title.startswith("Rooftop PV "):
                        basis = "rooftop_pv"
                    weather: dict[int, Decimal | None] = {}
                    summaries: dict[str, Decimal | None] = {}
                    labels: dict[str, str] = {}
                    extras: dict[int, Decimal | None] = {}
                    for column, value in enumerate(cells[1:], 1):
                        label = header[column] if column < len(header) else None
                        if label in (None, ""):
                            if value not in (None, ""):
                                extras[column + 1] = _number(value)
                        elif str(label).removesuffix(".0").isdigit():
                            weather[int(str(label).removesuffix(".0"))] = _number(value)
                        elif str(label) in _SUMMARIES:
                            field = _SUMMARIES[str(label)]
                            summaries[field] = _number(value)
                            labels[field] = str(label)
                        else:
                            raise ValueError(
                                f"{member}/{sheet}: unknown forecast column {label!r}"
                            )
                    found = True
                    yield PeakDemandForecast(
                        forecastYear=int(cells[0]),
                        demandBasis=basis,
                        weatherYearMW=weather,
                        sourceSummaryLabels=labels,
                        sourceExtraValues=extras,
                        sourceTitle=title,
                        sourceNotes=notes,
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=line,
                        sourceFile=None,
                        **summaries,
                    )
        if not found:
            raise ValueError("No peak-demand forecast tables found")
