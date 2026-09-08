"""Published hourly load forecasts, actuals and separate error summaries."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import datetime, time
from decimal import Decimal
from typing import Literal

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._load_forecasts import _ForecastRow, _ForecastTable
from ._public_tables import PublicFile
from ._weather import WeatherZone

_REGIONS: dict[str, WeatherZone | Literal["ERCOT"]] = {
    "coast": "COAST",
    "east": "EAST",
    "farwest": "FWEST",
    "north": "NORTH",
    "ncent": "NCENT",
    "northcentral": "NCENT",
    "scent": "SCENT",
    "southcentral": "SCENT",
    "south": "SOUTH",
    "west": "WEST",
    "ercot": "ERCOT",
}
_OLD = (
    "HE",
    "Actual",
    "Selected ",
    "A3",
    "A6",
    "E",
    "E1",
    "E2",
    "E3",
    "M",
    None,
    "HE",
    "Hour",
    "Hourly Error",
    "Under",
    "Over",
    "Freq Under",
    "Freq Over",
    "MAPE",
)
_NEW = (
    "Date & Time",
    "Actual",
    "Selected",
    "E",
    "E1",
    "E2",
    "E3",
    "M",
    "X",
    None,
    "Hour",
    "Error",
    "Under",
    "Over",
)
_FIELDS = {
    "Actual": "actual",
    "Selected": "selected",
    "Hour": "sourceHour",
    "Hourly Error": "error",
    "Error": "error",
    "Under": "under",
    "Over": "over",
    "Freq Under": "frequencyUnder",
    "Freq Over": "frequencyOver",
    "MAPE": "mape",
}


class _PerformanceRow(_ForecastRow):
    region: WeatherZone | Literal["ERCOT"]
    sourceMarkers: dict[str, str]


class LoadForecastPerformanceHour(_PerformanceRow):
    """Source model codes and published errors, without inferred issue times."""

    timestamp: datetime | None
    sourceHour: Decimal | None
    errorTimestamp: datetime | None
    hour: int | None
    actual: Decimal | None
    selected: Decimal | None
    A3: Decimal | None = None
    A6: Decimal | None = None
    E: Decimal | None
    E1: Decimal | None
    E2: Decimal | None
    E3: Decimal | None
    M: Decimal | None
    X: Decimal | None = None
    error: Decimal | None
    under: Decimal | None
    over: Decimal | None
    frequencyUnder: int | None = None
    frequencyOver: int | None = None
    mape: Decimal | None = None


class LoadForecastErrorSummary(_PerformanceRow):
    """A published summary block; its bucket is not the adjacent hourly date."""

    kind: Literal["average_error", "frequency", "monthly_mape"]
    hour: int | None
    sourceBucket: str
    under: Decimal | None = None
    over: Decimal | None = None
    frequencyUnder: int | None = None
    frequencyOver: int | None = None
    mape: Decimal | None = None
    sourceColumn: int


def _value(value: object, field: str, markers: dict[str, str]) -> Decimal | None:
    try:
        return _number(value)
    except ValueError:
        if not isinstance(value, str):
            raise
        markers[field] = value
        return None


def _clock(value: object, field: str, markers: dict[str, str]) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, time):
        markers[field] = value.isoformat()
        return None
    if value == 0:
        markers[field] = "0"
        return None
    for fmt in ("%d%b%Y:%H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(str(value), fmt)  # noqa: DTZ007
        except ValueError:
            pass
    raise ValueError(f"Invalid forecast metric timestamp: {value!r}")


class LoadForecastPerformance(_ForecastTable[LoadForecastPerformanceHour]):
    title_pattern = r".*(?:Metrics|Metrtics|Backcast).*"
    extensions = (".xlsx",)

    def files(self) -> list[PublicFile]:
        # Jan/Feb 2026 hourly metric files have misleading Backcast link titles.
        return [
            f for f in super().files() if "metrics" in f.url.rsplit("/", 1)[-1].lower()
        ]

    def _tables(
        self, data: bytes, filename: str
    ) -> Iterator[tuple[str, str, bool, Iterator[tuple[object, ...]]]]:
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                header = next(rows, ())
                modern = header[: len(_NEW)] == _NEW
                if not modern and header[: len(_OLD)] != _OLD:
                    raise ValueError(
                        f"{member}/{sheet}: unknown forecast metric columns"
                    )
                if sheet.lower().replace(" ", "") not in _REGIONS:
                    raise ValueError(
                        f"{member}/{sheet}: unknown forecast metric region"
                    )
                yield (
                    member,
                    sheet,
                    modern,
                    (tuple(row) + (None,) * max(0, 34 - len(row)) for row in rows),
                )

    def _read(
        self, data: bytes, filename: str
    ) -> Iterator[LoadForecastPerformanceHour]:
        found = False
        for member, sheet, modern, rows in self._tables(data, filename):
            header = _NEW if modern else _OLD
            for line, values in enumerate(rows, 2):
                if not any(v not in (None, "") for v in values[: len(header)]):
                    continue
                markers: dict[str, str] = {}
                numbers = {
                    _FIELDS.get(label.strip(), label.strip()): _value(
                        values[i], _FIELDS.get(label.strip(), label.strip()), markers
                    )
                    for i, label in enumerate(header)
                    if label and label not in ("HE", "Date & Time")
                }
                source_hour = numbers["sourceHour"]
                hour = (
                    int(source_hour)
                    if source_hour is not None
                    and 1 <= source_hour <= 24
                    and source_hour == int(source_hour)
                    else None
                )
                clock = _clock(values[0], "timestamp", markers)
                error_clock = (
                    None if modern else _clock(values[11], "errorTimestamp", markers)
                )
                found = True
                yield LoadForecastPerformanceHour.model_validate(
                    {
                        **numbers,
                        "timestamp": clock,
                        "hour": hour,
                        "errorTimestamp": error_clock,
                        "region": _REGIONS[sheet.lower().replace(" ", "")],
                        "sourceMarkers": markers,
                        "sourceMember": member,
                        "sourceSheet": sheet,
                        "sourceRow": line,
                    }
                )
        if not found:
            raise ValueError("No hourly forecast performance rows found")

    def summaries(
        self, *, where: Callable[[LoadForecastErrorSummary], bool] | None = None
    ) -> Iterator[LoadForecastErrorSummary]:
        for file in self.files():
            for row in self.read_summaries(
                self.download(file), filename=file.url.rsplit("/", 1)[-1]
            ):
                row.sourceFile = file
                if where is None or where(row):
                    yield row

    def read_summaries(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[LoadForecastErrorSummary], bool] | None = None,
    ) -> Iterator[LoadForecastErrorSummary]:
        found = False
        for member, sheet, modern, rows in self._tables(data, filename):
            region = _REGIONS[sheet.lower().replace(" ", "")]
            average = 15 if modern else 31 if region == "ERCOT" else 25
            chart_kind = "average_error"
            for line, values in enumerate(rows, 2):
                if not modern and values[average] in ("Hour", "HE"):
                    chart_kind = (
                        "frequency" if values[average] == "HE" else "average_error"
                    )
                blocks = [(chart_kind, average)]
                if modern:
                    blocks.append(("frequency", 19))
                elif len(values) > 19 and values[19] not in (None, ""):
                    blocks.append(("monthly_mape", 19))
                for kind, column in blocks:
                    value = values[column] if column < len(values) else None
                    if value in (None, "", "Hour", "HE"):
                        continue
                    markers: dict[str, str] = {}
                    if kind == "monthly_mape":
                        numbers = {"mape": _value(value, "mape", markers)}
                        bucket = "Monthly"
                    else:
                        fields = (
                            ("frequencyUnder", "frequencyOver")
                            if kind == "frequency"
                            else ("under", "over")
                        )
                        numbers = {
                            field: _value(values[column + i], field, markers)
                            for i, field in enumerate(fields, 1)
                        }
                        bucket = str(value)
                    row = LoadForecastErrorSummary.model_validate(
                        {
                            **numbers,
                            "kind": kind,
                            "sourceBucket": bucket,
                            "hour": int(value)
                            if kind != "monthly_mape"
                            and isinstance(value, (int, float))
                            and value == int(value)
                            else None,
                            "region": region,
                            "sourceMarkers": markers,
                            "sourceMember": member,
                            "sourceSheet": sheet,
                            "sourceRow": line,
                            "sourceColumn": column + 1,
                        }
                    )
                    found = True
                    if where is None or where(row):
                        yield row
        if not found:
            raise ValueError("No forecast performance summaries found")
