"""Typed numeric tables from monthly resource-adequacy outlook workbooks."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date, time
from decimal import Decimal
from io import BytesIO
from time import strptime
from typing import TYPE_CHECKING, Literal, cast

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import _ResourceFiles

if TYPE_CHECKING:
    from openpyxl.worksheet._read_only import ReadOnlyWorksheet

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


class MoraResource(BaseModel):
    """One unit or summary capacity row in an assessment-month outlook.

    inService retains a year, date or source status such as #N/A. Category and
    capacity labels describe the source's status and rating basis; neither
    installed capacity nor the reported rating implies available generation.
    Summary rows include totals, contributions and adjustments; source unit
    codes also appear on summaries. An omitted category remains None.
    """

    model_config = ConfigDict(extra="forbid")
    reportMonth: date
    kind: Literal["unit", "summary"]
    category: str | None
    name: str
    interconnectionRequestNumber: str | None
    unitCode: str | None
    county: str | None
    fuel: str | None
    zone: str | None
    inService: int | date | str | None
    installedCapacityMW: Decimal | None
    reportedCapacityMW: Decimal | None
    sourceInstalledCapacityLabel: str
    sourceCapacityLabel: str
    sourceInServiceLabel: str
    sourceReportLabel: str
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str
    sourceRow: int


class MoraScenarioValue(BaseModel):
    """A forecast MW value at a source scenario's hour, without an assumed date."""

    model_config = ConfigDict(extra="forbid")
    sourceScenario: str
    hourEnding: time
    timeZone: Literal["CST", "CDT"] | None
    valueMW: Decimal | None


class _MoraTableRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reportMonth: date
    sourceReportLabel: str
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str
    sourceRow: int


class MoraCapacity(_MoraTableRow):
    """Category ratings with their source hierarchy and separate scenario values.

    resourcePath includes each parent label. Parent and child ratings overlap;
    installedCapacityMW is reported once, independent of scenario count.
    """

    section: Literal["operational", "planned", "total"]
    sourceSectionLabel: str
    resourcePath: list[str]
    installedCapacityMW: Decimal | None
    availableCapacity: list[MoraScenarioValue]
    sourceInstalledCapacityLabel: str
    sourceAvailableCapacityLabel: str | None


MoraBalanceMetric = Literal[
    "average_weather_load",
    "large_load_adjustment",
    "large_flexible_load_adjustment",
    "total_load",
    "dispatchable_capacity",
    "thermal_capacity",
    "thermal_capacity_excluding_emergency_agreements",
    "storage_capacity",
    "hydro_capacity",
    "thermal_outages",
    "planned_thermal_outages",
    "unplanned_thermal_outages",
    "available_dispatchable_capacity",
    "wind_capacity",
    "solar_capacity",
    "available_non_dispatchable_capacity",
    "dc_tie_net_imports",
    "available_resources",
    "emergency_response_service",
    "distribution_voltage_reduction",
    "large_load_curtailment",
    "large_flexible_load_curtailment",
    "crypto_demand_response",
    "emergency_resources_before_eea",
    "responsive_reserve_load_resources",
    "non_spin_load_resources",
    "ecrs_load_resources",
    "tdsp_load_management",
    "rmr_and_other_agreement_capacity",
    "emergency_resources_during_eea",
    "total_emergency_resources",
    "normal_condition_reserves",
    "emergency_condition_reserves",
]
_BALANCE_METRICS: dict[str, MoraBalanceMetric] = {
    "Load Based on Average Weather": "average_weather_load",
    "Large Load Adjustment": "large_load_adjustment",
    "Large Flexible Load Adjustment": "large_flexible_load_adjustment",
    "Total Load": "total_load",
    "Dispatchable": "dispatchable_capacity",
    "Thermal": "thermal_capacity",
    "Thermal, excluding RMR and other Emergency Generation Agreements": "thermal_capacity_excluding_emergency_agreements",
    "Energy Storage": "storage_capacity",
    "Hydro": "hydro_capacity",
    "Expected Thermal Outages": "thermal_outages",
    "Planned": "planned_thermal_outages",
    "Unplanned": "unplanned_thermal_outages",
    "Total Available Dispatchable": "available_dispatchable_capacity",
    "Wind": "wind_capacity",
    "Solar": "solar_capacity",
    "Total Available Non-Dispatchable": "available_non_dispatchable_capacity",
    "Non-Synchronous Ties, Net Imports": "dc_tie_net_imports",
    "Total Available Resources (Normal Conditions)": "available_resources",
    "Emergency Response Service": "emergency_response_service",
    "Distribution Voltage Reduction": "distribution_voltage_reduction",
    "Large Load Curtailment": "large_load_curtailment",
    "Large Flexible Load Curtailment": "large_flexible_load_curtailment",
    "Anticipated Crypto Demand Response": "crypto_demand_response",
    "Available prior to an Energy Emergency Alert": "emergency_resources_before_eea",
    "Total Available prior to an Energy Emergency Alert": "emergency_resources_before_eea",
    "LRs providing Responsive Reserves": "responsive_reserve_load_resources",
    "LRs providing Non-spin": "non_spin_load_resources",
    "LRs providing ECRS": "ecrs_load_resources",
    "TDSP Load Management Programs": "tdsp_load_management",
    "RMR and Other Resource Agreement Capacity Units": "rmr_and_other_agreement_capacity",
    "Available during an Energy Emergency Alert": "emergency_resources_during_eea",
    "Total Available during an Energy Emergency Alert": "emergency_resources_during_eea",
    "Total Emergency Resources": "total_emergency_resources",
    "Capacity Available for Operating Reserves, Normal Conditions": "normal_condition_reserves",
    "Capacity Available for Operating Reserves, Emergency Conditions": "emergency_condition_reserves",
}


class MoraBalance(_MoraTableRow):
    """A published load/resource balance quantity, including scenario assumptions."""

    metric: MoraBalanceMetric
    sourceMetric: str
    values: list[MoraScenarioValue]


class ResourceOutlook(_ResourceFiles):
    """Discover MORA workbooks, including links in the historical year indexes."""

    title_pattern = r"Monthly Outlook for Resource Adequacy \(MORA\) .+"

    def percentiles(
        self, *, where: Callable[[MoraPercentile], bool] | None = None
    ) -> Iterator[MoraPercentile]:
        """Query all published percentile tables, retaining report revisions."""
        for file in self.files():
            yield from self.read_percentiles(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def resources(
        self, *, where: Callable[[MoraResource], bool] | None = None
    ) -> Iterator[MoraResource]:
        """Query resource-detail tables, preserving categories and revisions."""
        for file in self.files():
            yield from self.read_resources(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def read_resources(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[MoraResource], bool] | None = None,
    ) -> Iterator[MoraResource]:
        """Read the named B–J resource columns from saved workbooks or ZIPs."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            month, report_label = _report_month(content)
            for sheet, source in _sheets(content, date_columns=(), preserve_types=True):
                if sheet != "Resource Details":
                    continue
                rows = list(source)
                header_index = next(
                    (
                        i
                        for i, r in enumerate(rows)
                        if len(r) > 1 and r[1] == "UNIT NAME"
                    ),
                    None,
                )
                if header_index is None:
                    raise ValueError(f"{member}/{sheet}: Missing resource header")
                header = rows[header_index]
                labels = tuple(" ".join(str(v).split()) for v in header[1:10])
                if (
                    len(labels) != 9
                    or labels[:1] != ("UNIT NAME",)
                    or labels[1] not in ("INR", "INTERCONNECTION REQUEST NUMBER (INR)")
                    or labels[2:6] != ("UNIT CODE", "COUNTY", "FUEL", "ZONE")
                    or labels[6] not in ("IN SERVICE", "IN SERVICE YEAR")
                    or labels[7]
                    not in ("INSTALLED CAPACITY (MW)", "INSTALLED CAPACITY RATING (MW)")
                ):
                    raise ValueError(f"{member}/{sheet}: Unexpected resource columns")
                found = True
                table = [
                    (i + 1, tuple(r[:10]) + (None,) * max(0, 10 - len(r)))
                    for i, r in enumerate(rows)
                    if i > header_index
                ]
                last_data = max(
                    (i for i, r in table if any(v not in (None, "") for v in r[2:10])),
                    default=0,
                )
                notes = [
                    r[1]
                    for i, r in table
                    if i > last_data and isinstance(r[1], str) and r[1]
                ]
                category: str | None = None
                for number, cells in table:
                    if not any(v not in (None, "") for v in cells[2:10]):
                        if isinstance(cells[1], str) and cells[1]:
                            category = cells[1]
                        continue
                    record = MoraResource.model_validate(
                        {
                            "reportMonth": month,
                            "kind": "unit"
                            if any(cells[i] not in (None, "") for i in (2, 4, 6, 7))
                            else "summary",
                            "category": category,
                            "name": cells[1],
                            "interconnectionRequestNumber": cells[2] or None,
                            "unitCode": cells[3] or None,
                            "county": cells[4] or None,
                            "fuel": cells[5] or None,
                            "zone": cells[6] or None,
                            "inService": cells[7] if cells[7] != "" else None,
                            "installedCapacityMW": _number(cells[8]),
                            "reportedCapacityMW": _number(cells[9]),
                            "sourceInstalledCapacityLabel": header[8],
                            "sourceCapacityLabel": header[9],
                            "sourceInServiceLabel": header[7],
                            "sourceReportLabel": report_label,
                            "sourceNotes": notes,
                            "sourceMember": member,
                            "sourceSheet": sheet,
                            "sourceRow": number,
                        }
                    )
                    if where is None or where(record):
                        yield record
        if not found:
            raise ValueError("Download contains no MORA resource tables")

    def capacities(
        self, *, where: Callable[[MoraCapacity], bool] | None = None
    ) -> Iterator[MoraCapacity]:
        """Query category ratings and expected capacity for every published scenario."""
        for file in self.files():
            yield from self.read_capacities(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def read_capacities(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[MoraCapacity], bool] | None = None,
    ) -> Iterator[MoraCapacity]:
        """Read saved MORA XLSX files or ZIPs, retaining indentation-based hierarchy."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member == "workbook.xlsx" else member
            month, report_label = _report_month(content)
            source = _capacity_rows(content)
            notes = [
                str(cells[1])
                for cells, _ in source
                if len(cells) > 1 and str(cells[1]).startswith("[")
            ]
            header = next(
                (
                    i
                    for i, (cells, _) in enumerate(source)
                    if len(cells) > 2 and cells[2] == "Installed Capacity Rating [2]"
                ),
                None,
            )
            if header is None or header == 0:
                raise ValueError(f"{member}: Missing MORA capacity header")
            columns = [
                (i, value)
                for i, value in enumerate(source[header - 1][0])
                if i >= 3 and isinstance(value, str) and value
            ]
            if not columns:
                raise ValueError(f"{member}: Missing MORA capacity scenarios")
            labels = source[header][0]
            section: Literal["operational", "planned", "total"] = "operational"
            section_label = str(labels[1])
            path: list[tuple[float, str]] = []
            for number, (cells, indent) in enumerate(source[header + 1 :], header + 2):
                label = cells[1] if len(cells) > 1 else None
                if not isinstance(label, str) or not label:
                    continue
                if label == "NOTES:":
                    break
                if label.startswith("Planned Resources"):
                    section, section_label = "planned", label
                    path.clear()
                    continue
                if label.startswith("Total Resources"):
                    section, section_label = "total", label
                    path.clear()
                while path and path[-1][0] >= indent:
                    path.pop()
                path.append((indent, label))
                row = MoraCapacity(
                    reportMonth=month,
                    section=section,
                    sourceSectionLabel=section_label,
                    resourcePath=[name for _, name in path],
                    installedCapacityMW=_number(cells[2] if len(cells) > 2 else None),
                    availableCapacity=[
                        _scenario_value(title, cells[i] if i < len(cells) else None)
                        for i, title in columns
                    ],
                    sourceInstalledCapacityLabel=str(labels[2]),
                    sourceAvailableCapacityLabel=str(labels[3])
                    if len(labels) > 3 and labels[3] is not None
                    else None,
                    sourceReportLabel=report_label,
                    sourceNotes=notes,
                    sourceMember=member,
                    sourceSheet="Capacity by Resource Category",
                    sourceRow=number,
                )
                found = True
                if where is None or where(row):
                    yield row
        if not found:
            raise ValueError("Download contains no MORA capacity tables")

    def balance(
        self, *, where: Callable[[MoraBalance], bool] | None = None
    ) -> Iterator[MoraBalance]:
        """Query the monthly load/resource balance for every published scenario."""
        for file in self.files():
            yield from self.read_balance(
                self.download(file), filename=file.url.rsplit("/", 1)[-1], where=where
            )

    def read_balance(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        where: Callable[[MoraBalance], bool] | None = None,
    ) -> Iterator[MoraBalance]:
        """Read saved load/resource balance tables, with source metric labels."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            month, report_label = _report_month(content)
            for sheet, source in _sheets(content, date_columns=()):
                if sheet != "Monthly Outlook":
                    continue
                rows = list(source)
                notes = [
                    value
                    for cells in rows
                    for value in cells
                    if isinstance(value, str) and re.match(r"\[\d+\]", value)
                ]
                columns: list[tuple[int, str]] = []
                for number, cells in enumerate(rows, 1):
                    label = cells[4] if len(cells) > 4 else None
                    if label == "Loads and Resources (MW)":
                        columns = [
                            (i, value)
                            for i, value in enumerate(cells)
                            if i >= 7 and isinstance(value, str) and value
                        ]
                        continue
                    if not columns or not any(
                        i < len(cells) and cells[i] not in (None, "")
                        for i, _ in columns
                    ):
                        continue
                    metric_label = re.sub(r"\s*\[\d+\]$", "", str(label).strip())
                    if metric_label not in _BALANCE_METRICS:
                        raise ValueError(
                            f"{member}/{sheet}: Unknown balance metric {label!r}"
                        )
                    row = MoraBalance(
                        reportMonth=month,
                        metric=_BALANCE_METRICS[metric_label],
                        sourceMetric=str(label),
                        values=[
                            _scenario_value(title, cells[i] if i < len(cells) else None)
                            for i, title in columns
                        ],
                        sourceReportLabel=report_label,
                        sourceNotes=notes,
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=number,
                    )
                    found = True
                    if where is None or where(row):
                        yield row
        if not found:
            raise ValueError("Download contains no MORA balance tables")

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


def _capacity_rows(data: bytes) -> list[tuple[tuple[object, ...], float]]:
    # Indentation distinguishes e.g. Wind/Other from Storage/Other. Reading
    # values alone would lose the source's category hierarchy.
    try:
        from openpyxl import load_workbook
    except ImportError as error:
        raise ImportError("Install tinyercot[files] to read MORA capacities") from error
    book = load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        sheet = cast("ReadOnlyWorksheet", book["Capacity by Resource Category"])
        sheet.reset_dimensions()
        return [
            (
                tuple(cell.value for cell in cells),
                float(cells[1].alignment.indent or 0)
                if len(cells) > 1 and cells[1].alignment
                else 0,
            )
            for cells in sheet.rows
        ]
    finally:
        book.close()


def _scenario_value(label: str, value: object) -> MoraScenarioValue:
    clock = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.m\.", label)
    if clock is None:
        raise ValueError(f"MORA scenario is missing its hour: {label!r}")
    zone: Literal["CST", "CDT"] | None = (
        "CST" if "CST" in label else "CDT" if "CDT" in label else None
    )
    return MoraScenarioValue(
        sourceScenario=label,
        hourEnding=time(
            int(clock[1]) % 12 + (12 if clock[3] == "p" else 0), int(clock[2] or 0)
        ),
        timeZone=zone,
        valueMW=_number(value),
    )


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
