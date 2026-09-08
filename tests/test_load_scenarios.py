"""Weather-year predictions and independent load adjustments from original files."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, HourlyLoadScenario

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/load-scenarios"
SOURCES = json.loads((ROOT / "sources.json").read_text())


def original(source):
    with ZipFile(ROOT / "samples.zip") as archive:
        return archive.read(source["file"])


def cells(source):
    with ZipFile(ROOT / "samples.zip") as archive:
        return json.loads(archive.read(source["file"] + ".json"))


def number(v):
    return None if v in (None, "") else Decimal(str(v))


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s["file"])
def test_all_source_years_components_dates_and_zone_labels(source):
    data = original(source)
    assert hashlib.sha256(data).hexdigest() == source["fixtureSha256"]
    grid = cells(source)
    offset = source["dateOffset"]
    with Client() as c:
        rows = list(c.hourly_load_scenarios.read(data, filename=source["file"]))
    assert len(rows) == 48
    for line, (actual, raw) in enumerate(zip(rows, grid[1:], strict=True), 2):
        assert actual.forecastDate == date(
            *(int(raw[i]) for i in source["clockColumns"][1:4])
        )
        assert actual.hour == raw[source["clockColumns"][4]]
        assert actual.sourceDate == (
            date.fromisoformat(raw[source["clockColumns"][0]][:10]) if offset else None
        )
        assert actual.weatherYearPredictions == {
            int(grid[0][i][5:]): number(raw[i]) for i in range(offset + 4, offset + 49)
        }
        assert len(actual.weatherYearPredictions) == 45
        for field, i in source["components"]:
            assert getattr(actual, field) == number(raw[i])
            assert actual.sourceLabels[field] == grid[0][i]
        for year in range(1980, 2025):
            assert (
                actual.sourceLabels[f"weatherYearPredictions.{year}"] == f"Pred_{year}"
            )
        col = source["zoneColumn"]
        label = source["sheet"] if col is None else raw[col]
        assert actual.sourceWeatherZone == label and actual.weatherZone == label.upper()
        assert actual.sourceWeatherZoneColumn == ("wzone" if col is not None else None)
        assert actual.unit is None and actual.sourceFile is None
        assert actual.sourceMarkers == {}
        assert (actual.sourceMember, actual.sourceSheet, actual.sourceRow) == (
            source["file"],
            source["sheet"],
            line,
        )
        assert (
            HourlyLoadScenario.model_validate_json(actual.model_dump_json()) == actual
        )


def test_missing_flexible_load_is_not_zero_and_scent_column_order_is_preserved():
    with Client() as c:
        rows = {
            s["title"]: next(c.hourly_load_scenarios.read(original(s))) for s in SOURCES
        }
    for zone in ["East", "South", "West"]:
        assert rows[zone].largeFlexibleLoad is None
        assert rows[zone].contractedLoad == 0
    assert rows["Coast"].largeFlexibleLoad > 0
    scent = rows["South Central"]
    assert scent.sourceWeatherZoneColumn is None and scent.weatherZone == "SCENT"
    assert scent.electricVehicles == Decimal("34.43155933856281")
    assert scent.rooftopPV == 0
    assert rows["South"].sourceDate is None and rows["West"].sourceDate is None


def test_discovery_and_typed_filter_use_all_eight_actual_index_links():
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
        Client(client=http) as c,
    ):
        assert {f.url for f in c.hourly_load_scenarios.files()} == set(sources)
        rows = list(
            c.hourly_load_scenarios.rows(
                where=lambda r: r.weatherZone == "SCENT" and r.hour == 24
            )
        )
    assert len(rows) == 2
    assert all(r.sourceFile.title == "South Central" for r in rows)
    assert all("mis" not in url.lower() for url in calls)


def workbook(header, rows):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Coast"
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def test_prediction_labels_missing_cells_and_repeated_hours_remain_literal():
    data = workbook(
        ["year", "month", "day", "hour", "Pred_1980", "Pred_2024", "wzone", "coast_ev"],
        [
            [2030, 11, 3, 2, None, 42, "Coast", 0],
            [2030, 11, 3, 2, 100, 200, "Coast", 1],
        ],
    )
    with Client() as c:
        rows = list(c.hourly_load_scenarios.read(data))
    assert len(rows) == 2 and rows[0].hour == rows[1].hour == 2
    assert rows[0].weatherYearPredictions == {1980: None, 2024: Decimal(42)}
    assert rows[1].weatherYearPredictions == {1980: Decimal(100), 2024: Decimal(200)}
    assert rows[0].sourceDate is None


def test_foreign_zone_component_does_not_get_assigned_to_the_row_zone():
    data = workbook(
        ["year", "month", "day", "hour", "Pred_1980", "wzone", "east_ev"],
        [[2030, 1, 1, 1, 100, "Coast", 1]],
    )
    with Client() as c, pytest.raises(ValueError, match="weather zone disagree"):
        list(c.hourly_load_scenarios.read(data))


def test_original_reference_error_remains_distinct_from_a_blank_prediction():
    source = next(s for s in SOURCES if s["title"] == "South")
    with ZipFile(ROOT / "samples.zip") as archive:
        data = archive.read(source["errorExcerpt"]["file"])
        expected = json.loads(archive.read("South-error.xlsx.json"))
    assert hashlib.sha256(data).hexdigest() == source["errorExcerpt"]["sha256"]
    with Client() as c:
        rows = list(c.hourly_load_scenarios.read(data, filename="South.xlsx"))
    assert len(rows) == 12
    for row, expected_row in zip(rows, expected["records"], strict=True):
        raw = expected_row["row"]
        assert row.forecastDate == date(*raw[:3]) and row.hour == raw[3]
        assert (
            row.sourceRow == expected_row["sourceRow"]
            and row.sourceMember == "South.xlsx"
        )
        assert row.weatherYearPredictions[2017] is None
        i = expected["header"].index("Pred_2017")
        assert row.sourceMarkers == {"Pred_2017": raw[i]}
        for year in range(1980, 2025):
            if year != 2017:
                i = expected["header"].index(f"Pred_{year}")
                assert row.weatherYearPredictions[year] == number(raw[i])
        assert HourlyLoadScenario.model_validate_json(row.model_dump_json()) == row


def test_text_markers_and_numeric_strings_remain_distinct():
    data = workbook(
        ["year", "month", "day", "hour", "Pred_2017", "Pred_2024", "wzone", "coast_ev"],
        [[2028, 3, 13, 2, ".", "123.45", "Coast", "#N/A"]],
    )
    with Client() as c:
        row = next(c.hourly_load_scenarios.read(data))
    assert row.weatherYearPredictions == {2017: None, 2024: Decimal("123.45")}
    assert row.electricVehicles is None
    assert row.sourceMarkers == {"Pred_2017": ".", "coast_ev": "#N/A"}
