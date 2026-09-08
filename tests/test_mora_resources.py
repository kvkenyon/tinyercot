from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, MoraResource

TABLES = Path(__file__).resolve().parents[1] / "tools/inputs/public-tables"


@pytest.fixture(scope="module")
def resources():
    with Client() as client:
        return [
            row
            for fixture in ("mora-percentiles.zip", "mora-resources.zip")
            for row in client.resource_outlook.read_resources(
                (TABLES / fixture).read_bytes()
            )
        ]


def test_original_capacity_cells_labels_and_notes(resources):
    by_source = {(r.sourceMember, r.sourceRow): r for r in resources}
    assert len(by_source) == len(resources) == 19905
    for fixture in ("mora-percentiles.zip", "mora-resources.zip"):
        with ZipFile(TABLES / fixture) as archive:
            for member in archive.namelist():
                book = openpyxl.load_workbook(
                    BytesIO(archive.read(member)), read_only=True, data_only=True
                )
                try:
                    sheet = book["Resource Details"]
                    sheet.reset_dimensions()
                    source = list(sheet.values)
                    last_row = max(n for m, n in by_source if m == member)
                    notes = [
                        r[1]
                        for r in source[last_row:]
                        if len(r) > 1 and isinstance(r[1], str) and r[1]
                    ]
                    for (m, n), row in by_source.items():
                        if m != member:
                            continue
                        original = tuple(source[n - 1]) + (None,) * 10
                        assert row.name == original[1]
                        for value, cell in (
                            (row.installedCapacityMW, original[8]),
                            (row.reportedCapacityMW, original[9]),
                        ):
                            assert value == (
                                None if cell is None else Decimal(str(cell))
                            )
                        assert row.sourceInstalledCapacityLabel == source[1][8]
                        assert row.sourceCapacityLabel == source[1][9]
                        assert row.sourceInServiceLabel == source[1][7]
                        assert row.sourceNotes == notes
                finally:
                    book.close()


def test_service_years_dates_and_excel_errors_remain_distinct(resources):
    by_source = {(r.sourceMember, r.sourceRow): r for r in resources}
    year = by_source["MORA_October2025.xlsx", 3]
    projected = by_source["MORA_July2025.xlsx", 1393]
    unknown = by_source["MORA_Apr2024.xlsx", 1035]
    assert year.inService == 1993 and type(year.inService) is int
    assert projected.inService == date(2026, 5, 1)
    assert projected.reportMonth == date(2025, 7, 1)
    assert projected.category.startswith("Planned Thermal Resources")
    assert projected.unitCode is None
    assert unknown.inService == "#N/A"
    assert unknown.unitCode == "GOLINDA_UNIT1"
    assert unknown.installedCapacityMW == Decimal("101.1")
    for row in (year, projected, unknown):
        assert MoraResource.model_validate_json(row.model_dump_json()) == row


def test_totals_and_adjustments_with_codes_are_summaries(resources):
    by_source = {(r.sourceMember, r.sourceRow): r for r in resources}
    for number, code in (
        (404, "THERMAL_OPERATIONAL"),
        (443, "HYDRO_OPERATIONAL"),
        (479, "PUN_CAP_ADJUST"),
        (784, "WIND_OPERATIONAL_C"),
    ):
        row = by_source["MORA_December2023.xlsx", number]
        assert row.kind == "summary" and row.unitCode == code
    negative = by_source["MORA_Apr2024.xlsx", 483]
    assert negative.kind == "summary"
    assert negative.installedCapacityMW is None
    assert negative.reportedCapacityMW == Decimal(-71)
    missing = by_source["MORA_March2025.xlsx", 1343]
    assert missing.kind == "summary"
    assert missing.installedCapacityMW == 0 and missing.reportedCapacityMW is None
    # Column L repeats these published J values without its own table heading.
    unit = by_source["MORA_January2026.xlsx", 1467]
    total = by_source["MORA_January2026.xlsx", 1483]
    assert unit.kind == "unit" and unit.reportedCapacityMW == Decimal("24.2")
    assert total.kind == "summary"
    assert total.reportedCapacityMW == Decimal("763.9000000000001")
    # Column O has a helper zero on this section heading, not a resource row.
    assert ("MORA_March2025.xlsx", 1354) not in by_source


def test_missing_category_and_original_revisions_are_preserved(resources):
    assert Counter(r.sourceMember for r in resources if r.category is None) == {
        "MORA_October2025.xlsx": 402
    }
    early = [r for r in resources if r.reportMonth == date(2023, 12, 1)]
    assert Counter(r.sourceMember for r in early) == {
        "MORA_December2023.xlsx": 1432,
        "MORA_December2023_v2.xlsx": 1432,
    }
    assert {r.sourceCapacityLabel for r in early} == {"WINTER\nCAPACITY\n(MW)"}


def test_anonymous_resource_query_and_saved_nested_zip():
    url = "https://www.ercot.com/files/docs/2025/05/02/MORA_July2025.xlsx"
    with ZipFile(TABLES / "mora-resources.zip") as archive:
        content = archive.read("MORA_July2025.xlsx")

    def handler(request):
        assert "authorization" not in request.headers
        if request.url.path == "/gridinfo/resource":
            return httpx.Response(
                200,
                text=f'<a href="{url}">Monthly Outlook for Resource Adequacy (MORA) July 2025</a>',
            )
        assert str(request.url) == url
        return httpx.Response(200, content=content)

    outer = BytesIO()
    with ZipFile(outer, "w") as archive:
        archive.writestr("saved.zip", (TABLES / "mora-resources.zip").read_bytes())
    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        selected = list(
            client.resource_outlook.resources(
                where=lambda r: r.interconnectionRequestNumber == "26INR0049"
            )
        )
        saved = list(
            client.resource_outlook.read_resources(
                outer.getvalue(),
                where=lambda r: (
                    r.reportMonth == date(2025, 7, 1)
                    and r.interconnectionRequestNumber == "26INR0049"
                ),
            )
        )
    assert len(selected) == len(saved) == 1
    assert selected[0].inService == saved[0].inService == date(2026, 5, 1)
    assert selected[0].sourceMember == "MORA_July2025.xlsx"
    assert saved[0].sourceMember == "MORA_July2025.xlsx"
