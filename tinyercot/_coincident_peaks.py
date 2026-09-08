"""Four-coincident-peak loads and allocations from the public historical archive."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime, time
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


class PeakSettlementRun(BaseModel):
    """Published settlement-run metadata; an invalid source date remains visible."""

    model_config = ConfigDict(extra="forbid")
    runDate: date | None
    runTime: time | None
    sourceDate: str
    channel: int | None
    kind: Literal["FINAL", "INTERIM", "TRUE-UP"] | None


class MonthlyCoincidentPeak(BaseModel):
    """One monthly peak-load record, retaining submitted and settled quantities.

    loadType identifies what load measures; unit applies only to that value.
    Relative differences retain the original dimensionless cell values. The SIS
    report column has no explicit unit in these sources and is not rescaled.
    Total rows are retained; an unlabeled source total has entity=None.
    """

    model_config = ConfigDict(extra="forbid")
    timestamp: datetime
    entity: str | None
    entityCode: str | None
    duns: str | None
    controlArea: str | None
    loadType: Literal["submitted", "coincident_peak", "load_responsibility"]
    load: Decimal | None
    unit: Literal["kW", "MW"]
    energyMWh: Decimal | None = None
    gsuLossesKW: Decimal | None = None
    transmissionLossesKW: Decimal | None = None
    controlAreaTotalKW: Decimal | None = None
    demandReportMW: Decimal | None = None
    demandReportDifferenceMW: Decimal | None = None
    demandReportRelativeDifference: Decimal | None = None
    sisLoadReport: Decimal | None = None
    sisDifferenceMW: Decimal | None = None
    sisRelativeDifference: Decimal | None = None
    lossAdjustmentPercent: Decimal | None = None
    loadAtDeliveryPointKW: Decimal | None = None
    vamoLossPercent: Decimal | None = None
    loadResponsibilityKW: Decimal | None = None
    settlementRun: PeakSettlementRun | None
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceHeading: str
    sourceHeaders: list[str]
    sourceNotes: list[str]
    sourceRowNote: str | None


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

    def monthly(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        entity: str | None = None,
    ) -> Iterator[MonthlyCoincidentPeak]:
        """Stream monthly peak tables with inclusive peak dates and exact entity.

        Revisions and repeated publications remain separate. Source worksheet
        names are not used to infer the peak month or the settlement-run date.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        yield from self.read_monthly(
            self.download(), date_from=date_from, date_to=date_to, entity=entity
        )

    def read_monthly(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        date_from: date | None = None,
        date_to: date | None = None,
        entity: str | None = None,
    ) -> Iterator[MonthlyCoincidentPeak]:
        """Decode saved monthly peak-load reports with tinyercot[files].

        Blank cells and the source's dash placeholders become None, not zero.
        Annual allocations use read_allocations().
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                heading: str | None = None
                header: tuple[str, ...] | None = None
                columns: dict[str, int] = {}
                notes: list[str] = []
                pending: list[str] = []
                batch: list[dict[str, object]] = []
                for row_number, cells in enumerate(rows, 1):
                    labels = tuple(_text(c) or "" for c in cells)
                    new_heading = next(
                        (
                            c
                            for c in labels
                            if re.match(
                                r"(?:Integrated Peak Hour Demand|Peak Interval Demand|Peak Demand on)\b",
                                c,
                                re.IGNORECASE,
                            )
                        ),
                        None,
                    )
                    if new_heading:
                        if heading is not None and header is None:
                            raise ValueError(
                                f"{member}/{sheet}: Missing monthly peak columns"
                            )
                        yield from _monthly_rows(batch, notes)
                        batch = []
                        heading, header = new_heading, None
                        notes, pending = pending, []
                        continue
                    if _header(labels) is not None:
                        yield from _monthly_rows(batch, notes)
                        batch = []
                        heading, header = None, None
                        continue
                    mapping = _monthly_columns(labels) if heading else None
                    if mapping and heading is not None:
                        header, columns = labels, mapping
                        stamp = _peak_clock(heading)
                        run = _settlement_run(heading)
                        load_type = (
                            "submitted"
                            if "gsuLossesKW" in columns
                            else "coincident_peak"
                            if "lossAdjustmentPercent" in columns
                            else "load_responsibility"
                        )
                        unit = "MW" if "energyMWh" in columns else "kW"
                        found = True
                        continue
                    if header is None:
                        if any(labels) and not any(
                            isinstance(c, (int, float)) for c in cells
                        ):
                            (notes if heading else pending).append(
                                " | ".join(c for c in labels if c)
                            )
                        continue
                    names = (
                        0 if columns["load"] == 2 and load_type == "submitted" else 1
                    )
                    name = _text(cells[names]) if len(cells) > names else None
                    if unit == "MW" and cells and cells[0] == "Total":
                        name = "Total"
                    numbers = [cells[i] for i in columns.values() if i < len(cells)]
                    unnamed_total = (
                        name is None
                        and columns["load"] < len(cells)
                        and isinstance(cells[columns["load"]], (int, float, Decimal))
                    )
                    if (not name and not unnamed_total) or not any(
                        isinstance(v, (int, float, Decimal)) or v == "-"
                        for v in numbers
                    ):
                        if any(labels) and not any(
                            isinstance(c, (int, float)) for c in cells
                        ):
                            note = " | ".join(c for c in labels if c)
                            (notes if note.startswith("*Note") else pending).append(
                                note
                            )
                        continue
                    if len(cells) <= max(columns.values()):
                        raise ValueError(
                            f"{member}/{sheet}: Truncated monthly peak row"
                        )
                    if (
                        (date_from and stamp.date() < date_from)
                        or (date_to and stamp.date() > date_to)
                        or (entity is not None and name != entity)
                    ):
                        continue
                    payload: dict[str, object] = {
                        key: None
                        if cells[i] == "-" or (name == "Total" and cells[i] == "Total")
                        else _number(cells[i])
                        for key, i in columns.items()
                    }
                    payload.update(
                        timestamp=stamp,
                        entity=name,
                        entityCode=_text(cells[0])
                        if names == 1 and cells[0] != "Total"
                        else None,
                        duns=_text(cells[2]) if unit == "MW" else None,
                        controlArea=_text(cells[names + 1])
                        if load_type == "submitted"
                        else None,
                        loadType=load_type,
                        unit=unit,
                        settlementRun=run,
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=row_number,
                        sourceHeading=heading,
                        sourceHeaders=list(header),
                        sourceRowNote=_text(cells[10])
                        if "sisLoadReport" in columns
                        else None,
                    )
                    batch.append(payload)
                if heading is not None and header is None:
                    raise ValueError(f"{member}/{sheet}: Missing monthly peak columns")
                yield from _monthly_rows(batch, notes)
        if not found:
            raise ValueError("Download contains no monthly peak-load tables")


def _monthly_rows(
    rows: list[dict[str, object]], notes: list[str]
) -> Iterator[MonthlyCoincidentPeak]:
    for row in rows:
        yield MonthlyCoincidentPeak.model_validate({**row, "sourceNotes": notes})


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


def _monthly_columns(header: tuple[str, ...]) -> dict[str, int] | None:
    submitted = "Submitted Load kW (does not include GSU losses)"
    if submitted in header:
        start = header.index(submitted)
        if start not in (2, 3):
            raise ValueError("Unsupported submitted-load columns")
        fields = (
            "load",
            "gsuLossesKW",
            "transmissionLossesKW",
            "controlAreaTotalKW",
            "demandReportMW",
            "demandReportDifferenceMW",
            "demandReportRelativeDifference",
        )
        mapping = dict(zip(fields, range(start, start + 7), strict=True))
        if start == 3:
            mapping.update(
                sisLoadReport=11, sisDifferenceMW=12, sisRelativeDifference=13
            )
        return mapping
    if (
        len(header) > 4
        and header[0].upper() == "TDSP CODE"
        and re.fullmatch(r"\d{4} Load Responsibility MW", header[3])
        and header[4].endswith("Load Responsibility MWh")
    ):
        return {"load": 3, "energyMWh": 4}
    if len(header) > 2 and header[0] in {"Load Entity Acronym", "LSE Acronym"}:
        if re.fullmatch(r"\d{4} Load Responsibility kW", header[2]):
            return {"load": 2}
        if any(header[2].startswith(m) for m in _MONTHS) and header[2].endswith(
            "Load at ERCOT Coincident Peak kW"
        ):
            return {
                "load": 2,
                "lossAdjustmentPercent": 3,
                "loadAtDeliveryPointKW": 4,
                "vamoLossPercent": 5,
                "loadResponsibilityKW": 6,
            }
    return None


def _report_date(value: str) -> date | None:
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})", value):
        return None
    try:
        return datetime.strptime(  # noqa: DTZ007 -- source date only
            value, "%m/%d/%Y" if len(value.rsplit("/", 1)[-1]) == 4 else "%m/%d/%y"
        ).date()
    except ValueError:
        return None


def _peak_clock(heading: str) -> datetime:
    match = re.search(
        r"(\d{1,2}/\d{1,2}/\d{2,4})(?: at interval ending)? (\d{1,2}):(\d{2})",
        heading,
        re.IGNORECASE,
    )
    day = _report_date(match[1]) if match else None
    if match is None or day is None:
        raise ValueError(f"Unsupported monthly peak clock: {heading}")
    return datetime.combine(day, time(int(match[2]), int(match[3])))


def _settlement_run(heading: str) -> PeakSettlementRun | None:
    match = re.search(
        r"based on (.*?) settlement run on (\S+)(?: at (\d{1,2}):(\d{2}))?",
        heading,
        re.IGNORECASE,
    )
    if match is None:
        return None
    channel = re.search(r"Channel (\d+)", match[1], re.IGNORECASE)
    kind = re.search(r"FINAL|INTERIM|TRUE-UP", match[1], re.IGNORECASE)
    return PeakSettlementRun.model_validate(
        {
            "runDate": _report_date(match[2]),
            "runTime": time(int(match[3]), int(match[4])) if match[3] else None,
            "sourceDate": match[2],
            "channel": int(channel[1]) if channel else None,
            "kind": kind[0].upper() if kind else None,
        }
    )
