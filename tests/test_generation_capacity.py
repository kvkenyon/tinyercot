from collections import Counter
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, GenerationCapacityForecast

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/generation-capacity/Generation_Resource_Forecast_May2026.xlsx"
)
URL = "https://www.ercot.com/files/docs/2026/05/18/Generation_Resource_Forecast_May2026.xlsx"


@pytest.fixture(scope="module")
def forecast():
    with Client() as client:
        return next(
            client.generation_capacity.read(FIXTURE.read_bytes(), filename=FIXTURE.name)
        )


@pytest.fixture(scope="module")
def workbook():
    book = openpyxl.load_workbook(FIXTURE, read_only=True, data_only=True)
    yield book
    book.close()


def number(value):
    return None if value is None else Decimal(str(value))


def test_every_published_unit_field_and_seasonal_value(forecast, workbook):
    rows = list(workbook["Unit Details"].values)
    assert len(forecast.resources) == len(rows) - 3 == 1836
    fields = [
        "name",
        "interconnectionRequest",
        "unitCode",
        "technology",
        "fuel",
        "cdrStatus",
        "cdrResourceAttribute",
        "county",
        "zone",
        "inServiceDate",
    ]
    for row, source in zip(forecast.resources, rows[3:], strict=True):
        assert row.sourceRow >= 4 and rows[row.sourceRow - 1] == source
        for field, value in zip(fields, source[:10], strict=True):
            assert getattr(row, field) == (
                value.date() if isinstance(value, datetime) else value
            )
        assert row.installedCapacityMW == number(source[10])
        assert len(row.capabilities) == 20
        for c, capability in enumerate(row.capabilities, 12):
            assert capability.sourceColumn == c
            assert capability.capacityMW == number(source[c - 1])
            assert capability.period == str(rows[2][c - 1])
            assert (
                capability.season
                == ["summer", "winter", "spring", "fall"][(c - 12) // 5]
            )


def test_summary_values_and_hierarchy(forecast, workbook):
    rows = list(workbook["Capacity by Resource Category"].rows)
    assert len(forecast.categories) == 47
    assert Counter(r.section for r in forecast.categories) == {
        "operational": 26,
        "planned": 20,
        "total": 1,
    }
    for row in forecast.categories:
        source = rows[row.sourceRow - 1]
        assert row.categoryPath[-1] == source[1].value
        assert row.sourceIndent == source[1].alignment.indent
        assert row.installedCapacityMW == number(source[2].value)
        assert len(row.capabilities) == 10
        for c, capability in enumerate(row.capabilities, 4):
            assert capability.capacityMW == number(source[c - 1].value)
            assert capability.sourceColumn == c
            assert capability.period == str(rows[1][c - 1].value)
            assert capability.season == ("summer" if c < 9 else "winter")
    paths = {tuple(r.categoryPath) for r in forecast.categories}
    assert ("Renewable, Intermittent", "Solar", "Other") in paths
    assert ("Renewable, Intermittent", "Wind", "Other") in paths
    assert ("Energy Storage", "Batteries") in paths
    assert forecast.categories[-1].categoryPath == ["Total Resources, MW"]


def test_reference_cells_and_independent_region_tables(forecast, workbook):
    mapping = list(workbook["Wind-Solar Region Mapping"].values)
    expected = {
        (fuel, r, str(cells[c]), str(cells[c + 1]))
        for r, cells in enumerate(mapping[4:], 5)
        for fuel, c in [("wind", 0), ("solar", 3)]
        if cells[c] is not None
    }
    actual = {(r.fuel, r.sourceRow, r.county, r.region) for r in forecast.regions}
    assert actual == expected and len(actual) == len(forecast.regions)
    assert len(actual) == 508
    expected_notes = {
        (sheet.title, r, c, value)
        for sheet in workbook
        if sheet.title in ["Information", "Definitions", "Acronyms"]
        for r, cells in enumerate(sheet.values, 1)
        for c, value in enumerate(cells, 1)
        if isinstance(value, str) and value.strip()
    }
    actual_notes = {
        (n.sourceSheet, n.sourceRow, n.sourceColumn, n.text) for n in forecast.notes
    }
    assert expected_notes <= actual_notes
    for sheet, r, c, text in actual_notes:
        assert workbook[sheet].cell(r, c).value == text
    assert any("distinct from" in n.text.lower() for n in forecast.notes)
    assert any(
        "normal sustained operating conditions" in n.text.lower()
        for n in forecast.notes
    )


def test_scenarios_zeroes_and_missing_dates_survive_roundtrip(forecast):
    conversions = [
        r for r in forecast.resources if r.unitCode and r.unitCode.startswith("COLETO")
    ]
    assert len(conversions) > 1 and len({r.fuel for r in conversions}) > 1
    assert len([r for r in forecast.resources if r.inServiceDate is None]) == 5
    assert any(v.capacityMW == 0 for r in conversions for v in r.capabilities)
    assert (
        GenerationCapacityForecast.model_validate_json(forecast.model_dump_json())
        == forecast
    )


def test_anonymous_discovery_download_and_saved_zip(forecast):
    calls = []

    def handler(request):
        assert "authorization" not in request.headers
        calls.append(str(request.url))
        return (
            httpx.Response(200, content=FIXTURE.read_bytes())
            if str(request.url) == URL
            else httpx.Response(
                200, text=f'<a href="{URL}">Generation Resource Capacity Forecast</a>'
            )
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        assert list(
            client.generation_capacity.rows(where=lambda f: bool(f.resources))
        ) == [forecast]
        assert calls == ["https://www.ercot.com/gridinfo/resource", URL]
        data = BytesIO()
        with ZipFile(data, "w") as archive:
            archive.writestr("vintage/" + FIXTURE.name, FIXTURE.read_bytes())
        saved = next(client.generation_capacity.read(data.getvalue()))
        assert saved.sourceMember == "vintage/" + FIXTURE.name
        assert saved.resources == forecast.resources
        assert (
            list(
                client.generation_capacity.read(
                    FIXTURE.read_bytes(), where=lambda f: False
                )
            )
            == []
        )
