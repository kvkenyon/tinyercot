"""Public annual backcasted load profiles used in retail settlement."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from urllib.parse import unquote, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import LoadArchive, _Links, _sheets, _workbooks

INDEX_URL = "https://www.ercot.com/mktinfo/loadprofile/alp"
ADJUSTMENTS_URL = "https://www.ercot.com/files/docs/2008/10/03/hurricane_ike_adj_factors_for_coast_wzone.xls"
_FACTOR_HEADER = ("Date",) + tuple(f"INT{i}" for i in range(1, 97))
_ORIGINAL_HEADER = ("DATE", "PType_WZ") + tuple(f"INT{i}" for i in range(1, 97))


class LoadProfileInterval(BaseModel):
    """A numbered 15-minute source cell; blank cells remain None.

    All published columns remain in source order, including unused DST columns.
    Interval numbers are not wall-clock times or UTC offsets.
    """

    model_config = ConfigDict(extra="forbid")
    interval: int
    energyKWh: Decimal | None


class LoadProfileDay(BaseModel):
    """A modeled profile/day, not individual metered consumption.

    sourceAddTime retains ADDTIME where published, with no inferred timezone
    or assertion that it establishes when the data became publicly available.
    Auxiliary workbooks retain their separate identity during model transitions.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    profile: str
    kind: Literal["backcast", "auxiliary", "original"]
    intervals: list[LoadProfileInterval]
    sourceAddTime: datetime | None
    sourceMember: str
    sourceSheet: str

    @property
    def profileType(self) -> str:
        return self.profile.rsplit("_", 1)[0]

    @property
    def weatherZone(self) -> str:
        return self.profile.rsplit("_", 1)[1]


class LoadProfileAdjustment(BaseModel):
    """One published Hurricane Ike factor for the COAST weather zone.

    Factors remain separate from kWh profiles; they are never applied implicitly.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    interval: int
    factor: Decimal | None
    weatherZone: Literal["COAST"] = "COAST"
    sourceMember: str
    sourceSheet: str


class LoadProfiles:
    """Anonymous annual XLS/XLSX histories; decoding uses tinyercot[files]."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[LoadArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links(
            index_url=INDEX_URL, title_pattern=r"(\d{4}) Actual Load Profiles"
        )
        links.feed(response.text)
        if not links.archives:
            raise ValueError("No load-profile archives found in ERCOT's public index")
        return sorted(links.archives.values(), key=lambda item: (item.year, item.url))

    def download(self, archive: LoadArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        profile: str | None = None,
    ) -> Iterator[LoadProfileDay]:
        """Stream daily profiles with inclusive dates and an exact profile filter.

        Download only indexed years intersecting the bounds. Preserve source gaps
        and overlapping backcast/auxiliary rows, without filling or deduplicating.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            if (date_from and archive.year < date_from.year) or (
                date_to and archive.year > date_to.year
            ):
                continue
            yield from self.read(
                self.download(archive),
                filename=unquote(urlsplit(archive.url).path.rsplit("/", 1)[-1]),
                date_from=date_from,
                date_to=date_to,
                profile=profile,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        date_from: date | None = None,
        date_to: date | None = None,
        profile: str | None = None,
    ) -> Iterator[LoadProfileDay]:
        """Read a saved ZIP or workbook; retain the filename for auxiliary XLS.

        Filters have the same meaning as rows(). Each result retains all interval
        cells, including blanks, plus the original workbook and worksheet names.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=(0, 1, 102)):
                # Historical workbooks put explanatory notes before the table.
                header = next(
                    (
                        r
                        for r in rows
                        if len(r) > 2
                        and (
                            r[1] in {"Date", "ERC_TRADE_DATE"}
                            or r[:2] in {("DATE", "PType_WZ"), ("Date", "INT1")}
                        )
                    ),
                    None,
                )
                if header is None:
                    raise ValueError(f"{member}/{sheet}: Missing load-profile header")
                header = tuple(header)
                while header and header[-1] in (None, ""):
                    header = header[:-1]
                if header == _FACTOR_HEADER:
                    continue  # Available separately through read_adjustments().
                original = header == _ORIGINAL_HEADER
                if not original and (
                    header[:2]
                    not in {
                        ("PType_WZ", "Date"),
                        ("Profile Type and Weather Zone", "ERC_TRADE_DATE"),
                        ("Profile Type & Weather Zone", "ERC_TRADE_DATE"),
                    }
                    or header[2:102]
                    not in {
                        tuple(f"int_kWh{i}" for i in range(1, 101)),
                        tuple(f"INT{i:03}" for i in range(1, 101)),
                    }
                    or header[102:] not in {(), ("ADDTIME",)}
                ):
                    raise ValueError(
                        f"{member}/{sheet}: Unsupported load-profile columns"
                    )
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    interval_end = 98 if original else 102
                    if len(cells) < interval_end or any(
                        c not in (None, "") for c in cells[len(header) :]
                    ):
                        raise ValueError(
                            f"{member}/{sheet}: Unexpected load-profile row width"
                        )
                    name, stamp = cells[1::-1] if original else cells[:2]
                    if (
                        not isinstance(name, str)
                        or "_" not in name
                        or not isinstance(stamp, datetime)
                    ):
                        raise ValueError(
                            f"{member}/{sheet}: Invalid profile or trade date"
                        )
                    day = stamp.date()
                    if (
                        (profile is not None and name != profile)
                        or (date_from and day < date_from)
                        or (date_to and day > date_to)
                    ):
                        continue
                    added = (
                        cells[102] if len(header) == 103 and len(cells) > 102 else None
                    )
                    if added == "":
                        added = None
                    if added is not None and not isinstance(added, datetime):
                        raise ValueError(f"{member}/{sheet}: Invalid ADDTIME value")
                    yield LoadProfileDay(
                        operatingDay=day,
                        profile=name,
                        kind="original"
                        if original
                        else "auxiliary"
                        if "auxiliary" in member.lower()
                        else "backcast",
                        intervals=[
                            LoadProfileInterval(interval=i, energyKWh=_number(value))
                            for i, value in enumerate(cells[2:interval_end], 1)
                        ],
                        sourceAddTime=added,
                        sourceMember=member,
                        sourceSheet=sheet,
                    )
        if not found:
            raise ValueError("Download contains no load-profile workbooks")

    def adjustments(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[LoadProfileAdjustment]:
        """Read Hurricane Ike factors directly, with inclusive operating dates."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        response = self._http.get(ADJUSTMENTS_URL, follow_redirects=True)
        response.raise_for_status()
        for row in self.read_adjustments(
            response.content, filename=ADJUSTMENTS_URL.rsplit("/", 1)[-1]
        ):
            if (date_from is None or row.operatingDay >= date_from) and (
                date_to is None or row.operatingDay <= date_to
            ):
                yield row

    def read_adjustments(
        self, data: bytes, *, filename: str = "workbook"
    ) -> Iterator[LoadProfileAdjustment]:
        """Read the companion factor table; other worksheets contribute no rows."""
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content):
                if sheet != "Adjustment Factors":
                    continue
                if next(rows, ()) != _FACTOR_HEADER:
                    raise ValueError(
                        f"{member}/{sheet}: Unsupported adjustment columns"
                    )
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != 97 or not isinstance(cells[0], datetime):
                        raise ValueError(f"{member}/{sheet}: Invalid adjustment row")
                    for i, value in enumerate(cells[1:], 1):
                        yield LoadProfileAdjustment(
                            operatingDay=cells[0].date(),
                            interval=i,
                            factor=_number(value),
                            sourceMember=member,
                            sourceSheet=sheet,
                        )
