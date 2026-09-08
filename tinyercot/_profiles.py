"""Historical weather-based wind and solar planning profiles."""

from __future__ import annotations

import csv
import re
from collections.abc import Collection, Iterator
from datetime import date, datetime
from decimal import Decimal
from html.parser import HTMLParser
from io import BytesIO, TextIOWrapper
from typing import Literal
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from ._load import _sheets

INDEX_URL = "https://www.ercot.com/gridinfo/resource/2022"
ProfileScenario = Literal[
    "operational-planned",
    "hypothetical",
    "hypothetical-single-axis",
    "hypothetical-dual-axis",
    "metro-distributed",
    "rural-distributed",
]


class ProfileArchive(BaseModel):
    """One published study file; weather years do not indicate fleet vintage."""

    studyYear: int
    yearFrom: int
    yearTo: int
    fuel: Literal["wind", "solar"]
    scenario: ProfileScenario
    timeBasis: Literal["CST", "CST-CDT"]
    title: str
    url: str


class ProfileSeries(BaseModel):
    """An original column and its embedded metadata, when supplied.

    Labels can be unit codes, site IDs or regions. No geography or capacity is
    inferred from a different study. MWAC is retained as the source capacity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    label: str
    sourceHeader: str
    sourceColumn: int
    siteId: str | None = None
    capacityMW: Decimal | None = None
    commonName: str | None = None
    county: str | None = None
    cdrZone: str | None = None
    newForStudy: str | None = None
    tracking: str | None = None
    plantStatus: str | None = None


class ProfileOutput(BaseModel):
    """Modeled generation, in MW, for one published series."""

    model_config = ConfigDict(extra="forbid")
    series: ProfileSeries
    generationMW: Decimal | None


class ProfileHour(BaseModel):
    """A source DATE/TIME row, retaining repeats and its original column order.

    The timestamp has no inferred UTC offset or interval-ending convention.
    CST-CDT files repeat local fall-back hours without an explicit DST flag.
    """

    model_config = ConfigDict(extra="forbid")
    timestamp: datetime
    sourceTime: str
    sourceYear: int | None
    outputs: list[ProfileOutput]
    sourceMember: str
    sourceSheet: str | None
    sourceRow: int


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.href: str | None = None
        self.title = ""
        self.files: dict[str, ProfileArchive] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.title = ""

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.title += data

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self.href is None:
            return
        url = urljoin(INDEX_URL, self.href)
        self.href = None
        parts = urlsplit(url)
        match = re.fullmatch(
            r"/files/docs/(\d{4})/\d{2}/\d{2}/(.+?)[_-](\d{4})"
            r"(?:-(\d{4}))?[_-](CST(?:-CDT)?)\.(?:csv|xlsx)",
            parts.path,
        )
        if parts.scheme != "https" or parts.netloc != "www.ercot.com" or not match:
            return
        name = match[2].lower().replace("_", "-")
        if "profiles" not in name or not any(f in name for f in ("wind", "solar")):
            return
        scenario: ProfileScenario
        if "operational" in name and "planned" in name:
            scenario = "operational-planned"
        elif "singleaxis" in name:
            scenario = "hypothetical-single-axis"
        elif "dualaxis" in name:
            scenario = "hypothetical-dual-axis"
        elif "hypothetical" in name:
            scenario = "hypothetical"
        elif "metro-distributed" in name:
            scenario = "metro-distributed"
        elif "rural-distributed" in name:
            scenario = "rural-distributed"
        else:
            return
        self.files[url] = ProfileArchive(
            studyYear=int(match[1]),
            yearFrom=int(match[3]),
            yearTo=int(match[4] or match[3]),
            fuel="wind" if "wind" in name else "solar",
            scenario=scenario,
            timeBasis="CST-CDT" if match[5] == "CST-CDT" else "CST",
            title=" ".join(self.title.split()),
            url=url,
        )


class GenerationProfiles:
    """Direct public planning files linked from ERCOT's 2022 resource index.

    Choose a study and scenario explicitly; revisions represent different fleets
    and must not be silently concatenated into observed generation history.
    CSV needs no extras; XLSX uses tinyercot[files].
    """

    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def archives(
        self,
        *,
        study_year: int | None = None,
        fuel: Literal["wind", "solar"] | None = None,
        scenario: ProfileScenario | None = None,
    ) -> list[ProfileArchive]:
        response = self._http.get(INDEX_URL, follow_redirects=True)
        response.raise_for_status()
        links = _Links()
        links.feed(response.text)
        if not links.files:
            raise ValueError(
                "No generation-profile files found in ERCOT's public index"
            )
        return sorted(
            (
                a
                for a in links.files.values()
                if (study_year is None or a.studyYear == study_year)
                and (fuel is None or a.fuel == fuel)
                and (scenario is None or a.scenario == scenario)
            ),
            key=lambda a: (a.studyYear, a.fuel, a.scenario, a.yearFrom, a.url),
        )

    def download(self, archive: ProfileArchive) -> bytes:
        response = self._http.get(archive.url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    def rows(
        self,
        archive: ProfileArchive,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        series: Collection[str] | None = None,
    ) -> Iterator[ProfileHour]:
        """Download one study file and query inclusive dates and exact series labels."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        yield from self.read(
            self.download(archive),
            filename=archive.url.rsplit("/", 1)[-1],
            date_from=date_from,
            date_to=date_to,
            series=series,
        )

    def read_series(self, data: bytes) -> list[ProfileSeries]:
        """Read ordered column metadata from a saved profile CSV or XLSX."""
        return [s for _, _, _, columns, _ in _tables(data) for s in columns]

    def read(
        self,
        data: bytes,
        *,
        filename: str = "download",
        date_from: date | None = None,
        date_to: date | None = None,
        series: Collection[str] | None = None,
    ) -> Iterator[ProfileHour]:
        """Read original source rows; preserve missing cells and repeated timestamps."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must not be after date_to")
        for sheet, start, offset, columns, rows in _tables(data):
            selected = [s for s in columns if series is None or s.label in series]
            for number, cells in enumerate(rows, start + 1):
                if not any(v not in (None, "") for v in cells):
                    continue
                try:
                    if len(cells) != offset + 2 + len(columns):
                        raise ValueError("Unexpected profile column count")
                    day = str(cells[offset])
                    clock = str(cells[offset + 1])
                    hhmm = int(clock)
                    stamp = datetime(  # noqa: DTZ001 -- Source has no UTC offset.
                        int(day[:4]),
                        int(day[4:6]),
                        int(day[6:]),
                        hhmm // 100,
                        hhmm % 100,
                    )
                    if (date_from and stamp.date() < date_from) or (
                        date_to and stamp.date() > date_to
                    ):
                        continue
                    yield ProfileHour(
                        timestamp=stamp,
                        sourceTime=clock,
                        sourceYear=int(str(cells[0])) if offset else None,
                        outputs=[
                            ProfileOutput(
                                series=s,
                                generationMW=_number(cells[s.sourceColumn - 1]),
                            )
                            for s in selected
                        ],
                        sourceMember=filename,
                        sourceSheet=sheet,
                        sourceRow=number,
                    )
                except (ValueError, TypeError) as error:
                    raise ValueError(
                        f"{filename}/{sheet or 'CSV'}:{number}: {error}"
                    ) from error


def _number(value: object) -> Decimal | None:
    return None if value in (None, "") else Decimal(str(value))


def _text(value: object) -> str | None:
    return None if value in (None, "") else str(value)


def _tables(
    data: bytes,
) -> Iterator[
    tuple[str | None, int, int, list[ProfileSeries], Iterator[tuple[object, ...]]]
]:
    sheets: Iterator[tuple[str | None, Iterator[tuple[object, ...]]]]
    if data.startswith(b"PK"):
        sheets = _sheets(data)
    else:
        csv_rows = (
            tuple(r)
            for r in csv.reader(TextIOWrapper(BytesIO(data), encoding="utf-8-sig"))
        )
        sheets = iter([(None, csv_rows)])
    for sheet, rows in sheets:
        metadata: dict[str, tuple[object, ...]] = {}
        for number, header in enumerate(rows, 1):
            offset = 1 if header[:3] == ("", "DATE", "TIME") else 0
            if header[offset : offset + 2] == ("DATE", "TIME"):
                break
            if len(header) < 2:
                raise ValueError("Missing profile DATE/TIME header")
            metadata[str(header[1]).strip() if header[1] else "siteId"] = header
        else:
            raise ValueError("Missing profile DATE/TIME header")
        columns = []
        fields = {
            "siteId": "siteId",
            "MWAC": "capacityMW",
            "Common Name": "commonName",
            "County": "county",
            "CDR Zone": "cdrZone",
            "New for 2022": "newForStudy",
            "Tracking": "tracking",
            "Plant Status": "plantStatus",
        }
        unknown = metadata.keys() - fields.keys()
        if unknown:
            raise ValueError(f"Unknown profile metadata rows: {sorted(unknown)}")
        for i in range(offset + 2, len(header)):
            source = str(header[i])
            label, separator, capacity = source.partition(":capacity=")
            values: dict[str, object] = {
                "label": label,
                "sourceHeader": source,
                "sourceColumn": i + 1,
                "capacityMW": Decimal(capacity) if separator else None,
            }
            for key, row in metadata.items():
                values[fields[key]] = (
                    _number(row[i]) if key == "MWAC" else _text(row[i])
                )
            columns.append(ProfileSeries.model_validate(values))
        yield sheet, number, offset, columns, rows
