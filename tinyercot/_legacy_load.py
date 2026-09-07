"""Pre-2002 hourly loads; source entities and units are never conflated."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict


class LegacyHourlyLoad(BaseModel):
    """One entity/hour measurement, retaining source units and provenance.

    A missing unit means the source text does not state one. EEI MWh/hour is
    represented as MW. No demand values are rescaled. Card headers are retained
    verbatim because ERCOT contributors populated their metadata differently.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    hourEnding: int
    entity: str
    entityType: Literal["system", "control_area", "load_serving_entity"]
    controlArea: str | None = None
    demand: Decimal | None
    unit: Literal["MW", "kW"] | None
    sourceMember: str
    sourceError: Literal["#VALUE!"] | None = None
    sourceSheet: str | None = None
    sourceCardHeader: str | None = None


def read_legacy(
    data: bytes, *, filename: str = "download"
) -> Iterator[LegacyHourlyLoad]:
    """Read a legacy load ZIP, XLS or named text file; skip companion forecasts."""
    from ._history import _archive_files

    members = (
        _archive_files(data, "*")
        if data.startswith(b"PK")
        else iter([(filename, data)])
    )
    found = False
    for name, content in members:
        base = name.rsplit("/", 1)[-1]
        if base.upper() in {
            "ERCOTWINDEM.TXT",
            "ERCOTERYPROJ.TXT",
            "ERCOTSUMDEM.TXT",
        } or re.fullmatch(r"[A-Z]+FORE\.96", base.upper()):
            continue
        try:
            if content.startswith(b"\xd0\xcf\x11\xe0"):
                yield from _xls(content, name)
            elif base.lower() in {
                "erceei95.txt",
                "erceei97.txt",
            } or base.upper().endswith("LD.EEI"):
                yield from _eei(content.decode("ascii"), name)
            elif content.startswith(b"ERCOT Hourly Load Data for 1996"):
                yield from _system_1996(content.decode("ascii"), name)
            elif re.match(rb"ERCOT (?:1999|2000) Hourly Load", content):
                yield from _control_text(content.decode("ascii"), name)
            else:
                raise ValueError(
                    "Unsupported legacy hourly load file; pass the original filename for EEI text"
                )
            found = True
        except (ValueError, TypeError) as error:
            raise ValueError(f"{name}: {error}") from error
    if not found:
        raise ValueError("Download contains no legacy hourly load data")


def _number(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation as error:
        raise ValueError(f"Invalid source demand: {value!r}") from error


def _eei(text: str, filename: str) -> Iterator[LegacyHourlyLoad]:
    base = filename.rsplit("/", 1)[-1]
    area = re.fullmatch(r"([A-Z]+)\d{2}LD\.EEI", base.upper())
    if area is None and base.lower() not in {"erceei95.txt", "erceei97.txt"}:
        raise ValueError("Unrecognized EEI entity filename")
    entity = area[1] if area else "ERCOT"
    for line, card in enumerate(text.splitlines(), 1):
        if not card.strip():
            continue
        if len(card) < 80 or card[80:].strip() or card[6] not in "12":
            raise ValueError(f"line {line}: unsupported EEI card")
        day = date(1900 + int(card[4:6]), int(card[:2]), int(card[2:4]))
        first_hour = 1 if card[6] == "1" else 13
        for position in range(12):
            yield LegacyHourlyLoad(
                operatingDay=day,
                hourEnding=first_hour + position,
                entity=entity,
                entityType="control_area" if area else "system",
                controlArea=entity if area else None,
                demand=_number(card[20 + position * 5 : 25 + position * 5].strip()),
                unit="MW",
                sourceMember=filename,
                sourceCardHeader=card[:20],
            )


def _system_1996(text: str, filename: str) -> Iterator[LegacyHourlyLoad]:
    started = False
    for line, value in enumerate(text.splitlines(), 1):
        if not value.strip():
            continue
        match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d{2})\s+(\d+)\s+([\d,]+)\s*", value)
        if match:
            started = True
            yield LegacyHourlyLoad(
                operatingDay=date(1900 + int(match[3]), int(match[1]), int(match[2])),
                hourEnding=int(match[4]),
                entity="ERCOT",
                entityType="system",
                demand=_number(match[5]),
                unit=None,
                sourceMember=filename,
            )
        elif started:
            raise ValueError(f"line {line}: unsupported system-load row")
    if not started:
        raise ValueError("Missing system-load table")


_CONTROL_1999 = (
    "AENX",
    "CPST",
    "CSWS",
    "LCRA",
    "PUBX",
    "REIT",
    "STEC",
    "TMPP",
    "TNMP",
    "TUET",
)
_CONTROL_2000 = (
    "AENX",
    "AEPX",
    "CPST",
    "LCRA",
    "BPUB",
    "REIT",
    "STEC",
    "TMPP",
    "TNMP",
    "TUET",
)


def _control_text(text: str, filename: str) -> Iterator[LegacyHourlyLoad]:
    old = text.startswith("ERCOT 1999")
    codes = _CONTROL_1999 if old else _CONTROL_2000
    expected = (
        [*codes, "ERCOT", "TOTAL", "M", "D", "Year", "HR"]
        if old
        else ["M", "D", "HR", *codes, "ERCOT", "TUET", "ERCOT", "TOTAL"]
    )
    started = False
    for line, value in enumerate(text.splitlines(), 1):
        parts = value.split()
        if parts == expected:
            started = True
            continue
        if not started or not parts:
            continue
        if len(parts) != (15 if old else 14):
            raise ValueError(f"line {line}: unexpected control-area columns")
        if old:
            month, day, year, hour = map(int, parts[-4:])
            amounts = parts[:11]
        else:
            month, day, hour = map(int, parts[:3])
            year = 2000
            amounts = parts[3:]
        for entity, amount in zip((*codes, "ERCOT TOTAL"), amounts, strict=True):
            system = entity == "ERCOT TOTAL"
            yield LegacyHourlyLoad(
                operatingDay=date(year, month, day),
                hourEnding=hour,
                entity=entity,
                entityType="system" if system else "control_area",
                controlArea=None if system else entity,
                demand=None if amount == "#VALUE!" else _number(amount),
                sourceError="#VALUE!" if amount == "#VALUE!" else None,
                unit=None,
                sourceMember=filename,
            )
    if not started:
        raise ValueError("Missing supported control-area header")


def _xls(data: bytes, filename: str) -> Iterator[LegacyHourlyLoad]:
    try:
        import xlrd
    except ImportError as error:
        raise ImportError(
            "Install tinyercot[files] to read XLS load archives"
        ) from error
    found = False
    with xlrd.open_workbook(file_contents=data) as book:
        for sheet in book.sheets():
            title = sheet.cell_value(0, 0) if sheet.nrows and sheet.ncols else ""
            if title == "ERCOT - Composite Load":
                if (
                    sheet.ncols != 25
                    or sheet.cell_value(3, 0) != "Date"
                    or sheet.cell_value(0, 14) != "mw"
                ):
                    raise ValueError("Unsupported composite-load columns or units")
                hours = [
                    round(float(sheet.cell_value(3, j)) * 24) or 24
                    for j in range(1, 25)
                ]
                if hours != list(range(1, 25)):
                    raise ValueError("Unsupported composite hour labels")
                found = True
                for i in range(4, sheet.nrows):
                    operating_day = xlrd.xldate_as_datetime(
                        float(sheet.cell_value(i, 0)), book.datemode
                    ).date()
                    for j, hour in enumerate(hours, 1):
                        yield LegacyHourlyLoad(
                            operatingDay=operating_day,
                            hourEnding=hour,
                            entity="ERCOT",
                            entityType="system",
                            demand=_number(sheet.cell_value(i, j)),
                            unit="MW",
                            sourceMember=filename,
                            sourceSheet=sheet.name,
                        )
            elif title == "ERCOT FERC 714 1998 Hourly Demand Data":
                if list(sheet.row_values(5))[:4] != [
                    "MONTH",
                    "DAY",
                    "YEAR",
                    "HOUR ENDING",
                ] or any(
                    sheet.cell_value(5, j) != "HOURLY DEMAND kW"
                    for j in range(4, sheet.ncols)
                ):
                    raise ValueError("Unsupported LSE-load columns or units")
                found = True
                for i in range(6, sheet.nrows):
                    month, day, year, hour = (
                        int(sheet.cell_value(i, j)) for j in range(4)
                    )
                    for j in range(4, sheet.ncols):
                        entity = str(sheet.cell_value(3, j))
                        control = str(sheet.cell_value(4, j))
                        yield LegacyHourlyLoad(
                            operatingDay=date(year, month, day),
                            hourEnding=hour,
                            entity=entity,
                            entityType="system"
                            if entity == "TOTAL"
                            else "load_serving_entity",
                            controlArea=control,
                            demand=_number(sheet.cell_value(i, j)),
                            unit="kW",
                            sourceMember=filename,
                            sourceSheet=sheet.name,
                        )
            elif sheet.name not in {
                "ANNUAL ENERGY PROJECTION MWH",
                "SUMMER PEAK DEAMND MW",
                "WINTER PEAK DEMAND MW",
            }:
                raise ValueError(f"Unsupported legacy worksheet: {sheet.name}")
    if not found:
        raise ValueError("Workbook contains no legacy hourly loads")
