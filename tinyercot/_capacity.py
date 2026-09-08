"""Project and capacity histories from ERCOT's public resource workbooks."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from time import strptime
from typing import Literal
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import PublicFile, _ResourceFiles

_PROJECT_FIELDS = {
    "Project Name": "name",
    "County": "county",
    "Projected COD": "projectedCOD",
    "IA Signed": "interconnectionAgreementSigned",
    "Approved for Synchronization": "approvedForSynchronization",
    "Fuel": "fuel",
    "Technology": "technology",
    "Capacity (MW)": "capacityMW",
    "Year": "reportedYear",
    "Financial Security": "financialSecurity",
    "Comments": "comments",
}
_TOTAL_FIELDS = {
    "cumulative installed, no fs, and fs posted": "cumulativeInstalledAndSignedMW",
    "cumulative operational, no fs, and fs posted": "cumulativeOperationalAndSignedMW",
    "cumulative total mw": "cumulativeTotalMW",
    "cumulative mw installed": "cumulativeInstalledMW",
    "cumulative mw synchronized": "cumulativeSynchronizedMW",
    "operational": "operationalMW",
    "cumulative mw operational": "cumulativeOperationalMW",
    "ia signed-financial security posted": "financialSecurityPostedMW",
    "ia signed-no financial security": "noFinancialSecurityMW",
    "other planned": "otherPlannedMW",
    "dgr": "distributedGenerationMW",
    "small generator": "smallGeneratorsMW",
    "dgr comments": "dgrComments",
}
_GROUPS = {"Small Generators", "Small Generator", "DGRs"}


class _CapacityRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reportMonth: date | None
    sourceFile: PublicFile | None
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceColumns: list[str]
    sourceNotes: list[str]


class CapacityProject(_CapacityRow):
    """A reported project, retaining its projected dates and original identifier.

    Identifiers can be INRs or resource codes. A projected COD, agreement or
    synchronization approval does not establish commercial operation.
    """

    identifier: str
    sourceGroup: str | None
    name: str
    county: str
    projectedCOD: date
    interconnectionAgreementSigned: date | str | None
    approvedForSynchronization: date | None = None
    fuel: str | None
    technology: str
    capacityMW: Decimal
    reportedYear: int
    financialSecurity: Literal["Yes", "No"] | None
    comments: str | None = None


class CapacityTotals(_CapacityRow):
    """A published year or monthly point, with source measures kept separate.

    period retains the source year or full date, including a mid-month day.
    Missing columns and blank cells remain None; sourceColumns distinguishes them.
    """

    period: int | date
    sourcePeriodLabel: Literal["Year", "Month/Year"]
    cumulativeInstalledAndSignedMW: Decimal | None = None
    cumulativeOperationalAndSignedMW: Decimal | None = None
    cumulativeTotalMW: Decimal | None = None
    cumulativeInstalledMW: Decimal | None = None
    cumulativeSynchronizedMW: Decimal | None = None
    operationalMW: Decimal | None = None
    cumulativeOperationalMW: Decimal | None = None
    financialSecurityPostedMW: Decimal | None = None
    noFinancialSecurityMW: Decimal | None = None
    otherPlannedMW: Decimal | None = None
    distributedGenerationMW: Decimal | None = None
    smallGeneratorsMW: Decimal | None = None
    dgrComments: str | None = None


class CapacityChanges(_ResourceFiles):
    title_pattern = r"(?i)(?:Monthly )?Capacity Changes by Fuel Type Charts.*"

    def projects(
        self, *, where: Callable[[CapacityProject], bool] | None = None
    ) -> Iterator[CapacityProject]:
        """Query all project vintages, retaining companion files and corrections."""
        for file in self.files():
            yield from self.read_projects(
                self.download(file), source_file=file, where=where
            )

    def read_projects(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[CapacityProject], bool] | None = None,
    ) -> Iterator[CapacityProject]:
        """Read saved workbooks/ZIPs; source_file preserves the original URL/vintage."""
        for member, month, notes, sheet, rows in _tables(data, filename, source_file):
            header = next((r.index("INR") for r in rows if "INR" in r), None)
            if header is None:
                continue
            labels: list[str] = []
            group: str | None = None
            for number, cells in enumerate(rows, 1):
                right = cells[header:]
                if len(right) > 1 and right[1] == "Project Name":
                    labels = [str(v) for v in right if v is not None]
                    if labels[0] in _GROUPS:
                        group = labels[0]
                    unknown = set(labels[1:]) - _PROJECT_FIELDS.keys()
                    if unknown:
                        raise ValueError(
                            f"{member}/{sheet}: Unknown project columns {unknown}"
                        )
                    continue
                if not labels or not right or right[0] is None:
                    continue
                if not any(v not in (None, "") for v in right[1:]):
                    if right[0] in _GROUPS:
                        group = str(right[0])
                    continue
                fields = {
                    _PROJECT_FIELDS[label]: right[i] if i < len(right) else None
                    for i, label in enumerate(labels)
                    if i
                }
                fields["capacityMW"] = _number(fields["capacityMW"])
                row = CapacityProject.model_validate(
                    dict(
                        fields,
                        identifier=right[0],
                        sourceGroup=group,
                        reportMonth=month,
                        sourceFile=source_file,
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=number,
                        sourceColumns=labels,
                        sourceNotes=notes,
                    )
                )
                if where is None or where(row):
                    yield row

    def totals(
        self, *, where: Callable[[CapacityTotals], bool] | None = None
    ) -> Iterator[CapacityTotals]:
        """Query annual/monthly capacity series without combining their definitions."""
        for file in self.files():
            yield from self.read_totals(
                self.download(file), source_file=file, where=where
            )

    def read_totals(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[CapacityTotals], bool] | None = None,
    ) -> Iterator[CapacityTotals]:
        """Read saved annual/monthly source points, including original period dates."""
        for member, month, notes, sheet, rows in _tables(data, filename, source_file):
            columns: list[tuple[int, str, str]] = []
            project_start = next((r.index("INR") for r in rows if "INR" in r), None)
            period_label = ""
            for number, cells in enumerate(rows, 1):
                if cells and cells[0] in ("Year", "Month/Year"):
                    period_label = str(cells[0])
                    columns = []
                    for i, value in enumerate(cells[1:project_start], 1):
                        if value is None:
                            continue
                        label = str(value)
                        key = label.strip().lower()
                        if key not in _TOTAL_FIELDS:
                            raise ValueError(
                                f"{member}/{sheet}: Unknown capacity column {label!r}"
                            )
                        columns.append((i, label, _TOTAL_FIELDS[key]))
                    continue
                if not columns or not cells or cells[0] is None:
                    continue
                fields = {
                    field: (cells[i] if i < len(cells) else None)
                    if field == "dgrComments"
                    else _number(cells[i] if i < len(cells) else None)
                    for i, _, field in columns
                }
                row = CapacityTotals.model_validate(
                    dict(
                        fields,
                        period=cells[0],
                        sourcePeriodLabel=period_label,
                        reportMonth=month,
                        sourceFile=source_file,
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceRow=number,
                        sourceColumns=[period_label]
                        + [label for _, label, _ in columns],
                        sourceNotes=notes,
                    )
                )
                if where is None or where(row):
                    yield row


def _tables(
    data: bytes,
    filename: str,
    source_file: PublicFile | None,
) -> Iterator[tuple[str, date | None, list[str], str, list[tuple[object, ...]]]]:
    found = False
    for member, content in _workbooks(data):
        if member in {"workbook.xls", "workbook.xlsx"}:
            member = (
                unquote(source_file.url.rsplit("/", 1)[-1]) if source_file else filename
            )
        month_label = unquote(member)
        month = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)[ _-]+(\d{4})",
            month_label,
            re.IGNORECASE,
        )
        report_month = (
            date(*strptime(f"{month[1]} {month[2]}", "%B %Y")[:3]) if month else None
        )
        sheets = [
            (s, list(r))
            for s, r in _sheets(content, date_columns=(), preserve_types=True)
        ]
        corrections = [
            value
            for sheet, rows in sheets
            if sheet == "Correction Info"
            for cells in rows
            for value in cells
            if isinstance(value, str) and value != "Correction Description:"
        ]
        for sheet, rows in sheets:
            if sheet == "Correction Info":
                continue
            header = next((r.index("INR") for r in rows if "INR" in r), None)
            if header is None and not any(
                r and r[0] in ("Year", "Month/Year") for r in rows
            ):
                continue
            notes = corrections + [
                str(cells[header])
                for cells in rows
                if header is not None
                and len(cells) > header
                and isinstance(cells[header], str)
                and cells[header] not in _GROUPS
                and not any(v not in (None, "") for v in cells[header + 1 :])
            ]
            found = True
            yield member, report_month, notes, sheet, rows
    if not found:
        raise ValueError("Download contains no capacity-change tables")
