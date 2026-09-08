from datetime import date, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import get_args
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, MoraBalance, MoraBalanceMetric, MoraCapacity

TABLES = Path(__file__).resolve().parents[1] / "tools/inputs/public-tables"
FIXTURES = ("mora-percentiles.zip", "mora-resources.zip", "mora-summaries.zip")


@pytest.fixture(scope="module")
def summaries():
    with Client() as client:
        return {
            method: [
                row
                for fixture in FIXTURES
                for row in getattr(client.resource_outlook, method)(
                    (TABLES / fixture).read_bytes()
                )
            ]
            for method in ("read_capacities", "read_balance")
        }


@pytest.mark.parametrize(
    ("method", "sheet_name", "label_column", "value_column"),
    [
        ("read_capacities", "Capacity by Resource Category", 1, 3),
        ("read_balance", "Monthly Outlook", 4, 7),
    ],
)
def test_original_cells_scenarios_and_notes(
    summaries, method, sheet_name, label_column, value_column
):
    for fixture in FIXTURES:
        with ZipFile(TABLES / fixture) as archive:
            for member in archive.namelist():
                book = openpyxl.load_workbook(
                    BytesIO(archive.read(member)), read_only=True, data_only=True
                )
                try:
                    sheet = book[sheet_name]
                    sheet.reset_dimensions()
                    cells = list(sheet.values)
                    actual = {
                        r.sourceRow: r
                        for r in summaries[method]
                        if r.sourceMember == member
                    }
                    # Each source row with a numeric cell must be accounted for.
                    expected = {
                        n
                        for n, row in enumerate(cells, 1)
                        if any(isinstance(v, (int, float)) for v in row)
                    }
                    assert set(actual) == expected
                    notes = [
                        v
                        for row in cells
                        for v in row
                        if isinstance(v, str) and v.startswith("[")
                    ]
                    header = (
                        cells[1]
                        if method == "read_capacities"
                        else next(r for r in cells if "Loads and Resources (MW)" in r)
                    )
                    columns = [
                        i
                        for i, label in enumerate(header)
                        if i >= value_column and label is not None
                    ]
                    for n, row in actual.items():
                        original = cells[n - 1]
                        assert (
                            row.sourceNotes == notes and row.sourceSheet == sheet_name
                        )
                        if method == "read_capacities":
                            assert row.resourcePath[-1] == original[label_column]
                            assert row.installedCapacityMW == Decimal(str(original[2]))
                            values = row.availableCapacity
                        else:
                            assert row.sourceMetric == original[label_column]
                            values = row.values
                        assert [v.valueMW for v in values] == [
                            None if original[i] is None else Decimal(str(original[i]))
                            for i in columns
                        ]
                        assert [v.sourceScenario for v in values] == [
                            header[i] for i in columns
                        ]
                finally:
                    book.close()


def test_category_hierarchy_and_battery_contribution(summaries):
    rows = [
        r
        for r in summaries["read_capacities"]
        if r.sourceMember == "MORA_November2026.xlsx"
    ]
    battery = next(
        r
        for r in rows
        if r.section == "operational"
        and r.resourcePath == ["Energy Storage", "Batteries"]
    )
    assert battery.installedCapacityMW == Decimal("20965.520000000004")
    assert battery.availableCapacity[0].valueMW == Decimal("7853.775399999997")
    assert battery.availableCapacity[0].hourEnding == time(19)
    assert battery.availableCapacity[0].timeZone == "CST"
    assert {
        tuple(r.resourcePath)
        for r in rows
        if r.section == "operational" and r.resourcePath[-1] == "Other"
    } == {
        ("Renewable, Intermittent [6]", "Wind", "Other"),
        ("Energy Storage", "Other"),
    }
    assert sum(r.section == "total" for r in rows) == 1
    assert MoraCapacity.model_validate_json(battery.model_dump_json()) == battery


def test_older_hours_revisions_and_missing_heading(summaries):
    early = [
        r for r in summaries["read_capacities"] if r.reportMonth == date(2023, 12, 1)
    ]
    assert len(early) == 84
    assert {r.sourceMember for r in early} == {
        "MORA_December2023.xlsx",
        "MORA_December2023_v2.xlsx",
    }
    assert all(
        [v.hourEnding for v in r.availableCapacity] == [time(8), time(17)]
        for r in early
    )
    assert all(v.timeZone is None for r in early for v in r.availableCapacity)
    march = next(
        r for r in summaries["read_capacities"] if r.reportMonth == date(2024, 3, 1)
    )
    assert march.sourceAvailableCapacityLabel is None
    assert [v.hourEnding for v in march.availableCapacity] == [time(18), time(8)]
    assert "Late March" in march.availableCapacity[0].sourceScenario
    assert "Early March" in march.availableCapacity[1].sourceScenario


def test_same_hour_scenarios_and_metric_definitions_stay_distinct(summaries):
    rows = summaries["read_balance"]
    reserve = next(
        r
        for r in rows
        if r.reportMonth == date(2024, 4, 1) and r.metric == "normal_condition_reserves"
    )
    assert [v.hourEnding for v in reserve.values] == [time(20), time(20)]
    assert [v.valueMW for v in reserve.values] == [
        Decimal("21097.36730431109"),
        Decimal("4457.62041931109"),
    ]
    assert reserve.values[0].sourceScenario != reserve.values[1].sourceScenario
    assert set(get_args(MoraBalanceMetric)) == {r.metric for r in rows}
    assert MoraBalance.model_validate_json(reserve.model_dump_json()) == reserve


@pytest.mark.parametrize(
    ("method", "read_method", "count"),
    [("capacities", "read_capacities", 41), ("balance", "read_balance", 26)],
)
def test_query_and_saved_file_predicates(method, read_method, count):
    url = "https://www.ercot.com/files/docs/2026/09/03/MORA_November2026.xlsx"
    with ZipFile(TABLES / "mora-percentiles.zip") as archive:
        data = archive.read("MORA_November2026.xlsx")

    def handler(request):
        assert "authorization" not in request.headers
        if str(request.url) == url:
            return httpx.Response(200, content=data)
        assert request.url.path == "/gridinfo/resource"
        return httpx.Response(
            200,
            text=f'<a href="{url}">Monthly Outlook for Resource Adequacy (MORA) November 2026</a>',
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        live = list(
            getattr(client.resource_outlook, method)(
                where=lambda r: r.reportMonth == date(2026, 11, 1)
            )
        )
        saved = list(
            getattr(client.resource_outlook, read_method)(
                data,
                filename="MORA_November2026.xlsx",
                where=lambda r: r.reportMonth == date(2026, 11, 1),
            )
        )
    assert live == saved and len(live) == count


def test_unknown_balance_quantity_is_not_discarded():
    with ZipFile(TABLES / "mora-percentiles.zip") as archive:
        book = openpyxl.load_workbook(BytesIO(archive.read("MORA_November2026.xlsx")))
    book["Monthly Outlook"]["E52"] = "A new load definition"
    data = BytesIO()
    book.save(data)
    book.close()
    with Client() as client, pytest.raises(ValueError, match="Unknown balance metric"):
        list(client.resource_outlook.read_balance(data.getvalue()))
