"""Annual four-coincident-peak allocations from the public historical archive."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks

URL = "https://www.ercot.com/files/docs/2022/01/13/1996-2020_FourCoincidentPeakCalculations.zip"
_MONTHS = ("June", "July", "August", "September")


class CoincidentPeak(BaseModel):
    """A monthly source load and its published peak clock, when present.

    Clocks have no inferred UTC offset. The parent allocation supplies the unit.
    """

    model_config = ConfigDict(extra="forbid")
    month: int
    load: Decimal | None
    timestamp: datetime | None
    sourceHeader: str


class CoincidentPeakAllocation(BaseModel):
    """One annual allocation, retaining source revisions, units and identities.

    Ratios and adjustment factors retain their original scale. Original headers
    preserve whether ERCOT labels them as a share, factor, or percent.
    """

    model_config = ConfigDict(extra="forbid")
    year: int
    kind: Literal["allocation", "comparison", "revision_detail"]
    entity: str
    entityCode: str | None
    duns: str | None
    controlArea: str | None
    unit: Literal["kW", "MW"]
    peaks: list[CoincidentPeak]
    averageLoad: Decimal | None
    loadRatioShare: Decimal | None
    adjustmentUnit: Literal["factor", "percent"] | None
    gsuLosses: Decimal | None = None
    netGeneration: Decimal | None = None
    lossAdjustmentFactor: Decimal | None = None
    loadAtDeliveryPoint: Decimal | None = None
    vamoLossAllocation: Decimal | None = None
    loadResponsibility: Decimal | None = None
    oldLoadRatioShare: Decimal | None = None
    loadRatioShareDifference: Decimal | None = None
    sourceMember: str
    sourceSheet: str
    sourceSection: str | None
    sourceHeaders: list[str]
    sourceNotes: list[str]


class CoincidentPeaks:
    """Public historical 4CP files, independently of MIS and API credentials."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def download(self) -> bytes:
        """Download the original 1996–2020 archive, including nested yearly ZIPs."""
        response = self._http.get(URL, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def allocations(
        self,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
        entity: str | None = None,
    ) -> Iterator[CoincidentPeakAllocation]:
        """Stream annual allocation tables, preserving all published revisions.

        Year bounds are inclusive; entity matches the exact source name. Monthly
        preliminary reports and supporting calculation sheets are separate data.
        """
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not be after year_to")
        yield from self.read_allocations(
            self.download(),
            year_from=year_from,
            year_to=year_to,
            entity=entity,
        )

    def read_allocations(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        year_from: int | None = None,
        year_to: int | None = None,
        entity: str | None = None,
    ) -> Iterator[CoincidentPeakAllocation]:
        """Read annual allocations from saved ZIP/XLS/XLSX with tinyercot[files]."""
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not be after year_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                notes: list[str] = []
                header: tuple[str, ...] | None = None
                year = 0
                start = 0
                for cells in rows:
                    labels = tuple(_text(c) or "" for c in cells)
                    candidate = _header(labels)
                    if candidate is not None:
                        header, start = labels, candidate
                        match = re.search(
                            r"(?:19|20)\d{2}",
                            sheet
                            + " "
                            + " ".join(header)
                            + " "
                            + " ".join(notes)
                            + " "
                            + member.rsplit("/", 1)[-1],
                        )
                        if match is None:
                            raise ValueError(
                                f"{member}/{sheet}: Missing allocation year"
                            )
                        year = int(match[0])
                        found = True
                        continue
                    if not any(c not in (None, "") for c in cells):
                        continue
                    summary = start == -1
                    entity_index = 0 if start in (-1, 11) else 1
                    name = (
                        _text(cells[entity_index])
                        if len(cells) > entity_index
                        else None
                    )
                    loads = cells[2:3] if summary else cells[start : start + 5]
                    if (
                        header is None
                        or not name
                        or len(cells) <= (7 if summary else start + 4)
                        or not any(
                            isinstance(value, (int, float, Decimal)) for value in loads
                        )
                    ):
                        if any(
                            isinstance(c, str) and c.strip() for c in cells
                        ) and not any(
                            isinstance(c, (int, float, Decimal)) for c in cells
                        ):
                            notes.append(
                                " | ".join(str(c) for c in cells if c not in (None, ""))
                            )
                        continue
                    if (
                        (year_from is not None and year < year_from)
                        or (year_to is not None and year > year_to)
                        or (entity is not None and name != entity)
                    ):
                        continue
                    legacy = start == 11
                    adjusted = (
                        not legacy
                        and len(header) > 11
                        and "Loss Adjustment" in header[7]
                    )
                    unit: Literal["kW", "MW"] = (
                        "kW" if legacy or any("kW" in h for h in header) else "MW"
                    )
                    share = (
                        7 if summary else 8 if legacy else 11 if adjusted else start + 5
                    )
                    values: dict[str, object] = {
                        "year": year,
                        "kind": "comparison"
                        if sheet == "Comparison"
                        else "revision_detail"
                        if sheet == "Revision_Details"
                        else "allocation",
                        "entity": name,
                        "entityCode": None if legacy or summary else _text(cells[0]),
                        "duns": _text(cells[2]) if start == 3 else None,
                        "controlArea": _text(cells[1])
                        if summary
                        else _text(cells[12])
                        if adjusted and header[12] == "CA Acronym"
                        else None,
                        "unit": unit,
                        "adjustmentUnit": "factor"
                        if legacy
                        else "percent"
                        if adjusted or summary
                        else None,
                        "peaks": []
                        if summary
                        else [
                            CoincidentPeak(
                                month=i + 6,
                                load=_number(cells[start + i]),
                                timestamp=_clock(header[start + i]),
                                sourceHeader=header[start + i],
                            )
                            for i in range(4)
                        ],
                        "averageLoad": _number(
                            cells[2]
                            if summary
                            else cells[1]
                            if legacy
                            else cells[start + 4]
                        ),
                        "loadRatioShare": _number(cells[share])
                        if len(cells) > share
                        else None,
                        "sourceMember": member,
                        "sourceSheet": sheet,
                        "sourceSection": notes[-1] if notes else None,
                        "sourceHeaders": list(header),
                        "sourceNotes": list(notes),
                    }
                    if legacy:
                        for field, column in zip(
                            (
                                "gsuLosses",
                                "netGeneration",
                                "lossAdjustmentFactor",
                                "loadAtDeliveryPoint",
                                "vamoLossAllocation",
                                "loadResponsibility",
                            ),
                            range(2, 8),
                            strict=True,
                        ):
                            values[field] = _number(cells[column])
                    elif adjusted or summary:
                        for field, column in zip(
                            (
                                "lossAdjustmentFactor",
                                "loadAtDeliveryPoint",
                                "vamoLossAllocation",
                                "loadResponsibility",
                            ),
                            range(3, 7) if summary else range(7, 11),
                            strict=True,
                        ):
                            values[field] = _number(cells[column])
                    for label, field in (
                        ("Old Load Ratio Share", "oldLoadRatioShare"),
                        ("DIFFERENCES", "loadRatioShareDifference"),
                    ):
                        if label in header:
                            values[field] = _number(cells[header.index(label)])
                    yield CoincidentPeakAllocation.model_validate(values)
        if not found:
            raise ValueError("Download contains no annual 4CP allocation tables")


def _text(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return " ".join(str(value).split())


def _header(cells: tuple[str, ...]) -> int | None:
    if cells[:3] == ("Load Entity", "Control Area", "Average 4CP Load kW"):
        return -1
    for start in (2, 3, 11):
        if (
            len(cells) > start + 4
            and all(
                cells[start + i].startswith(month) for i, month in enumerate(_MONTHS)
            )
            and (
                "Average 4CP Load" in cells[start + 4]
                or cells[start + 4] == "4CP Average"
            )
        ):
            return start
    return None


def _clock(header: str) -> datetime | None:
    match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})", header)
    if match:
        return datetime.strptime(" ".join(match.groups()), "%m/%d/%Y %H:%M")  # noqa: DTZ007 -- source has no offset
    match = re.fullmatch(r"(\w+ \d{1,2}, \d{4}) @(\d{4})", header)
    if match:
        return datetime.strptime(" ".join(match.groups()), "%B %d, %Y %H%M")  # noqa: DTZ007 -- source has no offset
    return None
