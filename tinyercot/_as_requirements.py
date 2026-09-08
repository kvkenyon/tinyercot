"""Published ancillary-service requirements and their historical revisions."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import _PublicTable

Service = Literal["RegUp", "RegDown", "RRS", "NSRS", "ECRS"]


class _SourceCell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceSheet: str
    sourceRow: int
    sourceColumn: int


class AncillaryServiceQuantity(_SourceCell):
    """Published hourly requirement, or explicitly labelled change, in MW.

    period retains month, partial-month and individual-date labels. These are
    requirement schedules, not quantities actually procured in DAM or RTM.
    """

    service: Service
    kind: Literal["requirement", "change"] = "requirement"
    period: str
    hourEnding: int
    quantityMW: Decimal | None


class ResponsiveReserveAllocation(_SourceCell):
    """RRS components and source ratios; fractions are not multiplied by 100."""

    period: str
    hourEnding: int
    totalRrsMW: Decimal | None
    pfrsMW: Decimal | None
    lrsMW: Decimal | None
    equivalencyRatio: Decimal | None
    fractionFromLrs: Decimal | None = None
    totalEquivalentPfrsMW: Decimal | None = None


class AncillaryServiceAdjustment(_SourceCell):
    """An adjustment in MW with its original basis, applied by the caller."""

    service: Service
    basis: str
    period: str
    hourEnding: int
    adjustmentMW: Decimal | None


class AncillaryServiceSupportingValue(_SourceCell):
    """Published totals or unlabelled worksheet values, with no inferred unit."""

    label: str | None
    value: Decimal


class AncillaryServiceRequirementNote(_SourceCell):
    text: str


class AncillaryServiceRequirements(BaseModel):
    """One workbook revision; effectiveDate comes from its name, not issue time.

    Revisions are never merged or applied automatically. Read notes alongside
    the tables for qualifications, adjustment bases and source spreadsheet errors.
    """

    model_config = ConfigDict(extra="forbid")
    year: int
    effectiveDate: date | None
    sourceMember: str
    quantities: list[AncillaryServiceQuantity] = Field(default_factory=list)
    rrsAllocations: list[ResponsiveReserveAllocation] = Field(default_factory=list)
    adjustments: list[AncillaryServiceAdjustment] = Field(default_factory=list)
    supportingValues: list[AncillaryServiceSupportingValue] = Field(
        default_factory=list
    )
    notes: list[AncillaryServiceRequirementNote] = Field(default_factory=list)


def _service(sheet: str) -> Service:
    name = sheet.lower()
    services: tuple[tuple[str, Service], ...] = (
        ("regulation-up", "RegUp"),
        ("regulation up", "RegUp"),
        ("reg-up", "RegUp"),
        ("regulation-down", "RegDown"),
        ("regulation down", "RegDown"),
        ("rrs", "RRS"),
        ("nsrs", "NSRS"),
        ("ecrs", "ECRS"),
    )
    for text, service in services:
        if text in name:
            return service
    raise ValueError(f"Unknown ancillary service: {sheet}")


def _label(value: object) -> str:
    return value.date().isoformat() if isinstance(value, datetime) else str(value)


_RRS = {
    "Total RRS MW": "totalRrsMW",
    "PFRS": "pfrsMW",
    "LRs": "lrsMW",
    "Equivalency Ratio": "equivalencyRatio",
    "%RRS from LRs": "fractionFromLrs",
    "Total Equivalent PFRs": "totalEquivalentPfrsMW",
}


class AncillaryRequirements(_PublicTable[AncillaryServiceRequirements]):
    """Direct public AS requirement workbooks; requires tinyercot[files]."""

    index_url = "https://www.ercot.com/mktinfo/dam"
    title_pattern = (
        r"Methodology for Determining Minimum Ancillary Service Requirements"
    )

    def _read(
        self, data: bytes, filename: str
    ) -> Iterator[AncillaryServiceRequirements]:
        found = False
        for member, content in _workbooks(data):
            if member == "workbook.xlsx":
                member = filename
            sheets = [
                (name, list(rows)) for name, rows in _sheets(content, date_columns=())
            ]
            year = re.search(
                r"\b20\d{2}\b", member.replace("_", " ") + " " + sheets[0][0]
            )
            if year is None:
                raise ValueError(f"{member}: no requirement year")
            effective = re.search(r"Effective (\d{8}|\d{6})(?!\d)", member)
            effective_date = None
            if effective:
                stamp = effective[1]
                effective_date = date(
                    int(stamp[4:]) + (2000 if len(stamp) == 6 else 0),
                    int(stamp[:2]),
                    int(stamp[2:4]),
                )
            document = AncillaryServiceRequirements(
                year=int(year[0]), effectiveDate=effective_date, sourceMember=member
            )
            for sheet, rows in sheets:
                used: set[tuple[int, int]] = set()
                basis = ""
                service: Service | None = None
                for r, row in enumerate(rows):
                    text = str(row[0] or "") if row else ""
                    if "Incremental MW Adjustment" in text:
                        basis = text
                        service = (
                            _service(sheet) if not sheet.startswith("Reg") else None
                        )
                    if text in ("RegUp", "RegDown"):
                        service = "RegUp" if text == "RegUp" else "RegDown"
                    if text == "Month" and tuple(row[1:25]) == tuple(range(1, 25)):
                        if not basis or service is None:
                            raise ValueError(
                                f"{member}/{sheet}: adjustment basis or service absent"
                            )
                        for i in range(r + 1, r + 13):
                            for c in range(1, 25):
                                document.adjustments.append(
                                    AncillaryServiceAdjustment(
                                        service=service,
                                        basis=basis,
                                        period=_label(rows[i][0]),
                                        hourEnding=c,
                                        adjustmentMW=_number(rows[i][c]),
                                        sourceSheet=sheet,
                                        sourceRow=i + 1,
                                        sourceColumn=c + 1,
                                    )
                                )
                                used.add((i, c))
                            used.add((i, 0))
                        used.update((r, c) for c in range(25))
                    elif "HE" in row:
                        starts = [c for c, value in enumerate(row) if value == "HE"]
                        for start in starts:
                            stop = start + 1
                            while stop < len(row) and row[stop] not in (None, ""):
                                stop += 1
                            headers = row[start + 1 : stop]
                            rrs = str(headers[0]).strip() == "Total RRS MW"
                            for i in range(r + 1, r + 25):
                                hour = int(str(rows[i][start]))
                                if rrs:
                                    fields = {
                                        _RRS[str(header).strip()]: _number(rows[i][c])
                                        for c, header in enumerate(headers, start + 1)
                                    }
                                    document.rrsAllocations.append(
                                        ResponsiveReserveAllocation.model_validate(
                                            dict(
                                                fields,
                                                period=_label(rows[r - 1][start]),
                                                hourEnding=hour,
                                                sourceSheet=sheet,
                                                sourceRow=i + 1,
                                                sourceColumn=start + 1,
                                            )
                                        )
                                    )
                                else:
                                    for c, period in enumerate(headers, start + 1):
                                        document.quantities.append(
                                            AncillaryServiceQuantity(
                                                service=_service(sheet),
                                                kind="change"
                                                if sheet.startswith("Change")
                                                else "requirement",
                                                period=_label(period),
                                                hourEnding=hour,
                                                quantityMW=_number(rows[i][c]),
                                                sourceSheet=sheet,
                                                sourceRow=i + 1,
                                                sourceColumn=c + 1,
                                            )
                                        )
                                used.update((i, c) for c in range(start, stop))
                            used.update((r, c) for c in range(start, stop))
                for r, row in enumerate(rows):
                    for c, value in enumerate(row):
                        if (r, c) not in used and isinstance(value, (int, float)):
                            document.supportingValues.append(
                                AncillaryServiceSupportingValue(
                                    label=row[0] if isinstance(row[0], str) else None,
                                    value=Decimal(str(value)),
                                    sourceSheet=sheet,
                                    sourceRow=r + 1,
                                    sourceColumn=c + 1,
                                )
                            )
                        if (
                            (r, c) not in used
                            and isinstance(value, str)
                            and value.strip()
                        ):
                            document.notes.append(
                                AncillaryServiceRequirementNote(
                                    text=value,
                                    sourceSheet=sheet,
                                    sourceRow=r + 1,
                                    sourceColumn=c + 1,
                                )
                            )
            if not document.quantities and not document.rrsAllocations:
                raise ValueError(f"{member}: no ancillary requirement tables")
            found = True
            yield document
        if not found:
            raise ValueError("Download contains no ancillary requirement workbooks")
