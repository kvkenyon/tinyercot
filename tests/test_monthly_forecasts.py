"""Monthly forecasts retain source date/value pairs and explicit units."""

import hashlib
import json
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest
import xlrd

from tinyercot import Client, MonthlyLoadForecast

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/monthly-forecasts"
SOURCES = json.loads((ROOT / "sources.json").read_text())


def original(source):
    with ZipFile(ROOT / "workbooks.zip") as archive:
        return archive.read(source["file"])


def source_cells(data):
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


def number(value):
    return None if value in (None, "") else Decimal(str(value))


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s["file"])
def test_every_month_value_pair_matches_the_original_workbook(source):
    data = original(source)
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
    grids = source_cells(data)
    coordinates = sorted(
        (line, table["column"], table)
        for table in source["tables"]
        for line in range(table["firstRow"], table["lastRow"] + 1)
    )
    with Client() as client:
        rows = list(client.monthly_load_forecasts.read(data, filename=source["file"]))
    assert len(rows) == len(coordinates)
    for actual, (line, column, table) in zip(rows, coordinates, strict=True):
        grid = grids[table["sheet"]]
        values = grid[line - 1][column - 1 : column + 3]
        header = grid[table["headerRow"] - 1]
        expected_year = int(values[0]) if isinstance(values[0], (int, float)) else None
        expected_month = int(values[1]) if isinstance(values[1], (int, float)) else None
        assert (actual.forecastYear, actual.forecastMonth) == (
            expected_year,
            expected_month,
        )
        assert actual.peakDemand == number(values[2])
        assert actual.energy == number(values[3])
        assert actual.sourceTitle == table["title"]
        assert actual.sourcePeakLabel == header[column + 1]
        assert actual.sourceEnergyLabel == header[column + 2]
        assert actual.peakUnit == ("MW" if header[column + 1] == "Peak (MW)" else None)
        assert actual.energyUnit == (
            "MWh" if header[column + 2].startswith("Energy (") else None
        )
        assert (
            actual.sourceMember,
            actual.sourceSheet,
            actual.sourceRow,
            actual.sourceColumn,
        ) == (source["file"], table["sheet"], line, column)
        assert actual.sourceFile is None
        assert (
            MonthlyLoadForecast.model_validate_json(actual.model_dump_json()) == actual
        )


def test_2025_independent_date_columns_and_missing_units_are_not_repaired():
    source = next(s for s in SOURCES if "/2025/" in s["url"])
    with Client() as client:
        rows = list(client.monthly_load_forecasts.read(original(source)))
    adjusted = [r for r in rows if r.sourceTitle == "ERCOT Adjusted Forecast"]
    tsp = [r for r in rows if r.sourceTitle == "TSP Provided Forecast"]
    assert len(adjusted) == 240 and len(tsp) == 241
    assert (adjusted[0].forecastYear, adjusted[0].forecastMonth) == (2025, 1)
    assert tsp[0].forecastYear is None and tsp[0].forecastMonth is None
    assert tsp[0].peakDemand == Decimal("70716.52")
    assert tsp[0].energy == Decimal("38585578.513")
    assert (tsp[1].forecastYear, tsp[1].forecastMonth) == (2025, 1)
    assert tsp[1].peakDemand == Decimal("69131.27")
    assert (tsp[-1].forecastYear, tsp[-1].forecastMonth) == (2044, 12)
    assert tsp[-1].peakDemand is None and tsp[-1].energy is None
    assert all(r.peakUnit is None and r.energyUnit is None for r in rows)
    assert all(r.sourceEnergyLabel == "Annual Energy" for r in rows)


def test_2024_large_load_assumption_is_retained():
    source = next(s for s in SOURCES if "/2024/" in s["url"])
    with Client() as client:
        row = next(client.monthly_load_forecasts.read(original(source)))
    assert row.sourceNotes == [
        source_cells(original(source))["Monthly Peak and Energy"][0][4]
    ]
    assert "15% LFL during 4CP months" in row.sourceNotes[0]


def test_discovery_and_predicate_can_select_original_forecast_vintage():
    by_url = {s["url"]: s for s in SOURCES}
    calls = []
    with ZipFile(ROOT.parent / "peak-forecasts/indexes.zip") as archive:
        indexes = {n: archive.read(n) for n in archive.namelist()}

    def respond(request):
        url = str(request.url)
        calls.append(url)
        if url in by_url:
            return httpx.Response(200, content=original(by_url[url]))
        name = url.rsplit("/", 1)[-1]
        return httpx.Response(
            200, content=indexes[("root" if name == "forecast" else name) + ".html"]
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as http,
        Client(client=http) as client,
    ):
        service = client.monthly_load_forecasts
        assert {f.url for f in service.files()} == set(by_url)
        rows = list(
            service.rows(
                where=lambda r: (
                    r.sourceFile is not None and "/2025/" in r.sourceFile.url
                )
            )
        )
        assert len(rows) == 481
        assert all(r.sourceFile.url in by_url for r in rows)
        assert len([u for u in calls if u in by_url]) == len(SOURCES)
        assert all(u.startswith("https://www.ercot.com/") for u in calls)
