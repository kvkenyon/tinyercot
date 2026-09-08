"""Site metadata and published summaries accompanying planning profiles."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ._load import _sheets, _workbooks


class GenerationProfileKeySite(BaseModel):
    """One original site or unit-code row; identifiers are not inferred or joined."""

    model_config = ConfigDict(extra="forbid")
    siteNumber: int | None = None
    queuedModelFlag: bool | None = None
    unitCode: str | None = None
    commonName: str | None = None
    county: str | None = None
    cdrZone: str | None = None
    capacityMW: Decimal | None = None
    capacityLabel: str | None = None
    plantStatus: str | None = None
    plantStatusLabel: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    xCoordinate: Decimal | None = None
    yCoordinate: Decimal | None = None
    typeCode: int | None = None
    iecClass: int | None = None
    distanceToOperationalOrQueued: str | None = None
    metroArea: str | None = None
    developmentIntensity: str | None = None
    trackingSystem: str | None = None
    trackingType: str | None = None
    tilt: Decimal | Literal["Lat", "NA"] | None = None
    azimuth: Decimal | None = None
    dcAcRatio: Decimal | None = None
    inverters: str | None = None
    modules: str | None = None
    newFor: str | None = None
    newForLabel: str | None = None
    modeledIn: str | None = None
    modeledInLabel: str | None = None
    sourceSheet: str
    sourceRow: int


class GenerationProfileKeySummary(BaseModel):
    """A published count/capacity row, including totals without recomputation."""

    model_config = ConfigDict(extra="forbid")
    section: str
    label: str
    typeCode: int | None = None
    profileCount: int | None = None
    trackingScenarioCount: int | None = None
    trackingType: str | None = None
    totalProfileCount: int | None = None
    capacityMW: Decimal | None = None
    sourceRow: int


class GenerationProfileKey(BaseModel):
    """A key workbook; rows and note locations remain tied to this publication.

    Numeric site numbers are kept as supplied. Matching them to profile column
    names requires the same publication and site family. Queued-model flags use the matching
    worksheet legend; None means no such legend was supplied. Note text and
    original worksheet row numbers are retained.
    """

    model_config = ConfigDict(extra="forbid")
    sourceMember: str
    sourceTitle: str | None = None
    sourceDate: date | None = None
    sites: list[GenerationProfileKeySite] = Field(default_factory=list)
    summaries: list[GenerationProfileKeySummary] = Field(default_factory=list)
    sourceNotes: dict[str, str] = Field(default_factory=dict)


_FIELDS = {
    "UL ID": "siteNumber",
    "SITE ID": "siteNumber",
    "Unit Code": "unitCode",
    "RARF UNIT_CODE": "unitCode",
    "Common Name": "commonName",
    "Common Name of Project": "commonName",
    "County": "county",
    "COUNTY": "county",
    "CDR Zone": "cdrZone",
    "CDR_Zone": "cdrZone",
    "Capacity_MW": "capacityMW",
    "MWAC": "capacityMW",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "XCoord": "xCoordinate",
    "YCoord": "yCoordinate",
    "Type": "typeCode",
    "IEC Class*": "iecClass",
    "Distance to Op/Q'ed": "distanceToOperationalOrQueued",
    "Metro Area": "metroArea",
    "Development Intensity": "developmentIntensity",
    "Tracking System": "trackingSystem",
    "Tracking Type": "trackingType",
    "Tilt": "tilt",
    "Azimuth": "azimuth",
    "DC:AC Ratio": "dcAcRatio",
    "Inverter(s)": "inverters",
    "Module(s)": "modules",
}
_PREFIXES = {
    "New for ": "newFor",
    "Modeled in ": "modeledIn",
    "Modeled Capacity MW ": "capacityMW",
    "Development Status ": "plantStatus",
}


def _field(value: object) -> str | None:
    label = str(value).strip()
    return _FIELDS.get(label) or next(
        (field for prefix, field in _PREFIXES.items() if label.startswith(prefix)), None
    )


def _notes(
    key: GenerationProfileKey, sheet: str, row: int, cells: tuple[object, ...]
) -> None:
    for column, value in enumerate(cells, 1):
        if value is not None:
            key.sourceNotes[f"{sheet}!R{row}C{column}"] = str(value)


def _summary(key: GenerationProfileKey, rows: Iterator[tuple[object, ...]]) -> None:
    section = "SUMMARY"
    for number, cells in enumerate(rows, 1):
        row = (*cells, *(None for _ in range(max(0, 7 - len(cells)))))
        if number == 1:
            key.sourceTitle = str(row[1]) if row[1] is not None else None
        if number == 2 and isinstance(row[1], datetime):
            key.sourceDate = row[1].date()
        if "# of Profiles" in row:
            section = str(row[2])
        elif any(isinstance(cell, (int, float)) for cell in row):
            values: dict[str, object] = {"section": section, "sourceRow": number}
            if isinstance(row[1], (int, float)):
                values.update(
                    typeCode=row[1],
                    label=row[2],
                    profileCount=row[3],
                    trackingScenarioCount=row[4],
                    trackingType=row[5],
                    totalProfileCount=row[6],
                )
            elif row[1] is not None and str(row[1]).strip() == "Total":
                values.update(label=row[1], totalProfileCount=row[6])
            else:
                values.update(label=row[2], profileCount=row[3], capacityMW=row[4])
            key.summaries.append(GenerationProfileKeySummary.model_validate(values))
        else:
            _notes(key, "SUMMARY", number, cells)


def _queued_flags(data: bytes, key: GenerationProfileKey) -> None:
    from openpyxl import load_workbook

    book = load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        for sheet in book:
            cells = list(sheet.rows)
            legend = next(
                (
                    cell
                    for row in cells
                    for cell in row
                    if cell.value
                    == "Modeled as a Queued Plant (< 1 yr of observed generation)."
                ),
                None,
            )
            if legend is None:
                continue
            column = next(i for i, cell in enumerate(cells[0]) if cell.value == "UL ID")
            for site in key.sites:
                if site.sourceSheet == sheet.title:
                    fill = cells[site.sourceRow - 1][column].fill
                    site.queuedModelFlag = (
                        fill.patternType == legend.fill.patternType
                        and fill.fgColor == legend.fill.fgColor
                    )
    finally:
        book.close()


def read_keys(data: bytes, filename: str) -> Iterator[GenerationProfileKey]:
    found = False
    for member, content in _workbooks(data):
        key = GenerationProfileKey(
            sourceMember=filename if member == "workbook.xlsx" else member
        )
        for sheet, rows in _sheets(content, date_columns=()):
            if sheet == "SUMMARY":
                _summary(key, rows)
                continue
            columns: dict[int, str] = {}
            labels: dict[str, str] = {}
            for number, row in enumerate(rows, 1):
                if any(value in ("UL ID", "SITE ID", "Unit Code") for value in row):
                    columns = {
                        i: field
                        for i, cell in enumerate(row)
                        if (field := _field(cell)) is not None
                    }
                    labels = {
                        field.removesuffix("MW") + "Label": str(row[i]).strip()
                        for i, field in columns.items()
                        if field in {"capacityMW", "plantStatus", "newFor", "modeledIn"}
                    }
                    _notes(
                        key,
                        sheet,
                        number,
                        tuple(
                            None if i in columns else value
                            for i, value in enumerate(row)
                        ),
                    )
                    continue
                values = {
                    field: row[i]
                    for i, field in columns.items()
                    if i < len(row) and row[i] not in (None, "")
                }
                if len(values) > 1 and ("siteNumber" in values or "unitCode" in values):
                    key.sites.append(
                        GenerationProfileKeySite.model_validate(
                            dict(values, **labels, sourceSheet=sheet, sourceRow=number)
                        )
                    )
                    _notes(
                        key,
                        sheet,
                        number,
                        tuple(
                            None if i in columns else value
                            for i, value in enumerate(row)
                        ),
                    )
                else:
                    _notes(key, sheet, number, row)
        if not key.sites:
            raise ValueError(
                f"{key.sourceMember}: no supported profile key site tables"
            )
        _queued_flags(content, key)
        found = True
        yield key
    if not found:
        raise ValueError(f"{filename}: no profile key workbook found")
