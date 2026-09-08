"""Peak-demand forecasts compared with complete original XLS/XLSX sources."""

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

from tinyercot import Client, PeakDemandForecast

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/peak-forecasts"
SOURCES = json.loads((ROOT / "sources.json").read_text())
SUMMARY_FIELDS = {
    "Official Forecast 50/50": "p50MW",
    "P50": "p50MW",
    "90th Percentile": "p90MW",
    "P90": "p90MW",
    "ercot_90th": "p90MW",
    "Forecast": "forecastMW",
    "Contracts": "contractsMW",
    "Officer Letters": "officerLettersMW",
    "Total Large Loads": "totalLargeLoadsMW",
}


def original(source):
    with ZipFile(ROOT / "workbooks.zip") as archive:
        return archive.read(source["file"])


def cells(data):
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
def test_all_forecast_tables_match_original_source_cells(source):
    data = original(source)
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
    grids = cells(data)
    with Client() as client:
        actual = list(client.peak_demand_forecasts.read(data, filename=source["file"]))
    expected_coordinates = [
        (table, row)
        for table in source["tables"]
        for row in range(table["firstRow"], table["lastRow"] + 1)
    ]
    assert len(actual) == len(expected_coordinates)
    for forecast, (table, line) in zip(actual, expected_coordinates, strict=True):
        grid = grids[table["sheet"]]
        row, header = grid[line - 1], grid[table["headerRow"] - 1]
        title = next(v for v in grid[table["titleRow"] - 1] if v not in (None, ""))
        assert forecast.forecastYear == int(row[0])
        assert forecast.sourceTitle == title
        assert (forecast.sourceMember, forecast.sourceSheet, forecast.sourceRow) == (
            source["file"],
            table["sheet"],
            line,
        )
        weather, extras, labels = {}, {}, {}
        for column, value in enumerate(row[1:], 1):
            heading = header[column] if column < len(header) else None
            if heading in (None, ""):
                if value not in (None, ""):
                    extras[column + 1] = number(value)
            elif str(heading) in SUMMARY_FIELDS:
                field = SUMMARY_FIELDS[str(heading)]
                assert getattr(forecast, field) == number(value)
                labels[field] = str(heading)
            else:
                weather[int(float(heading))] = number(value)
        assert forecast.weatherYearMW == weather
        assert forecast.sourceExtraValues == extras
        assert forecast.sourceSummaryLabels == labels
        for field in set(SUMMARY_FIELDS.values()) - labels.keys():
            assert getattr(forecast, field) is None
        assert (
            PeakDemandForecast.model_validate_json(forecast.model_dump_json())
            == forecast
        )


def test_gross_net_pv_and_new_large_load_assumptions_remain_distinct():
    with Client() as client:
        source = next(s for s in SOURCES if "/2023/" in s["url"])
        rows = list(client.peak_demand_forecasts.read(original(source)))
        assert [r.demandBasis for r in rows] == ["gross"] * 10 + ["net"] * 10 + [
            "rooftop_pv"
        ] * 10
        assert rows[0].forecastYear == 2023 and rows[20].forecastYear == 2022
        assert len(rows[0].sourceExtraValues) == 15
        assert rows[0].forecastMW is not None and rows[0].p50MW is None
        assert rows[20].p90MW is None
        source = next(s for s in SOURCES if "/2024/" in s["url"])
        row = next(client.peak_demand_forecasts.read(original(source)))
        assert row.demandBasis == "net"
        assert row.contractsMW is not None and row.officerLettersMW is not None
        assert row.totalLargeLoadsMW is not None and row.p90MW is None
        assert "15%" in row.sourceNotes[0]
        source = next(s for s in SOURCES if "/2025/04/" in s["url"])
        rows = list(client.peak_demand_forecasts.read(original(source)))
        assert rows[0].sourceSheet == "TSP Provided"
        assert rows[7].sourceSheet == "ERCOT Adjusted"
        assert rows[0].p90MW != rows[7].p90MW


def test_live_index_shapes_discover_all_vintages_and_rows_keep_file_metadata():
    calls = []
    by_url = {s["url"]: s for s in SOURCES}
    with ZipFile(ROOT / "indexes.zip") as archive:
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
        service = client.peak_demand_forecasts
        assert {f.url for f in service.files()} == set(by_url)
        calls.clear()
        rows = list(
            service.rows(
                where=lambda r: r.forecastYear == 2025 and r.sourceFile is not None
            )
        )
        assert rows and all(r.sourceFile.url in by_url for r in rows)
        assert len([u for u in calls if u in by_url]) == len(SOURCES)
        assert all(u.startswith("https://www.ercot.com/") for u in calls)
