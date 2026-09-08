"""Typed parameters from ERCOT's annual distribution-loss summaries."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from time import strptime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import PublicFile, _PublicFiles


class DistributionLossCoefficient(BaseModel):
    """One DSP/code's published formula parameters and ERCOT load baseline.

    year is a filename label, not an effective-date or publication guarantee.
    Baseline dates describe the load inputs, not the coefficient's effective
    period. Source titles and formula text remain attached, including conflicts.
    Parameters and cached baseline values are never recalculated or applied.
    """

    model_config = ConfigDict(extra="forbid")
    year: int | None
    tdsp: str
    lossCode: str
    formula: Literal["k_adlf", "f1_f2_f3"]
    f1: Decimal | None = None
    f2: Decimal | None = None
    f3: Decimal | None = None
    tdspAverageIntervalLoadMWh: Decimal | None = None
    kFactor: Decimal | None = None
    annualDistributionLossFactor: Decimal | None = None
    ercotAnnualEnergyMWh: Decimal | None
    ercotIntervalCount: int | None
    ercotAverageIntervalLoadMWh: Decimal | None
    ercotPeakLoadMW: Decimal | None
    baselineFrom: date | None
    baselineThrough: date | None
    sourceBaselinePeriod: str
    sourceWorkbookTitle: str | None
    sourceFormula: str
    sourceMember: str
    sourceSheet: str
    sourceColumn: int
    sourceFile: PublicFile | None = None


class DistributionLossCoefficients(_PublicFiles):
    """Read summary workbooks in the public methodology bundles with [files]."""

    index_url = "https://www.ercot.com/mktinfo/metering/dlfmethodology"
    title_pattern = r"\d{4}.*TDSP Distribution Los[st] Factors.*Methodology.*"

    def rows(
        self, *, where: Callable[[DistributionLossCoefficient], bool] | None = None
    ) -> Iterator[DistributionLossCoefficient]:
        for file in self.files():
            yield from self.read(self.download(file), source_file=file, where=where)

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[DistributionLossCoefficient], bool] | None = None,
    ) -> Iterator[DistributionLossCoefficient]:
        """Read individual summaries or original ZIPs; preserve period variants."""
        found = False
        for member, content in _workbooks(data):
            if member in {"workbook.xls", "workbook.xlsx"}:
                member = filename
            elif not re.search(
                r"(?:^|/)ERCOT.*DLF.*Summary[^/]*\.xlsx?$", member, re.IGNORECASE
            ):
                continue
            tables = {
                name: list(rows)
                for name, rows in _sheets(content, date_columns=(), preserve_types=True)
            }
            for sheet, rows in tables.items():
                if sheet != "TDSP and ERCOT Variables":
                    continue
                found = True
                start = tables.get("Start", [])
                for record in _parameters(rows, start, member, sheet, source_file):
                    if where is None or where(record):
                        yield record
        if not found:
            raise ValueError("Download contains no distribution-loss summary tables")


def _baseline_period(label: str) -> tuple[date | None, date | None]:
    if match := re.fullmatch(r"Year (\d{4})", label.strip()):
        return date(int(match[1]), 1, 1), date(int(match[1]), 12, 31)
    try:
        left, right = label.replace("Sept ", "September ").split(" to ")
        start = date(*strptime(left.strip(), "%B %d, %Y")[:3])
        end = date(*strptime(right.strip(), "%B %d, %Y")[:3])
        if start <= end:
            return start, end
    except ValueError:
        pass
    return None, None


def _parameters(
    rows: list[tuple[object, ...]],
    start: list[tuple[object, ...]],
    member: str,
    sheet: str,
    source_file: PublicFile | None,
) -> Iterator[DistributionLossCoefficient]:
    column = rows[0].index("DSP =")
    if rows[1][column] != "DLF Code =":
        raise ValueError(f"{member}/{sheet}: Missing DLF codes")
    labels = tuple(str(row[column]).strip() for row in rows[2:5])
    fields: tuple[str, str, str]
    family: Literal["k_adlf", "f1_f2_f3"]
    if labels == ("F1 =", "F2 =", "F3 ="):
        fields, family = ("f1", "f2", "f3"), "f1_f2_f3"
    elif labels[0] in {"TDSP AAL (MWH) =", "DSP AAL (MWh) ="} and labels[1:] == (
        "K factor =",
        "ADLF =",
    ):
        fields, family = (
            ("tdspAverageIntervalLoadMWh", "kFactor", "annualDistributionLossFactor"),
            "k_adlf",
        )
    else:
        raise ValueError(f"{member}/{sheet}: Unknown distribution-loss formula columns")
    base = rows[0].index("ERCOT")
    period = str(rows[1][base])
    first, last = _baseline_period(period)
    baseline = {str(row[base]).strip().upper(): row[base + 1] for row in rows[:6]}
    notes = [cell for row in start for cell in row if isinstance(cell, str)]
    title = next(
        (t for t in notes if t.startswith("ERCOT Distribution Loss Factor")), None
    )
    formula = next(t for t in notes if t.startswith("SILF"))
    year = re.search(r"\d{4}", member.rsplit("/", 1)[-1])
    for i in range(column + 1, len(rows[0])):
        if rows[0][i] in (None, ""):
            continue
        yield DistributionLossCoefficient.model_validate(
            {
                "year": int(year[0]) if year else None,
                "tdsp": rows[0][i],
                "lossCode": rows[1][i],
                "formula": family,
                **{field: _number(rows[j][i]) for j, field in enumerate(fields, 2)},
                "ercotAnnualEnergyMWh": _number(baseline["ANNUAL MWH"]),
                "ercotIntervalCount": baseline["INTERVAL COUNT"],
                "ercotAverageIntervalLoadMWh": _number(baseline["ERCOT AAL"]),
                "ercotPeakLoadMW": _number(baseline.get("ERCOT PEAK MW")),
                "baselineFrom": first,
                "baselineThrough": last,
                "sourceBaselinePeriod": period,
                "sourceWorkbookTitle": title,
                "sourceFormula": formula,
                "sourceMember": member,
                "sourceSheet": sheet,
                "sourceColumn": i + 1,
                "sourceFile": source_file,
            }
        )
