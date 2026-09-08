"""Public long-term load forecast summary workbooks."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from time import strptime
from typing import Literal
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from ._load import _sheets
from ._reliability_forecast import ReliabilityLoadForecast, read_reliability

INDEX_URL = "https://www.ercot.com/gridinfo/load/forecast/index.html"
ForecastKind = Literal[
    "monthly",
    "weekly-p90",
    "weather-year-peaks",
    "seasonal-peaks",
    "winter-reliability",
]
ForecastScenario = Literal["ERCOT Adjusted", "TSP Provided"]


class LoadForecastArchive(BaseModel):
    """A directly linked forecast; its section identifies the published vintage."""

    kind: ForecastKind
    title: str
    section: str
    url: str


class _Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceColumn: int


class MonthlyLoadForecast(_Source):
    """One source row, with no repair of misaligned date labels.

    The published TSP table starts with quantities alongside 'year'/'month',
    and ends with a date alongside empty quantities. Both rows are retained.
    Energy units are not specified in this workbook; the original label stays
    explicit rather than silently interpreting 'Annual Energy' as monthly MWh.
    """

    scenario: ForecastScenario
    year: int | None
    month: int | None
    sourceYear: str | None
    sourceMonth: str | None
    peakDemandMW: Decimal | None
    energy: Decimal | None
    energyLabel: str


class LoadForecastPeak(_Source):
    """A peak by forecast period, region, scenario and (where given) weather year.

    Winter labels span two years. Coincident regional values and published ERCOT
    totals are retained independently. No totals or percentiles are recalculated.
    """

    scenario: ForecastScenario
    year: int
    yearTo: int
    periodLabel: str
    season: Literal["Summer", "Winter"]
    region: str
    weatherYear: int | None = None
    percentile: int | None = None
    coincident: bool | None = None
    peakDemandMW: Decimal | None
    sourceLabel: str


class WeeklyLoadForecast(_Source):
    """Published P90 weekly peak and regional values at the source peak hour.

    Peak_Hour is preserved without inventing an interval-ending or UTC convention.
    """

    beginDate: date
    endDate: date
    peakDate: date
    peakHour: int
    percentile: Literal[90] = 90
    region: str
    peakDemandMW: Decimal | None


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.href: str | None = None
        self.title = ""
        self.heading = False
        self.section = ""
        self.files: dict[str, LoadForecastArchive] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("h2", "h3"):
            self.heading, self.section = True, ""
        if tag == "a":
            self.href, self.title = dict(attrs).get("href"), ""

    def handle_data(self, data: str) -> None:
        if self.heading:
            self.section += data
        if self.href is not None:
            self.title += data

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h2", "h3"):
            self.heading = False
        if tag != "a" or self.href is None:
            return
        url = urljoin(INDEX_URL, self.href)
        self.href = None
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.netloc != "www.ercot.com":
            return
        title = " ".join(self.title.split())
        kind: ForecastKind
        if re.fullmatch(r"\d{4} ERCOT Monthly Peak Demand and Energy Forecast", title):
            kind = "monthly"
        elif re.fullmatch(r"\d{4} Weekly P90 Peaks", title):
            kind = "weekly-p90"
        elif title == "ERCOT Peak Demand Scenarios":
            kind = "weather-year-peaks"
        elif title == "Summer and Winter Peaks":
            kind = "seasonal-peaks"
        elif re.fullmatch(
            r"ERCOT Adjusted Load Forecast Winter \d{4}-\d{4} for RS Magnitude", title
        ):
            kind = "winter-reliability"
        else:
            return
        if parts.path.endswith(".xlsx"):
            self.files[url] = LoadForecastArchive(
                kind=kind, title=title, section=" ".join(self.section.split()), url=url
            )


class LoadForecast:
    """Discover and query public planning files without API credentials.

    XLSX decoding uses tinyercot[files]. Each query takes one archive to keep
    published vintages distinct. The winter reliability workbook has its own
    reader; other hourly forecasts and model-error reports have separate layouts.
    """

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(
        self, *, kind: ForecastKind | None = None
    ) -> list[LoadForecastArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links()
        links.feed(response.text)
        if not links.files:
            raise ValueError("No load forecast summaries found in ERCOT's public index")
        return [a for a in links.files.values() if kind is None or a.kind == kind]

    def download(self, archive: LoadForecastArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def reliability(self, archive: LoadForecastArchive) -> ReliabilityLoadForecast:
        """Read a winter reliability workbook, including all hours, peaks and notes."""
        if archive.kind != "winter-reliability":
            raise ValueError("Select a winter reliability forecast archive")
        return self.read_reliability(
            self.download(archive), filename=_filename(archive)
        )

    def read_reliability(
        self, data: bytes, *, filename: str = "workbook"
    ) -> ReliabilityLoadForecast:
        """Decode a saved workbook; query its typed hours by operatingDay/operator."""
        return read_reliability(data, filename=filename)

    def monthly(self, archive: LoadForecastArchive) -> Iterator[MonthlyLoadForecast]:
        """Read monthly source labels and values, including unlabelled quantities."""
        if archive.kind != "monthly":
            raise ValueError("Select a monthly forecast archive")
        yield from self.read_monthly(
            self.download(archive), filename=_filename(archive)
        )

    def peaks(self, archive: LoadForecastArchive) -> Iterator[LoadForecastPeak]:
        """Read seasonal or weather-year peaks; filter typed rows by year/region."""
        if archive.kind not in ("weather-year-peaks", "seasonal-peaks"):
            raise ValueError("Select a seasonal or weather-year peak archive")
        yield from self.read_peaks(self.download(archive), filename=_filename(archive))

    def weekly(self, archive: LoadForecastArchive) -> Iterator[WeeklyLoadForecast]:
        if archive.kind != "weekly-p90":
            raise ValueError("Select a weekly P90 forecast archive")
        yield from self.read_weekly(self.download(archive), filename=_filename(archive))

    def read_monthly(
        self, data: bytes, *, filename: str = "workbook"
    ) -> Iterator[MonthlyLoadForecast]:
        for sheet, rows in _sheets(data):
            title, header = next(rows), next(rows)
            if (
                title[0] != "ERCOT Adjusted Forecast"
                or title[6] != "TSP Provided Forecast"
            ):
                raise ValueError("Unsupported monthly forecast headings")
            for number, row in enumerate(rows, 3):
                row += (None,) * max(0, 9 - len(row))
                for offset, scenario in [(0, "ERCOT Adjusted"), (5, "TSP Provided")]:
                    y, m, peak, energy = row[offset : offset + 4]
                    if all(v is None for v in (y, m, peak, energy)):
                        continue
                    yield MonthlyLoadForecast.model_validate(
                        {
                            "scenario": scenario,
                            "year": int(str(y)) if y not in (None, "year") else None,
                            "month": int(str(m)) if m not in (None, "month") else None,
                            "sourceYear": None if y is None else str(y),
                            "sourceMonth": None if m is None else str(m),
                            "peakDemandMW": _number(peak),
                            "energy": _number(energy),
                            "energyLabel": str(header[offset + 3]),
                            "sourceMember": filename,
                            "sourceSheet": sheet,
                            "sourceRow": number,
                            "sourceColumn": offset + 1,
                        }
                    )

    def read_peaks(
        self, data: bytes, *, filename: str = "workbook"
    ) -> Iterator[LoadForecastPeak]:
        for sheet, rows in _sheets(data):
            if sheet in ("ERCOT Adjusted", "TSP Provided"):
                table = list(rows)
                label, header = str(table[1][0]), table[5]
                if header[0] != "year" or "Net Summer Peak Demand (MW)" not in label:
                    raise ValueError("Unsupported weather-year peak headings")
                for number, row in enumerate(table[6:], 7):
                    row += (None,) * max(0, len(header) - len(row))
                    if row[0] is None:
                        continue
                    for j, weather in enumerate(header[1:], 1):
                        if weather is None:
                            continue
                        yield LoadForecastPeak.model_validate(
                            {
                                "scenario": sheet,
                                "year": int(str(row[0])),
                                "yearTo": int(str(row[0])),
                                "periodLabel": str(row[0]),
                                "season": "Summer",
                                "region": "ERCOT",
                                "weatherYear": None
                                if weather == "ercot_90th"
                                else int(str(weather)),
                                "percentile": 90 if weather == "ercot_90th" else None,
                                "peakDemandMW": _number(row[j]),
                                "sourceLabel": label,
                                "sourceMember": filename,
                                "sourceSheet": sheet,
                                "sourceRow": number,
                                "sourceColumn": j + 1,
                            }
                        )
            elif sheet in ("Summer", "Winter"):
                sections: dict[int, tuple[str, tuple[object, ...]]] = {}
                labels: dict[int, str] = {}
                for number, row in enumerate(rows, 1):
                    row += (None,) * max(0, 25 - len(row))
                    for offset in (0, 15):
                        period = row[offset]
                        if isinstance(period, str) and "Peak Forecast" in period:
                            labels[offset] = period
                        elif row[offset + 1] == "COAST":
                            sections[offset] = (
                                labels[offset],
                                row[offset + 1 : offset + 10],
                            )
                        elif period is not None:
                            label, regions = sections[offset]
                            years = str(period).split("-")
                            for j, region in enumerate(regions, offset + 1):
                                yield LoadForecastPeak.model_validate(
                                    {
                                        "scenario": "ERCOT Adjusted"
                                        if "ERCOT Adjusted" in label
                                        else "TSP Provided",
                                        "year": int(years[0]),
                                        "yearTo": int(years[-1]),
                                        "periodLabel": str(period),
                                        "season": sheet,
                                        "region": region,
                                        "coincident": "Non-Coincident" not in label,
                                        "peakDemandMW": _number(row[j]),
                                        "sourceLabel": label,
                                        "sourceMember": filename,
                                        "sourceSheet": sheet,
                                        "sourceRow": number,
                                        "sourceColumn": j + 1,
                                    }
                                )
            else:
                raise ValueError(f"Unsupported peak forecast worksheet: {sheet}")

    def read_weekly(
        self, data: bytes, *, filename: str = "workbook"
    ) -> Iterator[WeeklyLoadForecast]:
        for sheet, rows in _sheets(data):
            header = next(rows)
            if header[:4] != ("Begin_Date", "End_Date", "Peak_Date", "Peak_Hour"):
                raise ValueError("Unsupported weekly forecast headings")
            for number, row in enumerate(rows, 2):
                row += (None,) * max(0, len(header) - len(row))
                if not any(v is not None for v in row):
                    continue
                for j, region in enumerate(header[4:], 4):
                    yield WeeklyLoadForecast(
                        beginDate=_date(row[0]),
                        endDate=_date(row[1]),
                        peakDate=_date(row[2]),
                        peakHour=int(str(row[3])),
                        region=str(region),
                        peakDemandMW=_number(row[j]),
                        sourceMember=filename,
                        sourceSheet=sheet,
                        sourceRow=number,
                        sourceColumn=j + 1,
                    )


def _number(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _date(value: object) -> date:
    return date(*strptime(str(value), "%d%b%Y")[:3])


def _filename(archive: LoadForecastArchive) -> str:
    return archive.url.rsplit("/", 1)[-1]
