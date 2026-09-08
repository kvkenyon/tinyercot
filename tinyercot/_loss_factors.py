"""Direct public histories of actual and forecast settlement loss factors."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import LoadArchive, _Links, _sheets, _workbooks

INDEX_URL = "https://www.ercot.com/mktinfo/data_agg"
_SERIES: dict[
    str, tuple[Literal["actual", "forecast"], Literal["transmission", "distribution"]]
] = {
    "ACTUAL_TLF": ("actual", "transmission"),
    "FORECASTED_TLF": ("forecast", "transmission"),
    "ACTUAL_DLF": ("actual", "distribution"),
    "FORECASTED_DLF": ("forecast", "distribution"),
}
_HEADER = (
    ("SAVERECORDER", "STARTTIME")
    + tuple(f"INTV{i}" for i in range(1, 101))
    + ("LSTIME",)
)


class LossFactorInterval(BaseModel):
    """A source INTV column, retaining its position and unscaled factor.

    Blank cells remain None; interval numbers do not establish UTC times.
    """

    model_config = ConfigDict(extra="forbid")
    interval: int
    factor: Decimal | None


class LossFactorDay(BaseModel):
    """One source series/day; factors are never implicitly applied to load.

    STARTTIME and LSTIME are retained without inferred timezones. LSTIME is
    not proof of when the record became publicly available.
    """

    model_config = ConfigDict(extra="forbid")
    kind: Literal["actual", "forecast"]
    level: Literal["transmission", "distribution"]
    tdsp: str | None
    lossCode: str | None
    recorder: str
    sourceStartTime: datetime
    sourceLastTime: datetime
    intervals: list[LossFactorInterval]
    sourceMember: str
    sourceSheet: str

    @property
    def operatingDay(self) -> date:
        return self.sourceStartTime.date()


class LossFactors:
    """Discover and query direct public workbooks using tinyercot[files]."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[LoadArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links(
            index_url=INDEX_URL,
            title_pattern=r"Historical[ _-]+Loss[ _-]+Factors[ _-]+(\d{4}).*",
        )
        links.feed(response.text)
        if not links.archives:
            raise ValueError("No historical loss factors found in ERCOT's public index")
        return sorted(links.archives.values(), key=lambda a: (a.year, a.url))

    def download(self, archive: LoadArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        where: Callable[[LossFactorDay], bool] | None = None,
    ) -> Iterator[LossFactorDay]:
        """Read every linked history with inclusive operating-date bounds.

        Archive labels do not limit coverage. Overlapping files stay distinct.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            yield from self.read(
                self.download(archive),
                filename=archive.url.rsplit("/", 1)[-1],
                date_from=date_from,
                date_to=date_to,
                where=where,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        date_from: date | None = None,
        date_to: date | None = None,
        where: Callable[[LossFactorDay], bool] | None = None,
    ) -> Iterator[LossFactorDay]:
        """Decode saved workbooks or ZIPs, retaining all 100 interval columns."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=(), preserve_types=True):
                if sheet not in _SERIES:
                    raise ValueError(f"{member}/{sheet}: Unknown loss-factor sheet")
                kind, level = _SERIES[sheet]
                offset = 2 if level == "distribution" else 0
                header = (("TDSPNAME", "LOSSCODE") if offset else ()) + _HEADER
                if next(rows, ()) != header:
                    raise ValueError(f"{member}/{sheet}: Unexpected loss-factor header")
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != len(header):
                        raise ValueError(f"{member}/{sheet}: Unexpected row width")
                    stamp = cells[offset + 1]
                    if not isinstance(stamp, datetime):
                        raise TypeError(f"{member}/{sheet}: Invalid STARTTIME")
                    day = stamp.date()
                    if (date_from and day < date_from) or (date_to and day > date_to):
                        continue
                    record = LossFactorDay.model_validate(
                        {
                            "kind": kind,
                            "level": level,
                            "tdsp": cells[0] if offset else None,
                            "lossCode": cells[1] if offset else None,
                            "recorder": cells[offset],
                            "sourceStartTime": stamp,
                            "sourceLastTime": cells[-1],
                            "intervals": [
                                {"interval": i, "factor": _number(v)}
                                for i, v in enumerate(cells[offset + 2 : -1], 1)
                            ],
                            "sourceMember": member,
                            "sourceSheet": sheet,
                        }
                    )
                    if where is None or where(record):
                        yield record
        if not found:
            raise ValueError("Download contains no loss-factor tables")
