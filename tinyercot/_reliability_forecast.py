"""Hourly load and peak breakdowns for the winter reliability study."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ._load import _sheets


class TransmissionOperatorLoad(BaseModel):
    """An operator's share of base load, excluding large-load additions."""

    name: str
    loadMW: Decimal | None
    sourceColumn: int


class ReliabilityForecastNote(BaseModel):
    text: str
    sourceSheet: str
    sourceRow: int
    sourceColumn: int


class _Load(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    hour: int
    baseLoadMW: Decimal | None
    loadWithLargeLoadsMW: Decimal | None
    operators: list[TransmissionOperatorLoad]
    sourceSheet: str
    sourceRow: int


class ReliabilityForecastHour(_Load):
    """A published local date/hour; no UTC or interval convention is inferred."""

    sourceYear: int
    sourceMonth: int
    sourceDay: int


class ReliabilityForecastPeak(_Load):
    """The published peak and explicit large-load additions, without recomputation."""

    largeLoadAdditionsMW: Decimal | None


class ReliabilityLoadForecast(BaseModel):
    """A complete study workbook, including its assumptions and published peak.

    Hourly operator shares exclude large-load additions. Original date component
    columns remain available alongside Date; no timestamp repair is performed.
    The percentile comes from the explanation, not an empirical recalculation.
    """

    title: str
    percentile: int | None
    hours: list[ReliabilityForecastHour]
    peaks: list[ReliabilityForecastPeak]
    notes: list[ReliabilityForecastNote]
    sourceMember: str


def read_reliability(data: bytes, *, filename: str) -> ReliabilityLoadForecast:
    result = ReliabilityLoadForecast(
        title="", percentile=None, hours=[], peaks=[], notes=[], sourceMember=filename
    )
    for sheet, rows in _sheets(data):
        if sheet == "Explanation":
            for i, row in enumerate(rows, 1):
                for j, value in enumerate(row, 1):
                    if value is not None:
                        result.notes.append(
                            ReliabilityForecastNote(
                                text=str(value),
                                sourceSheet=sheet,
                                sourceRow=i,
                                sourceColumn=j,
                            )
                        )
                        if i == 1 and j == 1:
                            result.title = str(value)
                        match = re.search(
                            r"(\d+)(?:st|nd|rd|th) percentile", str(value)
                        )
                        if match:
                            result.percentile = int(match[1])
            continue
        header = next(rows)
        if sheet == "Forecast" and header[:7] == (
            "Date",
            "Year",
            "Month",
            "Day",
            "Hour",
            "ERCOT System Base Load (No Large Loads)",
            "ERCOT System Base Load (With Large Loads)",
        ):
            offset = 7
        elif sheet == "Peak" and header[:5] == (
            "Forecasted Peak Date",
            "Forecasted Peak Hour",
            "ERCOT System Base Load (No LLs)",
            "Large Load Additions*",
            "ERCOT System Base Load (With LLs)",
        ):
            offset = 5
        else:
            raise ValueError(f"Unsupported reliability forecast worksheet: {sheet}")
        for i, row in enumerate(rows, 2):
            row += (None,) * max(0, len(header) - len(row))
            if not any(v is not None for v in row):
                continue
            if isinstance(row[0], str) and row[0].startswith("*"):
                for j, value in enumerate(row, 1):
                    if value is not None:
                        result.notes.append(
                            ReliabilityForecastNote(
                                text=str(value),
                                sourceSheet=sheet,
                                sourceRow=i,
                                sourceColumn=j,
                            )
                        )
                continue
            values: dict[str, object] = {
                "operatingDay": row[0],
                "hour": row[4] if sheet == "Forecast" else row[1],
                "baseLoadMW": _number(row[5] if sheet == "Forecast" else row[2]),
                "loadWithLargeLoadsMW": _number(
                    row[6] if sheet == "Forecast" else row[4]
                ),
                "operators": [
                    TransmissionOperatorLoad(
                        name=str(label), loadMW=_number(row[j]), sourceColumn=j + 1
                    )
                    for j, label in enumerate(header[offset:], offset)
                ],
                "sourceSheet": sheet,
                "sourceRow": i,
            }
            if sheet == "Forecast":
                values.update(sourceYear=row[1], sourceMonth=row[2], sourceDay=row[3])
                result.hours.append(ReliabilityForecastHour.model_validate(values))
            else:
                values["largeLoadAdditionsMW"] = _number(row[3])
                result.peaks.append(ReliabilityForecastPeak.model_validate(values))
    if not result.title or not result.hours or not result.peaks:
        raise ValueError("Missing reliability forecast explanation, hours or peak")
    return result


def _number(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))
