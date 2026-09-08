from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import CapacityProject, CapacityTotals, Client

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/public-tables/capacity-changes.zip"
)


@pytest.fixture(scope="module")
def records():
    with Client() as client:
        return (
            list(client.capacity_changes.read_projects(FIXTURE.read_bytes())),
            list(client.capacity_changes.read_totals(FIXTURE.read_bytes())),
        )


def test_original_project_rows_dates_and_capacities(records):
    actual = {(r.sourceMember, r.sourceSheet, r.sourceRow): r for r in records[0]}
    expected_keys = set()
    with ZipFile(FIXTURE) as archive:
        for member in archive.namelist():
            book = openpyxl.load_workbook(
                BytesIO(archive.read(member)), read_only=True, data_only=True
            )
            try:
                for sheet in book:
                    sheet.reset_dimensions()
                    rows = list(sheet.values)
                    start = next((r.index("INR") for r in rows if "INR" in r), None)
                    if start is None:
                        continue
                    labels = []
                    for n, cells in enumerate(rows, 1):
                        right = cells[start:]
                        if len(right) > 1 and right[1] == "Project Name":
                            labels = [v for v in right if v is not None]
                        elif len(right) > 1 and isinstance(right[1], str):
                            key = (member, sheet.title, n)
                            expected_keys.add(key)
                            row = actual[key]
                            original = dict(zip(labels, right))
                            assert row.identifier == right[0]
                            assert row.name == original["Project Name"]
                            assert row.county == original["County"]
                            assert row.projectedCOD == original["Projected COD"].date()
                            assert row.capacityMW == Decimal(
                                str(original["Capacity (MW)"])
                            )
                            assert row.reportedYear == original["Year"]
                            assert row.financialSecurity == original.get(
                                "Financial Security"
                            )
                            assert row.sourceColumns == labels
                            for field, header in (
                                ("interconnectionAgreementSigned", "IA Signed"),
                                (
                                    "approvedForSynchronization",
                                    "Approved for Synchronization",
                                ),
                            ):
                                value = original.get(header)
                                expected = (
                                    value.date()
                                    if isinstance(value, datetime)
                                    else value
                                )
                                assert getattr(row, field) == expected
            finally:
                book.close()
    assert set(actual) == expected_keys and len(actual) == len(records[0])


def test_absent_project_table_and_original_monthly_periods(records):
    projects, totals = records
    early_battery = [
        r
        for r in totals
        if "September_2018" in r.sourceMember and r.sourceSheet == "Battery Chart"
    ]
    assert [r.period for r in early_battery] == list(range(2012, 2019))
    assert not any(
        "September_2018" in r.sourceMember and r.sourceSheet == "Battery Chart"
        for r in projects
    )
    monthly = next(r for r in totals if "November_2020_monthly" in r.sourceMember)
    assert monthly.sourcePeriodLabel == "Year"
    assert monthly.period == date(2020, 11, 20)
    assert monthly.cumulativeInstalledAndSignedMW == Decimal("26874.980000000003")
    assert monthly.cumulativeInstalledMW == Decimal("25120.58")
    assert monthly.cumulativeSynchronizedMW == Decimal("1754.4")
    assert monthly.cumulativeOperationalMW is None
    assert "Cumulative MW Synchronized" in monthly.sourceColumns
    for row in (early_battery[0], monthly):
        assert CapacityTotals.model_validate_json(row.model_dump_json()) == row


def test_agreement_statuses_resource_codes_and_project_comments(records):
    projects, totals = records
    statuses = {
        r.interconnectionAgreementSigned
        for r in projects
        if isinstance(r.interconnectionAgreementSigned, str)
    }
    assert statuses == {"12/31/1899", "Not Required", "Date Not Available"}
    dgr = next(r for r in projects if r.identifier == "BRP_PBL2_UNIT1")
    assert dgr.projectedCOD == date(2020, 12, 31) and dgr.reportedYear == 2022
    assert dgr.approvedForSynchronization == date(2021, 6, 25)
    comment = next(r for r in projects if r.identifier == "21INR0538" and r.comments)
    assert "rescinded on 3/9/2022" in comment.comments
    assert any(
        r.dgrComments
        == "All Capacities have been approved for synchronization to the grid"
        for r in totals
    )
    assert {"DGRs", "Small Generator", "Small Generators"} <= {
        r.sourceGroup for r in projects
    }
    assert CapacityProject.model_validate_json(dgr.model_dump_json()) == dgr


def test_corrected_financial_security_keeps_original_missing_values(records):
    projects = [
        r
        for r in records[0]
        if r.reportMonth == date(2023, 10, 1)
        and r.sourceSheet == "Battery Chart"
        and r.sourceGroup
    ]
    original = [r for r in projects if "Corrected" not in r.sourceMember]
    corrected = [r for r in projects if "Corrected" in r.sourceMember]
    assert len(original) == len(corrected) == 60
    assert Counter(r.financialSecurity for r in original) == {None: 58, "Yes": 2}
    assert Counter(r.financialSecurity for r in corrected) == {"Yes": 56, "No": 4}
    assert all(
        any("missing values" in note for note in r.sourceNotes) for r in corrected
    )
    assert all(not r.sourceNotes for r in original)


def test_companion_project_dates_and_blank_capacity_series_stay_distinct(records):
    projects, totals = records
    repower = [
        r
        for r in projects
        if r.reportMonth == date(2026, 7, 1) and r.identifier == "20INR0286"
    ]
    assert len(repower) == 2
    assert {r.projectedCOD for r in repower} == {date(2026, 5, 1), date(2026, 12, 19)}
    blank = [
        r
        for r in totals
        if "April_2025.xlsx" in r.sourceMember
        and "Small Generator" in r.sourceColumns
        and r.smallGeneratorsMW is None
    ]
    assert {(r.sourceSheet, r.period) for r in blank} == {
        ("Wind Chart", 2028),
        ("Solar Chart", 2030),
    }
    latest = next(r for r in totals if "July_2026.xlsx" in r.sourceMember)
    assert latest.cumulativeOperationalMW is not None
    assert (
        latest.cumulativeInstalledMW is None and latest.cumulativeSynchronizedMW is None
    )


@pytest.mark.parametrize("method", ["projects", "totals"])
def test_anonymous_discovery_preserves_same_filename_urls(method):
    basename = "Capacity_Changes_by_Fuel_Type_Charts_November_2018.xlsx"
    urls = [
        f"https://www.ercot.com/files/docs/2018/12/{day}/{basename}"
        for day in ("04", "11")
    ]
    with ZipFile(FIXTURE) as archive:
        payloads = {
            url: archive.read(url.removeprefix("https://www.ercot.com/files/docs/"))
            for url in urls
        }

    def handler(request):
        assert "authorization" not in request.headers
        if str(request.url) in payloads:
            return httpx.Response(200, content=payloads[str(request.url)])
        if request.url.path == "/gridinfo/resource":
            return httpx.Response(
                200, text='<a href="/gridinfo/resource/2018">2018</a>'
            )
        assert request.url.path == "/gridinfo/resource/2018"
        return httpx.Response(
            200,
            text="".join(
                f'<a href="{url}">Capacity Changes by Fuel Type Charts, November 2018</a>'
                for url in urls
            ),
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            getattr(client.capacity_changes, method)(
                where=lambda r: r.reportMonth == date(2018, 11, 1)
            )
        )
    assert rows and {r.sourceFile.url for r in rows} == set(urls)
    assert {r.sourceMember for r in rows} == {basename}


def test_discovery_includes_monthly_prefix_and_original_capitalization():
    links = {
        "https://www.ercot.com/files/docs/2020/12/09/Capacity_Changes_by_Fuel_Type_Charts_November_2020_monthly.xlsx": "Monthly Capacity Changes by Fuel Type Charts, November 2020",
        "https://www.ercot.com/files/docs/2023/09/07/capacity-changes-by-fuel-type-charts_august_2023.xlsx": "Capacity Changes By Fuel Type Charts August 2023",
        "https://www.ercot.com/files/docs/2023/09/07/capacity-changes-by-fuel-type-charts_august_2023_plannedmonthly.xlsx": "Capacity Changes By Fuel Type Charts August 2023 Plannedmonthly",
    }
    page = "".join(f'<a href="{url}">{title}</a>' for url, title in links.items())
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text=page)
            )
        ) as http,
        Client(client=http) as client,
    ):
        assert {f.url: f.title for f in client.capacity_changes.files()} == links


def test_saved_bytes_without_a_filename_do_not_invent_report_month():
    with ZipFile(FIXTURE) as archive:
        data = archive.read(archive.namelist()[0])
    with Client() as client:
        rows = list(client.capacity_changes.read_projects(data))
    assert rows and all(r.reportMonth is None and r.sourceFile is None for r in rows)
