"""Public historical IDR compliance summaries for retail settlement analysis."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal

import httpx
from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import LoadArchive, _Links, _sheets, _workbooks

INDEX_URL = "https://www.ercot.com/mktinfo/data_agg/idr_pcv"


class IdrCompliance(BaseModel):
    """One market/provider value from a particular report vintage.

    Numeric values retain their original scale. Text markers and Excel errors
    are represented by status with compliance=None. A run date is not proof of
    when the report became publicly available.
    """

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    reportRunDate: date
    entity: str
    compliance: Decimal | None
    status: str | None
    sourceMember: str
    sourceSheet: str
    sourceArchive: str | None


class IdrComplianceHistory:
    """Anonymous annual downloads; decoding uses the optional files dependencies."""

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(self) -> list[LoadArchive]:
        """Discover archive links; years describe filings, not operating dates."""
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links(index_url=INDEX_URL, title_pattern=r"IDR PCV (\d{4})")
        links.feed(response.text)
        if not links.archives:
            raise ValueError("No IDR compliance archives found in ERCOT's public index")
        return sorted(links.archives.values(), key=lambda r: (r.year, r.url))

    def download(self, archive: LoadArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        entity: str | None = None,
    ) -> Iterator[IdrCompliance]:
        """Stream report vintages with inclusive operating dates and exact entity.

        Filings can describe much earlier dates, so every indexed archive is
        considered. Repeated rows and corrections remain separate.
        """
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for archive in self.archives():
            yield from self.read(
                self.download(archive),
                filename=archive.url.rsplit("/", 1)[-1],
                date_from=date_from,
                date_to=date_to,
                entity=entity,
            )

    def read(
        self,
        data: bytes,
        *,
        filename: str = "workbook",
        date_from: date | None = None,
        date_to: date | None = None,
        entity: str | None = None,
    ) -> Iterator[IdrCompliance]:
        """Decode saved ZIPs/workbooks, preserving provider labels and cell status."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, preserve_types=True):
                run: date | None = None
                nonempty = False
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    nonempty = True
                    title = (
                        " ".join(cells[0].split()) if isinstance(cells[0], str) else ""
                    )
                    if title.startswith("Report Run Date:"):
                        label = title.partition(":")[2].strip()
                        if label:
                            month, day_number, year = map(int, label.split("/"))
                            run = date(year, month, day_number)
                        elif len(cells) > 1 and isinstance(cells[1], datetime):
                            run = cells[1].date()
                    if cells[0] in ("Date", "Trade Day"):
                        header = cells
                        break
                else:
                    if nonempty:
                        raise ValueError(f"{member}/{sheet}: Missing compliance header")
                    continue
                if (
                    run is None
                    or len(header) < 2
                    or not all(isinstance(c, str) and c for c in header)
                ):
                    raise ValueError(
                        f"{member}/{sheet}: Missing report date or entity columns"
                    )
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != len(header):
                        raise ValueError(
                            f"{member}/{sheet}: Unexpected compliance row width"
                        )
                    stamp = cells[0]
                    # Old templates contain zero-date rows filled entirely with #N/A.
                    if stamp == datetime.fromisoformat("1899-12-31T00:00:00") and all(
                        v == "#N/A" for v in cells[1:]
                    ):
                        continue
                    if isinstance(stamp, datetime):
                        day = stamp.date()
                    elif isinstance(stamp, str):
                        day = date.fromisoformat(stamp.replace("/", "-"))
                    else:
                        raise TypeError(f"{member}/{sheet}: Invalid operating date")
                    if (date_from and day < date_from) or (date_to and day > date_to):
                        continue
                    for name, value in zip(header[1:], cells[1:], strict=True):
                        if entity is not None and name != entity:
                            continue
                        marker = value if isinstance(value, str) and value else None
                        yield IdrCompliance.model_validate(
                            {
                                "operatingDay": day,
                                "reportRunDate": run,
                                "entity": name,
                                "compliance": None if marker else _number(value),
                                "status": marker,
                                "sourceMember": member,
                                "sourceSheet": sheet,
                                "sourceArchive": filename
                                if filename.lower().endswith(".zip")
                                else None,
                            }
                        )
        if not found:
            raise ValueError("Download contains no IDR compliance tables")
