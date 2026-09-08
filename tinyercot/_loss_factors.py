"""Direct public histories of actual and forecast settlement loss factors."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import LoadArchive, _sheets, _workbooks
from ._public_tables import _year_files

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
    """A source interval column, retaining its position and unscaled factor.

    Blank cells remain None; interval numbers do not establish UTC times.
    sourceLabel is an INTV name or legacy clock (including 24:00 and repeats).
    It is None when a source row does not match its sheet's interval headings.
    """

    model_config = ConfigDict(extra="forbid")
    interval: int
    factor: Decimal | None
    sourceLabel: str | None = None


class LossFactorDay(BaseModel):
    """One source series/day; factors are never implicitly applied to load.

    STARTTIME and LSTIME are retained without inferred timezones. LSTIME is
    not proof of when the record became publicly available. Legacy TIMESTAMP
    values are preserved too. Unknown kind/recorder/TDSP/loss code remain None.
    sourceSecondaryIdentifier and sourceMarker retain the legacy second and
    fourth columns, including unlabeled values without invented meanings.
    """

    model_config = ConfigDict(extra="forbid")
    kind: Literal["actual", "forecast"] | None
    level: Literal["transmission", "distribution"]
    tdsp: str | None
    lossCode: str | None
    recorder: str | None
    sourceStartTime: datetime
    sourceLastTime: datetime
    intervals: list[LossFactorInterval]
    sourceMember: str
    sourceSheet: str
    sourceFile: LoadArchive | None = None
    sourceSecondaryIdentifier: str | int | None = None
    sourceMarker: str | None = None

    @property
    def operatingDay(self) -> date:
        return self.sourceStartTime.date()


class LossFactors:
    """Discover and query direct public workbooks using tinyercot[files]."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[LoadArchive]:
        """Discover current files and all linked annual aggregation indexes."""
        pattern = (
            r"(?i)(?:Historical[ _-]+Loss[ _-]+Factors[ _-]+\d{4}.*"
            r"|\d{4} TDSP (?:Transmission|Distribution) Loss Factors [-–] "
            r"(?:Actual|Forecasted)|[DT]LF (?:actual|forecasted) for \d{4})"
        )

        archives = []
        for file in _year_files(self._http, INDEX_URL, pattern):
            year = re.search(r"\d{4}", file.title)
            if year is not None:
                archives.append(LoadArchive(year=int(year[0]), **file.model_dump()))
        if not archives:
            raise ValueError("No historical loss factors found in ERCOT's public index")
        return sorted(archives, key=lambda a: (a.year, a.url))

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
                source_file=archive,
                date_from=date_from,
                date_to=date_to,
                where=where,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        source_file: LoadArchive | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        where: Callable[[LossFactorDay], bool] | None = None,
    ) -> Iterator[LossFactorDay]:
        """Decode saved workbooks or ZIPs, retaining every source interval.

        source_file preserves index metadata, including the forecast label absent
        from early distribution workbooks. Without it, an unknown kind is None.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=(), preserve_types=True):
                header_cells = next(rows, ())
                if "START TIME" in header_cells:
                    found = True
                    for record in _legacy_days(
                        rows, header_cells, member, sheet, source_file
                    ):
                        day = record.operatingDay
                        if (date_from and day < date_from) or (
                            date_to and day > date_to
                        ):
                            continue
                        if where is None or where(record):
                            yield record
                    continue
                if sheet not in _SERIES:
                    raise ValueError(f"{member}/{sheet}: Unknown loss-factor sheet")
                kind, level = _SERIES[sheet]
                offset = 2 if level == "distribution" else 0
                header = (("TDSPNAME", "LOSSCODE") if offset else ()) + _HEADER
                if header_cells != header:
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
                                {
                                    "interval": i,
                                    "factor": _number(v),
                                    "sourceLabel": f"INTV{i}",
                                }
                                for i, v in enumerate(cells[offset + 2 : -1], 1)
                            ],
                            "sourceMember": member,
                            "sourceSheet": sheet,
                            "sourceFile": source_file,
                        }
                    )
                    if where is None or where(record):
                        yield record
        if not found:
            raise ValueError("Download contains no loss-factor tables")


def _kind(label: str) -> Literal["actual", "forecast"] | None:
    match = re.search(r"(?i)(?<![a-z])(actual|forecast(?:ed)?)(?![a-z])", label)
    if match is None:
        return None
    return "actual" if match[1].lower() == "actual" else "forecast"


def _timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.strptime(value.strip(), "%m/%d/%Y %H:%M:%S")  # noqa: DTZ007 -- source has no offset
    raise ValueError(f"Invalid loss-factor timestamp: {value!r}")


def _interval_label(value: object) -> str:
    if isinstance(value, (datetime, time)):
        minutes = value.hour * 60 + value.minute
        return f"{minutes // 60:02}:{minutes % 60:02}" if minutes else "24:00"
    if isinstance(value, timedelta):
        minutes = round(value.total_seconds() / 60)
    elif isinstance(value, (int, float)):
        minutes = round(value * 1440)
    else:
        raise TypeError(f"Invalid loss-factor interval header: {value!r}")
    return f"{minutes // 60:02}:{minutes % 60:02}"


def _legacy_days(
    rows: Iterator[tuple[object, ...]],
    header: tuple[object, ...],
    member: str,
    sheet: str,
    source_file: LoadArchive | None,
) -> Iterator[LossFactorDay]:
    if (
        header[0] not in {"CUTNAME", "TDSP"}
        or header[2] != "START TIME"
        or "TIMESTAMP" not in header
    ):
        raise ValueError(f"{member}/{sheet}: Unexpected legacy loss-factor header")
    end = header.index("TIMESTAMP")
    labels = [_interval_label(value) for value in header[4:end]]
    file_kind = _kind(member) or (_kind(source_file.title) if source_file else None)
    for cells in rows:
        if all(c in (None, "") for c in cells):
            continue
        # The 2003 DST sheet has trailing loss-code labels without dates or data.
        if all(c in (None, "") for i, c in enumerate(cells) if i != 1):
            continue
        stamp = _timestamp(cells[2])
        stop = end
        # The 2013 TLF sheet includes a 100-interval fall-back row beneath a
        # 96-interval header. Its timestamp occupies the final, unlabeled column.
        if (
            end == 100
            and len(cells) == 105
            and isinstance(cells[end], (int, float))
            and isinstance(cells[104], (datetime, str))
            and cells[104] != ""
        ):
            stop = 104
        if any(c not in (None, "") for c in cells[stop + 1 :]):
            raise ValueError(f"{member}/{sheet}: Unexpected values after timestamp")
        primary = cells[0]
        if not isinstance(primary, str):
            raise TypeError(f"{member}/{sheet}: Invalid loss-factor identifier")
        transmission = primary.startswith("TLF ")
        recorder = transmission or primary.startswith("DISTLOSSFACT_")
        yield LossFactorDay.model_validate(
            {
                "kind": _kind(primary) if transmission else file_kind,
                "level": "transmission" if transmission else "distribution",
                "tdsp": None if recorder else primary,
                "lossCode": cells[1]
                if not recorder and cells[1] not in (None, "")
                else None,
                "recorder": primary if recorder else None,
                "sourceStartTime": stamp,
                "sourceLastTime": _timestamp(cells[stop]),
                "intervals": [
                    {
                        "interval": i,
                        "factor": _number(value),
                        "sourceLabel": labels[i - 1] if stop == end else None,
                    }
                    for i, value in enumerate(cells[4:stop], 1)
                ],
                "sourceMember": member,
                "sourceSheet": sheet,
                "sourceFile": source_file,
                "sourceSecondaryIdentifier": cells[1]
                if cells[1] not in (None, "")
                else None,
                "sourceMarker": cells[3] if cells[3] not in (None, "") else None,
            }
        )
