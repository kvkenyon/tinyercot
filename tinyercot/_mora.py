"""Typed numeric tables from monthly resource-adequacy outlook workbooks."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from time import strptime
from typing import Literal
from urllib.parse import urljoin, urlsplit

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import PublicFile, _FileLinks, _PublicFiles

MoraMetric = Literal[
    "gross_demand",
    "solar_generation",
    "wind_generation",
    "thermal_outages",
    "non_extreme_weather_outages",
    "extreme_weather_outages",
]
_METRICS: dict[str, MoraMetric] = {
    "Gross Demand by Hour, MW": "gross_demand",
    "Solar Generation by Hour, MW": "solar_generation",
    "Wind Generation by Hour, MW": "wind_generation",
    "Thermal Unplanned Outages": "thermal_outages",
    "Unplanned Thermal Outages-Daily, MW": "thermal_outages",
    "Unplanned Thermal Outages Not Due to Extreme Weather - Daily, MW": "non_extreme_weather_outages",
    "Unplanned Thermal Outages Due to Extreme Weather - Daily, MW": "extreme_weather_outages",
}


class MoraPercentile(BaseModel):
    """One published forecast percentile, separate from realized observations.

    percentile is a fraction in 0–1. hour is the source's numbered hour, or None
    for daily outages; it is not a UTC clock or a dated hourly observation.
    """

    model_config = ConfigDict(extra="forbid")
    reportMonth: date
    metric: MoraMetric
    percentile: Decimal
    hour: int | None
    value: Decimal | None
    sourceUnit: Literal["MW"] | None
    sourceMetric: str
    sourceReportLabel: str
    sourcePercentile: str
    sourcePeriodLabel: str
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str


class _MoraLinks(_FileLinks):
    def __init__(self, index_url: str, title_pattern: str) -> None:
        super().__init__(index_url, title_pattern)
        self.years: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        super().handle_starttag(tag, attrs)
        if tag == "a" and self.href:
            url = urljoin(self.index_url, self.href)
            parts = urlsplit(url)
            if (
                parts.scheme == "https"
                and parts.netloc == "www.ercot.com"
                and re.fullmatch(r"/gridinfo/resource/\d{4}", parts.path)
            ):
                self.years.add(url)


class ResourceOutlook(_PublicFiles):
    """Discover MORA workbooks, including links in the historical year indexes."""

    index_url = "https://www.ercot.com/gridinfo/resource"
    title_pattern = r"Monthly Outlook for Resource Adequacy \(MORA\) .+"

    def files(self) -> list[PublicFile]:
        def links(url: str) -> _MoraLinks:
            response = self._http.get(url, follow_redirects=True)
            response.raise_for_status()
            parser = _MoraLinks(url, self.title_pattern)
            parser.feed(response.text)
            return parser

        current = links(self.index_url)
        files = dict(current.files)
        for url in sorted(current.years):
            files.update(links(url).files)
        workbooks = [
            f
            for f in files.values()
            if urlsplit(f.url).path.lower().endswith((".xlsx", ".xls"))
        ]
        if not workbooks:
            raise ValueError("No MORA workbooks found in ERCOT's public indexes")
        return sorted(workbooks, key=lambda f: f.url)

    def percentiles(
        self, *, where: Callable[[MoraPercentile], bool] | None = None
    ) -> Iterator[MoraPercentile]:
        """Query all published percentile tables, retaining report revisions."""
        for file in self.files():
            yield from self.read_percentiles(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def read_percentiles(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[MoraPercentile], bool] | None = None,
    ) -> Iterator[MoraPercentile]:
        """Read saved workbooks/ZIPs without inventing omitted hours or metrics."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            month, report_label = _report_month(content)
            for sheet, source in _sheets(content, date_columns=()):
                if sheet != "PRRM Percentile Results":
                    continue
                found = True
                rows = list(source)
                notes = [
                    v
                    for cells in rows
                    for v in cells
                    if isinstance(v, str) and v.startswith("* ")
                ]
                metric: MoraMetric | None = None
                label = ""
                columns: list[tuple[int, int | None, str]] = []
                for cells in rows:
                    if all(v in (None, "") for v in cells):
                        continue
                    title = next(
                        (
                            v
                            for v in cells[:2]
                            if isinstance(v, str)
                            and v != "Percentiles"
                            and not re.fullmatch(r"\d+(?:\.\d+)?%", v)
                        ),
                        None,
                    )
                    if title is not None:
                        label = title
                        metric = next(
                            (v for k, v in _METRICS.items() if title.startswith(k)),
                            None,
                        )
                        columns = []
                        continue
                    if len(cells) > 1 and cells[1] == "Percentiles":
                        if metric is None:
                            raise ValueError(
                                f"{member}/{sheet}: Unknown percentile metric"
                            )
                        columns = []
                        for i, v in enumerate(cells[2:], 2):
                            if v in (None, ""):
                                continue
                            if (
                                isinstance(v, (int, float))
                                and v == int(v)
                                and 1 <= v <= 24
                            ):
                                columns.append((i, int(v), str(v)))
                            elif metric.endswith("outages") and v in (
                                "Daily",
                                "Unplanned Thermal Outages",
                                "Thermal Unplanned Outages, Daily",
                                "Weather-related Thermal Outages, Winter",
                            ):
                                columns.append((i, None, str(v)))
                            else:
                                raise ValueError(
                                    f"{member}/{sheet}: Unknown hour column"
                                )
                        continue
                    if len(cells) < 2 or cells[1] in (None, ""):
                        continue
                    value = cells[1]
                    if isinstance(value, str) and not value.endswith("%"):
                        continue
                    percentile = (
                        Decimal(value[:-1]) / 100
                        if isinstance(value, str)
                        else _number(value)
                    )
                    if metric is None or not columns or percentile is None:
                        raise ValueError(f"{member}/{sheet}: Missing percentile header")
                    for column, hour, period_label in columns:
                        record = MoraPercentile(
                            reportMonth=month,
                            metric=metric,
                            percentile=percentile,
                            hour=hour,
                            value=_number(
                                cells[column] if column < len(cells) else None
                            ),
                            sourceUnit="MW" if ", MW" in label else None,
                            sourceMetric=label,
                            sourceReportLabel=report_label,
                            sourcePercentile=str(value),
                            sourcePeriodLabel=period_label,
                            sourceNotes=notes,
                            sourceMember=member,
                            sourceSheet=sheet,
                        )
                        if where is None or where(record):
                            yield record
        if not found:
            raise ValueError("Download contains no MORA percentile tables")


def _report_month(data: bytes) -> tuple[date, str]:
    for sheet, rows in _sheets(data, date_columns=()):
        if sheet == "Cover":
            for cells in rows:
                for value in cells:
                    if isinstance(value, str) and value.startswith("Reporting Month:"):
                        match = re.fullmatch(
                            r"Reporting Month:\s*([A-Za-z]+ \d{4})(?:,? Revised)?",
                            value,
                            re.IGNORECASE,
                        )
                        if match:
                            return date(*strptime(match[1], "%B %Y")[:3]), value
    raise ValueError("MORA workbook is missing its reporting month")
