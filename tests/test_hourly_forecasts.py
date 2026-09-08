"""Original XLSX/XLSB excerpts preserve every published load component."""

import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, HourlyLoadForecast

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/hourly-forecasts"
SOURCES = json.loads((ROOT / "sources.json").read_text())


def original(source):
    with ZipFile(ROOT / "samples.zip") as archive:
        return archive.read(source["file"])


def cells(source):
    with ZipFile(ROOT / "samples.zip") as archive:
        return json.loads(archive.read(source["file"] + ".json"))


def number(value):
    return None if value in (None, "") else Decimal(str(value))


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s["file"])
def test_every_component_matches_independent_source_cells(source):
    data = original(source)
    assert hashlib.sha256(data).hexdigest() == source["fixtureSha256"]
    grid = cells(source)
    first = source["firstRow"]
    offset = 0 if grid[first - 2][0] == "year" else 1
    with Client() as client:
        rows = list(client.hourly_load_forecasts.read(data, filename=source["file"]))
    assert len(rows) == len(grid) - first + 1
    for line, (actual, raw) in enumerate(
        zip(rows, grid[first - 1 :], strict=True), first
    ):
        assert actual.forecastDate == date(*(int(v) for v in raw[offset : offset + 3]))
        assert actual.hour == raw[offset + 3]
        source_date = raw[0] if offset else None
        if isinstance(source_date, (float, int)):
            source_date = (
                date(1899, 12, 30) + timedelta(days=int(source_date))
            ).isoformat()
        assert actual.sourceDate == (
            date.fromisoformat(source_date[:10]) if source_date else None
        )
        assert actual.sourceMember == source["file"] and actual.sourceRow == line
        assert actual.sourceFile is None and actual.scenario is None
        assert actual.unit == ("MW" if source["title"].startswith("2023") else None)
        seen = set()
        for group, start, zones in source["groups"]:
            component = getattr(actual, group)
            for i, zone in enumerate(zones, start):
                assert getattr(component, zone) == number(raw[i])
                assert actual.sourceLabels[f"{group}.{zone}"] == grid[first - 2][i]
                seen.add(i)
        assert seen == set(range(offset + 4, len(raw)))
        assert (
            HourlyLoadForecast.model_validate_json(actual.model_dump_json()) == actual
        )


def test_absent_totals_negative_pv_and_flexible_load_components_stay_distinct():
    with Client() as client:
        decoded = {
            s["title"]: next(client.hourly_load_forecasts.read(original(s)))
            for s in SOURCES
        }
    tsp = decoded["TSP Provided Hourly Forecast"]
    adjusted = decoded["ERCOT Adjusted Forecast"]
    assert tsp.contractedLoad.total is None and tsp.officerLetterLoad.total is None
    assert adjusted.contractedLoad.total == adjusted.officerLetterLoad.total == 0
    assert tsp.largeFlexibleLoad.east is None
    older = decoded["2022 ERCOT Hourly Forecast"]
    assert older.rooftopPV.southCentral < 0
    assert older.gross is not None and older.baseLoad is None
    assert decoded["2021 ERCOT Hourly Forecast"].forecast is not None
    row = decoded["2024 ERCOT Hourly Forecast"]
    assert (
        row.contractedFlexibleLoad is not None
        and row.officerLetterFlexibleLoad is not None
    )
    assert row.officerLetterLoad.east is None
    assert row.sourceLabels["largeFlexibleLoad.coast"] == "Coast_LFL_15%"
    assert row.sourceLabels["net.coast"] == "Coast_Net_15"
    assert "15%" in row.sourceNotes[0]


def test_live_index_shapes_discover_both_excel_formats_and_filter_after_scenario():
    sources = {s["url"]: s for s in SOURCES}
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
        service = client.hourly_load_forecasts
        assert {f.url for f in service.files()} == set(sources)
        rows = list(
            service.rows(
                where=lambda r: r.scenario == "ercot_adjusted" and r.hour == 24
            )
        )
    assert len(rows) == 2
    assert all(r.sourceFile.title == "ERCOT Adjusted Forecast" for r in rows)
    assert all("ercot.com" in url and "mis" not in url.lower() for url in calls)


def test_repeated_hours_and_date_column_disagreement_are_preserved():
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(["Date", "Year", "Month", "Day", "Hour", "Coast", "ERCOT"])
    sheet.append([date(2025, 11, 1), 2025, 11, 2, 2, 10, 100])
    sheet.append([date(2025, 11, 2), 2025, 11, 2, 2, 20, 200])
    stream = BytesIO()
    book.save(stream)
    with Client() as client:
        rows = list(client.hourly_load_forecasts.read(stream.getvalue()))
    assert len(rows) == 2 and rows[0].hour == rows[1].hour == 2
    assert rows[0].forecastDate == rows[1].forecastDate == date(2025, 11, 2)
    assert rows[0].sourceDate == date(2025, 11, 1)
    assert rows[0].forecast.coast == 10 and rows[1].forecast.coast == 20


def test_unknown_component_is_not_silently_dropped():
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append(["year", "month", "day", "hour", "Coast_NewComponent"])
    sheet.append([2025, 1, 1, 1, 100])
    stream = BytesIO()
    book.save(stream)
    with (
        Client() as client,
        pytest.raises(ValueError, match="Unknown hourly forecast column"),
    ):
        list(client.hourly_load_forecasts.read(stream.getvalue()))
