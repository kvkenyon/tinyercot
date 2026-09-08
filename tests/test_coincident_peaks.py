from collections import Counter
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, CoincidentPeakAllocation
from tinyercot._coincident_peaks import URL

FIXTURE = Path(__file__).resolve().parents[1] / "tools/inputs/four-cp/allocations.zip"


@pytest.fixture(scope="module")
def allocations():
    with Client() as client:
        return list(client.coincident_peaks.read_allocations(FIXTURE.read_bytes()))


def test_complete_captured_annual_tables(allocations):
    assert len(allocations) == 4345
    assert {r.year for r in allocations} == set(range(1996, 2021))
    assert Counter(r.kind for r in allocations) == {
        "allocation": 4212,
        "comparison": 124,
        "revision_detail": 9,
    }
    assert all(
        [p.month for p in r.peaks] == ([] if r.year == 1997 else [6, 7, 8, 9])
        for r in allocations
    )
    assert all(
        p.timestamp is None or p.timestamp.year == r.year
        for r in allocations
        for p in r.peaks
    )
    assert (
        CoincidentPeakAllocation.model_validate_json(allocations[0].model_dump_json())
        == allocations[0]
    )


def test_kw_values_and_historical_loss_adjustments(allocations):
    row = next(r for r in allocations if r.year == 1996 and r.entity == "Brazos")
    assert row.unit == "kW"
    assert row.averageLoad == Decimal("1061825.0")
    assert row.gsuLosses == Decimal("2062.9")
    assert row.lossAdjustmentFactor == Decimal("0.03519461844061518")
    assert row.peaks[0].load == Decimal("1107900.0")
    assert row.peaks[0].timestamp == datetime.fromisoformat("1996-06-19T17:00:00")
    assert row.peaks[0].timestamp.tzinfo is None
    assert row.duns is None
    assert row.adjustmentUnit == "factor"


def test_summary_below_monthly_tables_preserves_percent_units(allocations):
    row = next(r for r in allocations if r.year == 1997)
    assert row.entity == "Austin Electric Utility" and row.controlArea == "AEUX"
    assert row.peaks == []
    assert row.averageLoad == Decimal("1783073.3")
    assert row.adjustmentUnit == "percent"
    assert row.lossAdjustmentFactor == Decimal("1.87853")
    assert (
        row.sourceSection
        == "PRELIMINARY 1997 Four Coincident Peak Load Calculation as of 2/16/98"
    )


def test_revisions_are_retained_without_recomputing_shares(allocations):
    rows = [
        r
        for r in allocations
        if r.year == 2008
        and r.entity == "CENTERPOINT ENERGY HOUSTON ELECTRIC LLC (TDSP)"
    ]
    assert len(rows) == 2 and rows[0].sourceMember != rows[1].sourceMember
    assert rows[0].loadRatioShare == Decimal("0.25391237655230137")
    assert rows[1].oldLoadRatioShare == rows[0].loadRatioShare
    assert rows[1].loadRatioShareDifference == Decimal("0.000007873824533377594")
    assert rows[1].loadRatioShare == Decimal("0.25392025037683474")


def test_revision_sections_keep_year_and_missing_share(allocations):
    rows = [r for r in allocations if r.kind == "revision_detail"]
    assert all(r.year == 2019 for r in rows)
    assert rows[0].sourceSection == "ORIGINALLY FILED NUMBERS"
    revised = next(
        r
        for r in rows
        if r.sourceSection == "NEW AEP TEXAS CENTRAL LOAD PLUS Sharyland/McAllen"
    )
    assert revised.averageLoad == Decimal("5019.420838")
    assert revised.loadRatioShare is None
    assert revised.peaks[0].timestamp == datetime.fromisoformat("2019-06-19T17:00:00")


def test_modern_mw_and_string_identifiers(allocations):
    row = next(
        r
        for r in allocations
        if r.year == 2020 and r.entity == "AEP TEXAS CENTRAL COMPANY (TDSP)"
    )
    assert row.unit == "MW" and row.entityCode == "5"
    assert row.duns == "007924772"
    assert row.averageLoad == Decimal("4981.34814")
    assert row.peaks[-1].timestamp == datetime.fromisoformat("2020-09-01T14:30:00")
    assert row.gsuLosses is None


def test_missing_peak_clocks_are_not_inferred(allocations):
    row = next(r for r in allocations if r.year == 2001)
    assert all(p.timestamp is None for p in row.peaks)


def test_missing_first_month_does_not_drop_entity():
    with ZipFile(FIXTURE) as archive:
        name = next(n for n in archive.namelist() if n.endswith("Calculation2020.xlsx"))
        book = openpyxl.load_workbook(BytesIO(archive.read(name)))
    book.worksheets[0].cell(4, 4).value = None
    data = BytesIO()
    book.save(data)
    book.close()
    with Client() as client:
        row = next(client.coincident_peaks.read_allocations(data.getvalue()))
    assert row.entity == "AEP TEXAS CENTRAL COMPANY (TDSP)"
    assert row.peaks[0].load is None
    assert row.peaks[1].load == Decimal("5051.084372")


def test_anonymous_download_and_query_filters():
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        return httpx.Response(200, content=FIXTURE.read_bytes())

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.coincident_peaks.allocations(
                year_from=2020, year_to=2020, entity="AEP TEXAS CENTRAL COMPANY (TDSP)"
            )
        )
        assert len(rows) == 1 and rows[0].year == 2020
        with pytest.raises(ValueError, match="year_from"):
            list(client.coincident_peaks.allocations(year_from=2020, year_to=2019))
    assert requested == [URL]
