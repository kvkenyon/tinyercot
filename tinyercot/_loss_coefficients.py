"""Published seasonal transmission-loss coefficients and their input basis."""

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
from ._public_tables import PublicFile, _PublicFiles, _year_files

_Season = Literal["spring", "summer", "fall", "winter"]
_SEASONS: dict[str, _Season] = {
    "SPRING": "spring",
    "SUMMER": "summer",
    "FALL": "fall",
    "WINTER": "winter",
}


class TransmissionLossCoefficient(BaseModel):
    """An area/season's published SSC/SIC, retaining the separate input basis.

    SSC and SIC produce percent loss, while SONLF/SOFFLF inputs are fractions.
    No coefficients are recalculated. Input and final ERCOT correction labels
    can differ. Missing or reversed effective periods have None date bounds.
    asOf is the workbook's label, not proof of publication time.
    """

    model_config = ConfigDict(extra="forbid")
    year: int
    asOf: date
    season: _Season
    area: str
    slopePercentPerMW: Decimal | None
    interceptPercent: Decimal | None
    onPeakLoadMW: Decimal | None
    offPeakLoadMW: Decimal | None
    onPeakLossFactor: Decimal | None
    offPeakLossFactor: Decimal | None
    effectiveFrom: date | None
    effectiveThrough: date | None
    sourceEffectivePeriod: str | None
    sourceHeading: str
    sourceArea: str
    sourceInputArea: str
    sourceMember: str
    sourceSheet: str
    sourceRow: int
    sourceInputRow: int
    sourceFile: PublicFile | None = None


class TransmissionLossCoefficients(_PublicFiles):
    """Discover and read annual public coefficient workbooks with tinyercot[files]."""

    index_url = "https://www.ercot.com/mktinfo/data_agg"
    title_pattern = r"\d{4} TDSP Transmission Loss Factors [-–] Methodology"

    def files(self) -> list[PublicFile]:
        return _year_files(self._http, self.index_url, self.title_pattern)

    def rows(
        self, *, where: Callable[[TransmissionLossCoefficient], bool] | None = None
    ) -> Iterator[TransmissionLossCoefficient]:
        for file in self.files():
            yield from self.read(
                self.download(file),
                filename=file.url.rsplit("/", 1)[-1],
                source_file=file,
                where=where,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: PublicFile | None = None,
        where: Callable[[TransmissionLossCoefficient], bool] | None = None,
    ) -> Iterator[TransmissionLossCoefficient]:
        """Read original workbooks or ZIPs, preserving all years and revisions."""
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, source in _sheets(content, date_columns=()):
                rows = list(source)
                headers = [i for i, row in enumerate(rows) if "SSC" in row]
                if not headers:
                    continue
                found = True
                for record in _coefficients(
                    rows, headers[0], member, sheet, source_file
                ):
                    if where is None or where(record):
                        yield record
        if not found:
            raise ValueError(
                "Download contains no seasonal transmission-loss coefficients"
            )


def _date(label: str) -> date:
    fmt = "%m/%d/%y" if len(label.rsplit("/", 1)[-1]) == 2 else "%m/%d/%Y"
    return date(*strptime(label, fmt)[:3])


def _period(label: str | None) -> tuple[date | None, date | None]:
    if label is not None:
        try:
            left, right = label.split(" - ")
            start, end = _date(left), _date(right)
            if start <= end:
                return start, end
        except ValueError:
            pass
    return None, None


def _coefficients(
    rows: list[tuple[object, ...]],
    header: int,
    member: str,
    sheet: str,
    source_file: PublicFile | None,
) -> Iterator[TransmissionLossCoefficient]:
    heading = str(rows[0][0])
    match = re.match(r"TRANSMISSION LOSS FACTORS for (\d{4}) as of ([\d/]+)", heading)
    if match is None:
        raise ValueError(f"{member}/{sheet}: Missing coefficient year/as-of heading")
    basis = next(i for i, row in enumerate(rows) if "SONL" in row)
    input_columns = {
        str(rows[basis - 1][i]).split()[0]: i
        for i, value in enumerate(rows[basis])
        if value == "SONL"
    }
    input_rows = {
        str(row[0]): (i, row)
        for i, row in enumerate(rows[basis + 1 : header], basis + 1)
        if row and row[0] in _SEASONS
    }
    periods = {
        str(row[1]): str(row[0])
        for row in rows[header + 1 :]
        if len(row) > 1 and row[1] in _SEASONS
    }
    for i, row in enumerate(rows[header + 1 :], header + 1):
        if not row or row[0] not in _SEASONS:
            continue
        season = str(row[0])
        input_row, values = input_rows[season]
        period = periods.get(season)
        start, end = _period(period)
        for column, label in enumerate(rows[header]):
            if label != "SSC":
                continue
            if rows[header][column + 1] != "SIC":
                raise ValueError(f"{member}/{sheet}: Missing SIC beside SSC")
            area_label = str(rows[header - 1][column])
            area = area_label.split()[0]
            source_column = input_columns[area]
            if rows[basis][source_column : source_column + 4] != (
                "SONL",
                "SOFFL",
                "SONLF",
                "SOFFLF",
            ):
                raise ValueError(
                    f"{member}/{sheet}: Unexpected coefficient input columns"
                )
            yield TransmissionLossCoefficient(
                year=int(match[1]),
                asOf=_date(match[2]),
                season=_SEASONS[season],
                area=area,
                slopePercentPerMW=_number(row[column]),
                interceptPercent=_number(row[column + 1]),
                onPeakLoadMW=_number(values[source_column]),
                offPeakLoadMW=_number(values[source_column + 1]),
                onPeakLossFactor=_number(values[source_column + 2]),
                offPeakLossFactor=_number(values[source_column + 3]),
                effectiveFrom=start,
                effectiveThrough=end,
                sourceEffectivePeriod=period,
                sourceHeading=heading,
                sourceArea=area_label,
                sourceInputArea=str(rows[basis - 1][source_column]),
                sourceMember=member,
                sourceSheet=sheet,
                sourceRow=i + 1,
                sourceInputRow=input_row + 1,
                sourceFile=source_file,
            )
