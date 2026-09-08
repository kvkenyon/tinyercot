"""The direct public archive of historical generation scheduled by zone."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO

import httpx
from pydantic import BaseModel, ConfigDict

URL = "https://www.ercot.com/files/docs/2007/04/23/historical_generation_scheduled_by_zone.zip"


class ScheduledGeneration(BaseModel):
    """A scheduled MW quantity at the source's local CPT period ending.

    Historical zone IDs change between years. The source supplies no zone names
    or UTC offsets; neither is inferred. These are schedules, not actual output.
    """

    model_config = ConfigDict(extra="forbid")
    periodEnding: datetime
    zoneId: int
    scheduledMW: Decimal
    sourceMember: str

    @property
    def operatingDay(self) -> date:
        """The date of the 15-minute interval, including period endings at midnight."""
        return (self.periodEnding - timedelta(minutes=15)).date()


class ZonalGeneration:
    """Anonymous access to the published 2001–2007 snapshot and its yearly ZIPs."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def download(self) -> bytes:
        """Download the original archive, containing seven nested yearly ZIPs."""
        response = self._http.get(URL, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Iterator[ScheduledGeneration]:
        """Read schedules with inclusive operating-date bounds; retain source gaps."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for row in self.read(self.download()):
            if (date_from is None or row.operatingDay >= date_from) and (
                date_to is None or row.operatingDay <= date_to
            ):
                yield row

    def read(
        self, data: bytes, *, filename: str = "download"
    ) -> Iterator[ScheduledGeneration]:
        """Read the outer ZIP, a yearly ZIP, or a saved tab-delimited report."""
        from ._history import _archive_files

        files = (
            _archive_files(data, "*.txt")
            if data.startswith(b"PK")
            else iter([(filename, data)])
        )
        found = False
        for member, content in files:
            found = True
            rows = csv.reader(StringIO(content.decode("ascii")), delimiter="\t")
            if next(rows, None) != ["CPT_PERIODENDING", "ZONEID", "MW"]:
                raise ValueError(f"{member}: Unsupported scheduled-generation header")
            for number, cells in enumerate(rows, 2):
                if not cells:
                    continue
                if len(cells) != 3:
                    raise ValueError(
                        f"{member}:{number}: Expected three source columns"
                    )
                try:
                    yield ScheduledGeneration.model_validate(
                        dict(
                            zip(
                                ("periodEnding", "zoneId", "scheduledMW"),
                                cells,
                                strict=True,
                            )
                        )
                        | {"sourceMember": member}
                    )
                except ValueError as error:
                    raise ValueError(f"{member}:{number}: {error}") from error
        if not found:
            raise ValueError("Archive contains no scheduled-generation reports")
