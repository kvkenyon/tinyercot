"""Monthly public load forecasts and shared forecast-file discovery."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Literal, TypeVar
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import PublicFile, _PublicTable, _year_files


class _ForecastRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceFile: PublicFile | None = None


T = TypeVar("T", bound=_ForecastRow)


class _ForecastTable(_PublicTable[T]):
    index_url = "https://www.ercot.com/gridinfo/load/forecast"

    def files(self) -> list[PublicFile]:
        return [
            f
            for f in _year_files(self._http, self.index_url, self.title_pattern)
            if urlsplit(f.url).path.lower().endswith((".xls", ".xlsx"))
        ]

    def rows(self, *, where: Callable[[T], bool] | None = None) -> Iterator[T]:
        for file in self.files():
            for row in self.read(
                self.download(file), filename=file.url.rsplit("/", 1)[-1]
            ):
                row.sourceFile = file
                if where is None or where(row):
                    yield row


class MonthlyLoadForecast(_ForecastRow):
    """A source month/value pair; unlabelled dates and units remain unknown."""

    forecastYear: int | None
    forecastMonth: int | None
    peakDemand: Decimal | None
    energy: Decimal | None
    peakUnit: Literal["MW"] | None
    energyUnit: Literal["MWh"] | None
    sourcePeakLabel: str
    sourceEnergyLabel: str
    sourceTitle: str | None
    sourceColumn: int
    sourceNotes: list[str]


def _period(value: object) -> int | None:
    if value in (None, "", "year", "month", "Year", "Month"):
        return None
    return int(str(value).removesuffix(".0"))


class MonthlyLoadForecasts(_ForecastTable[MonthlyLoadForecast]):
    title_pattern = (
        r"(?:\d{4} )?ERCOT Monthly Peak Demand and Energy Forecast(?: \d{4})?"
    )

    def _read(self, data: bytes, filename: str) -> Iterator[MonthlyLoadForecast]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, iterator in _sheets(content, date_columns=()):
                rows = list(iterator)
                notes = [
                    v
                    for row in rows
                    for v in row
                    if isinstance(v, str) and v.startswith("This forecast ")
                ]
                # Two 2025 tables share rows, with independently labelled dates.
                blocks: list[tuple[int, str, str, str | None]] = []
                for line, row in enumerate(rows, 1):
                    headers = [
                        i
                        for i, value in enumerate(row)
                        if value in ("Peak (MW)", "Monthly Peaks")
                    ]
                    if headers:
                        blocks = []
                        for peak in headers:
                            energy = str(row[peak + 1])
                            if energy not in (
                                "Energy (Mwh)",
                                "Energy (MWh)",
                                "Annual Energy",
                            ):
                                raise ValueError(
                                    f"{member}/{sheet}: unknown energy header {energy!r}"
                                )
                            title = next(
                                (
                                    v
                                    for earlier in reversed(rows[: line - 1])
                                    for v in earlier[peak - 2 : peak + 2]
                                    if isinstance(v, str) and "Forecast" in v
                                ),
                                None,
                            )
                            blocks.append((peak - 2, str(row[peak]), energy, title))
                        continue
                    for start, peak_label, energy_label, title in blocks:
                        values = list(row[start : start + 4])
                        values.extend([None] * (4 - len(values)))
                        if all(v in (None, "") for v in values):
                            continue
                        year, month, peak_value, energy_value = values

                        found = True
                        yield MonthlyLoadForecast(
                            forecastYear=_period(year),
                            forecastMonth=_period(month),
                            peakDemand=_number(peak_value),
                            energy=_number(energy_value),
                            peakUnit="MW" if peak_label == "Peak (MW)" else None,
                            energyUnit="MWh"
                            if energy_label.startswith("Energy (")
                            else None,
                            sourcePeakLabel=peak_label,
                            sourceEnergyLabel=energy_label,
                            sourceTitle=title,
                            sourceColumn=start + 1,
                            sourceNotes=notes,
                            sourceMember=member,
                            sourceSheet=sheet,
                            sourceRow=line,
                        )
        if not found:
            raise ValueError("No monthly load forecast tables found")
