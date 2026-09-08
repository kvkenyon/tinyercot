"""Historical weighted weather-zone observations from ERCOT's public files."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, get_args

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks

URL = "https://www.ercot.com/files/docs/2002/12/11/weather1996_2000.zip"
WeatherZone = Literal[
    "COAST", "EAST", "FWEST", "NCENT", "NORTH", "SCENT", "SOUTH", "WEST"
]
WeatherVariable = Literal["CLOUDCOVER", "WINDSPEED", "DEWPOINT", "DRYBULB TEMP"]
_ZONES: dict[str, WeatherZone] = {
    "Coast": "COAST",
    "East": "EAST",
    "FarWest": "FWEST",
    "North Central": "NCENT",
    "North": "NORTH",
    "South Central": "SCENT",
    "South": "SOUTH",
    "West": "WEST",
}
_HOURS = tuple(f"Hour {i}" for i in range(1, 25))


class WeatherHour(BaseModel):
    """A source hour column, with no inferred ending time, DST flag or UTC offset."""

    model_config = ConfigDict(extra="forbid")
    hour: int
    value: Decimal | None


class WeatherDay(BaseModel):
    """One variable/day from weighted station observations within a weather zone.

    Values retain their original scale. These workbooks do not label measurement
    units, so sourceUnit remains None; no unit or clock conversion is performed.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    weatherZone: WeatherZone
    variable: WeatherVariable
    hours: list[WeatherHour]
    sourceUnit: str | None = None
    sourceMember: str
    sourceSheet: str
    sourceNotes: list[str]


class HistoricalWeather:
    """Anonymous hourly history; workbook decoding uses tinyercot[files]."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def download(self) -> bytes:
        """Return ERCOT's original weather ZIP, including all eight zones."""
        response = self._http.get(URL, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        weather_zone: WeatherZone | None = None,
        variable: WeatherVariable | None = None,
    ) -> Iterator[WeatherDay]:
        """Stream variable/day records with inclusive dates and exact filters."""
        _check_filters(date_from, date_to, weather_zone, variable)
        yield from self.read(
            self.download(),
            date_from=date_from,
            date_to=date_to,
            weather_zone=weather_zone,
            variable=variable,
        )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        date_from: date | None = None,
        date_to: date | None = None,
        weather_zone: WeatherZone | None = None,
        variable: WeatherVariable | None = None,
    ) -> Iterator[WeatherDay]:
        """Read a saved ZIP or workbook; retain the original filename for its zone.

        Use actual worksheet dates, including dates beyond the archive's label.
        Preserve all 24 numbered hour columns, with blank cells remaining None.
        """
        _check_filters(date_from, date_to, weather_zone, variable)
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            match = re.fullmatch(
                r"Weather '96-'00 (.+)\.xlsx?", member.rsplit("/", 1)[-1]
            )
            if match is None or match[1] not in _ZONES:
                raise ValueError(f"{member}: Cannot identify source weather zone")
            zone = _ZONES[match[1]]
            if weather_zone is not None and zone != weather_zone:
                continue
            for sheet, rows in _sheets(content):
                if sheet not in get_args(WeatherVariable):
                    raise ValueError(f"{member}/{sheet}: Unknown weather variable")
                if variable is not None and sheet != variable:
                    continue
                notes: list[str] = []
                for cells in rows:
                    if cells[1:] == _HOURS:
                        break
                    notes.extend(c for c in cells if isinstance(c, str) and c)
                else:
                    raise ValueError(
                        f"{member}/{sheet}: Missing hourly weather columns"
                    )
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != 25 or not isinstance(cells[0], datetime):
                        raise ValueError(
                            f"{member}/{sheet}: Invalid hourly weather row"
                        )
                    day = cells[0].date()
                    if (date_from and day < date_from) or (date_to and day > date_to):
                        continue
                    yield WeatherDay.model_validate(
                        {
                            "operatingDay": day,
                            "weatherZone": zone,
                            "variable": sheet,
                            "hours": [
                                WeatherHour(hour=i, value=_number(v))
                                for i, v in enumerate(cells[1:], 1)
                            ],
                            "sourceMember": member,
                            "sourceSheet": sheet,
                            "sourceNotes": notes,
                        }
                    )
        if not found and weather_zone is None and variable is None:
            raise ValueError("Download contains no historical weather tables")


def _check_filters(
    date_from: date | None,
    date_to: date | None,
    weather_zone: WeatherZone | None,
    variable: WeatherVariable | None,
) -> None:
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must not be after date_to")
    if weather_zone is not None and weather_zone not in _ZONES.values():
        raise ValueError("Unknown weather_zone")
    if variable is not None and variable not in get_args(WeatherVariable):
        raise ValueError("Unknown weather variable")
