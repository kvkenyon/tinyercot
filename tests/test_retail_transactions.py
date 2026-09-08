from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, RetailTransactionMonth

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/public-tables/retail-transactions.zip"
)
ARCHIVE_URL = "https://www.ercot.com/files/docs/2025/01/02/August-2026-Retail-Monthly-Transaction-Totals.zip"


@pytest.fixture(scope="module")
def retail_rows():
    with Client() as client:
        return list(client.retail_transactions.read(FIXTURE.read_bytes()))


def test_all_original_fixture_cells_dates_and_source_labels(retail_rows):
    actual = iter(retail_rows)
    with ZipFile(FIXTURE) as archive:
        assert len(archive.namelist()) == 5
        for member in archive.namelist():
            book = openpyxl.load_workbook(
                BytesIO(archive.read(member)), read_only=True, data_only=True
            )
            try:
                for sheet in book:
                    sheet.reset_dimensions()
                    source = sheet.values
                    header = next(source)
                    dates = []
                    for value in header[1:-2]:
                        month, day, year = map(int, value.split("/"))
                        dates.append(date(year, month, day))
                    for cells in source:
                        if all(v in (None, "") for v in cells):
                            continue
                        row = next(actual)
                        assert (
                            row.sourceMember == member
                            and row.sourceSheet == sheet.title
                        )
                        assert row.month == dates[0].replace(day=1)
                        assert row.transactionCode == (
                            None if cells[0] == "Grand Total" else cells[0]
                        )
                        assert len(row.days) == len(dates)
                        for value, day, original in zip(
                            row.days, dates, cells[1:-2], strict=True
                        ):
                            assert value.operatingDay == day and value.count == int(
                                original
                            )
                        assert row.reportedTotal == int(cells[-2])
                        assert row.reportedAveragePerDay == Decimal(cells[-1])
            finally:
                book.close()
    assert next(actual, None) is None
    assert len({r.transactionCode for r in retail_rows} - {None}) == 30
    assert (
        RetailTransactionMonth.model_validate_json(retail_rows[0].model_dump_json())
        == retail_rows[0]
    )


def test_unnamed_categories_and_totals_remain_distinct(retail_rows):
    unknown = [r for r in retail_rows if r.sourceSheet.startswith(" ")]
    assert len(unknown) == 8
    assert {r.sourceSheet for r in unknown} == {" Inbound", " Outbound"}
    assert {r.month for r in unknown} == {date(2025, 4, 1), date(2026, 1, 1)}
    assert sum(r.transactionCode is None for r in unknown) == 4
    by_source = Counter(
        (r.sourceMember, r.sourceSheet)
        for r in retail_rows
        if r.transactionCode is None
    )
    assert len(by_source) == 114 and set(by_source.values()) == {1}


def test_source_averages_are_not_recomputed_and_month_lengths_are_retained(retail_rows):
    rounded = [
        r
        for r in retail_rows
        if r.reportedAveragePerDay * len(r.days) != r.reportedTotal
    ]
    assert rounded
    assert all(
        r.reportedAveragePerDay == r.reportedAveragePerDay.to_integral_value()
        for r in retail_rows
    )
    assert {len(r.days) for r in retail_rows} == {28, 30, 31}
    # Categories overlap; each sheet's published total remains its own record.
    assert {"ERCOT Inbound", "Residential Inbound", "ONCOR to ERCOT"} <= {
        r.sourceSheet for r in retail_rows
    }


def test_current_archive_discovery_can_query_earlier_months():
    requested = []

    def handler(request):
        requested.append(str(request.url))
        assert "authorization" not in request.headers
        if str(request.url) == ARCHIVE_URL:
            return httpx.Response(200, content=FIXTURE.read_bytes())
        return httpx.Response(
            200, text=f'<a href="{ARCHIVE_URL}">Retail Monthly Transaction Totals</a>'
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.retail_transactions.rows(
                where=lambda r: (
                    r.month == date(2025, 1, 1)
                    and r.sourceSheet == "ERCOT Inbound"
                    and r.transactionCode is None
                ),
            )
        )
    assert len(rows) == 1
    assert [d.operatingDay for d in rows[0].days] == [
        date(2025, 1, d) for d in range(1, 32)
    ]
    assert requested == ["https://www.ercot.com/mktinfo/retail", ARCHIVE_URL]


def test_saved_file_filter_preserves_transaction_codes(retail_rows):
    with ZipFile(FIXTURE) as z:
        member = next(
            n for n in z.namelist() if n.endswith("1_2025 Monthly Retail Totals.xlsx")
        )
        data = z.read(member)
    with Client() as client:
        rows = list(
            client.retail_transactions.read(
                data,
                filename="saved.xlsx",
                where=lambda r: r.transactionCode == "814_06_MVI",
            )
        )
    expected = [
        r
        for r in retail_rows
        if r.sourceMember == member and r.transactionCode == "814_06_MVI"
    ]
    assert rows and len(rows) == len(expected)
    assert all(r.sourceMember == "saved.xlsx" for r in rows)
    assert [r.reportedTotal for r in rows] == [r.reportedTotal for r in expected]


def test_unknown_summary_header_fails_instead_of_losing_a_column():
    book = openpyxl.Workbook()
    book.active.append(["", "1/1/2026", "Grand Total", "Renamed Average"])
    data = BytesIO()
    book.save(data)
    book.close()
    with Client() as client, pytest.raises(ValueError, match="changed.xlsx/Sheet"):
        list(client.retail_transactions.read(data.getvalue(), filename="changed.xlsx"))
