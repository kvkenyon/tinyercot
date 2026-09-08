"""All seasonal/weekly peak tables checked against original source positions."""

# Source dates have no time zone; only their calendar dates are read.
# ruff: noqa: DTZ007

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest
import xlrd

from tinyercot import Client, SeasonalPeakForecast, WeeklyPeakForecast

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/zonal-peaks"
SOURCES = json.loads((ROOT / "sources.json").read_text())
ZONE_FIELDS = {
    "coast": "coast",
    "east": "east",
    "fwest": "farWest",
    "ncent": "northCentral",
    "north": "north",
    "scent": "southCentral",
    "south": "south",
    "west": "west",
}


def original(source):
    with ZipFile(ROOT / "workbooks.zip") as archive:
        return archive.read(source["file"])


def grids(data):
    if data.startswith(b"\xd0\xcf"):
        book = xlrd.open_workbook(file_contents=data)
        result = {
            s.name: [s.row_values(i) for i in range(s.nrows)] for s in book.sheets()
        }
        book.release_resources()
        return result
    book = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    result = {s.title: list(s.values) for s in book}
    book.close()
    return result


def number(v):
    return None if v in (None, "") else Decimal(str(v))


def day(v):
    # The original weekly inputs use Excel dates or DDMonYYYY strings.
    return (
        v.date() if isinstance(v, datetime) else datetime.strptime(v, "%d%b%Y").date()
    )


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s["file"])
def test_complete_source_tables(source):
    data = original(source)
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
    source_grids = grids(data)
    with Client() as client:
        service = (
            client.weekly_peak_forecasts
            if source["kind"] == "weekly"
            else client.seasonal_peak_forecasts
        )
        rows = list(service.read(data, filename=source["file"]))
    coordinates = []
    for table in source["tables"]:
        for line in range(table["firstRow"], table["lastRow"] + 1):
            coordinates.append(
                (
                    list(source_grids).index(table["sheet"]),
                    line,
                    table.get("column", 1),
                    table,
                )
            )
    coordinates.sort(key=lambda c: c[:3])
    assert len(rows) == len(coordinates)
    for actual, (_, line, column, table) in zip(rows, coordinates, strict=True):
        grid = source_grids[table["sheet"]]
        raw, header = grid[line - 1], grid[table["headerRow"] - 1]
        assert (actual.sourceMember, actual.sourceSheet, actual.sourceRow) == (
            source["file"],
            table["sheet"],
            line,
        )
        if isinstance(actual, WeeklyPeakForecast):
            assert (actual.beginDate, actual.endDate, actual.peakDate) == tuple(
                day(v) for v in raw[:3]
            )
            assert actual.peakHour == raw[3]
            assert actual.kind == "forecast" and actual.percentile is None
            assert actual.unit is None
            start = 4
        else:
            assert isinstance(actual, SeasonalPeakForecast)
            period = str(raw[column - 1]).removesuffix(".0")
            assert actual.sourcePeriod == period
            assert actual.year == int(period.split("-")[0])
            assert actual.endYear == (
                int(period.split("-")[1]) if "-" in period else None
            )
            assert actual.kind == table["kind"]
            assert actual.sourceTitle == table["title"]
            assert actual.sourceColumn == column
            assert actual.sourcePercentileLabel == table["percentileLabel"]
            assert actual.percentile == (90 if table["percentileLabel"] else None)
            assert actual.unit == ("MW" if "(MW)" in table["title"] else None)
            start = column
        for i in range(8):
            field = ZONE_FIELDS[header[start + i].lower()]
            assert getattr(actual.peaks, field) == number(raw[start + i])
        assert actual.peaks.total == number(raw[start + 8])
        assert actual.sourceTotalLabel == header[start + 8]
        assert type(actual).model_validate_json(actual.model_dump_json()) == actual


def test_historical_headers_and_percentiles_do_not_override_section_kind():
    source = next(s for s in SOURCES if "06252014" in s["url"])
    with Client() as client:
        rows = list(client.seasonal_peak_forecasts.read(original(source)))
    assert all(r.kind == "forecast" and r.percentile == 90 for r in rows[:16])
    assert all(r.kind == "historical" and r.percentile is None for r in rows[16:])
    assert all(r.unit == "MW" and r.coincident is False for r in rows[16:])
    assert rows[16].year == 2002
    assert rows[16].sourceTitle == "Summer Non-Coincident Peak Demand (MW)"


def test_winter_periods_and_parallel_forecasts_keep_independent_values():
    source = next(s for s in SOURCES if "Summer-and-Winter" in s["url"])
    with Client() as client:
        rows = list(client.seasonal_peak_forecasts.read(original(source)))
    assert len(rows) == 56
    assert {r.scenario for r in rows} == {"tsp_provided", "ercot_adjusted"}
    assert {r.season for r in rows} == {"summer", "winter"}
    assert {r.coincident for r in rows} == {False, True}
    assert all(r.demandBasis == "net" for r in rows)
    assert rows[0].sourceColumn == 1 and rows[1].sourceColumn == 16
    assert rows[0].peaks.coast != rows[1].peaks.coast
    winter = [r for r in rows if r.season == "winter"]
    assert all(r.endYear == r.year + 1 for r in winter)
    assert winter[0].sourcePeriod == "2025-2026"


@pytest.mark.parametrize("kind", ["seasonal", "weekly"])
def test_discovery_enriches_percentiles_before_filtering_without_changing_history(kind):
    sources = {s["url"]: s for s in SOURCES if s["kind"] == kind}
    with ZipFile(ROOT.parent / "peak-forecasts/indexes.zip") as archive:
        indexes = {n: archive.read(n) for n in archive.namelist()}
    calls = []

    def respond(request):
        url = str(request.url)
        calls.append(url)
        if url in sources:
            return httpx.Response(200, content=original(sources[url]))
        name = url.rsplit("/", 1)[-1]
        return httpx.Response(
            200, content=indexes[("root" if name == "forecast" else name) + ".html"]
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as http,
        Client(client=http) as client,
    ):
        service = (
            client.weekly_peak_forecasts
            if kind == "weekly"
            else client.seasonal_peak_forecasts
        )
        assert {f.url for f in service.files()} == set(sources)
        all_rows = list(service.rows())
        assert all(r.sourceFile.url in sources for r in all_rows)
        assert all(r.percentile is None for r in all_rows if r.kind == "historical")
        selected = list(service.rows(where=lambda r: r.percentile == 90))
        assert selected and all(r.kind == "forecast" for r in selected)
        if kind == "weekly":
            assert len(selected) == 263
        else:
            missing_body_label = [
                r
                for r in selected
                if "/2022/" in r.sourceFile.url and "90th_" in r.sourceFile.url
            ]
            assert len(missing_body_label) == 30
            assert all(
                r.sourcePercentileLabel == r.sourceFile.title
                for r in missing_body_label
            )
        assert all(u.startswith("https://www.ercot.com/") for u in calls)
