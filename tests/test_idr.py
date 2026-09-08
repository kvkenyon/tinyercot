from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, IdrCompliance
from tinyercot._idr import INDEX_URL

FIXTURE = Path(__file__).resolve().parents[1] / "tools/inputs/idr/historical.zip"
ARCHIVE_URL = "https://www.ercot.com/files/docs/2009/03/02/idr_pcv_2009.zip"


@pytest.fixture(scope="module")
def compliance():
    with Client() as client:
        return list(
            client.idr_compliance.read(FIXTURE.read_bytes(), filename="capture.zip")
        )


def test_original_workbooks_cover_all_provider_layouts(compliance):
    assert len(compliance) == 4700
    assert len({r.sourceMember for r in compliance}) == 13
    assert all(r.sourceArchive == "capture.zip" for r in compliance)
    assert {
        "System",
        "Market",
        "CPL",
        "WTU",
        "AEP-C",
        "TXU",
        "ONCOR",
        "Shrylnd",
        "Sharyland",
    } <= {r.entity for r in compliance}
    assert (
        IdrCompliance.model_validate_json(compliance[0].model_dump_json())
        == compliance[0]
    )


def test_excel_errors_and_not_applicable_markers_are_not_numbers(compliance):
    assert Counter(r.status for r in compliance) == {
        None: 4426,
        "#N/A": 94,
        "Not MRE For Date": 180,
    }
    assert all(r.compliance is None for r in compliance if r.status)
    error = next(r for r in compliance if r.status == "#N/A")
    assert error.entity == "MVEC" and error.operatingDay == date(2002, 1, 31)
    assert error.reportRunDate == date(2003, 5, 23)


def test_zero_date_template_rows_do_not_create_1899_observations(compliance):
    rows = [r for r in compliance if r.sourceMember == "IDR PCV as of 06.28.2003.xls"]
    assert len(rows) == 140
    assert all(r.operatingDay.year >= 2002 for r in compliance)


def test_excel_and_multiline_run_dates_and_trade_day_header(compliance):
    first = next(
        r for r in compliance if r.sourceMember == "IDR PCV as of 01.02.2003.xls"
    )
    assert first.reportRunDate == date(2003, 1, 2)
    assert first.operatingDay == date(2002, 3, 12)
    assert first.compliance == Decimal("0.993009565857248")
    multiline = next(
        r for r in compliance if r.sourceMember == "IDR PCV as of 07.30.2003.xls"
    )
    assert multiline.reportRunDate == date(2003, 7, 30)
    assert multiline.operatingDay == date(2002, 7, 11)


def test_repeated_operating_dates_keep_distinct_report_vintages(compliance):
    rows = [
        r
        for r in compliance
        if r.operatingDay == date(2002, 3, 14) and r.entity == "System"
    ]
    assert {date(2003, 1, 2), date(2003, 1, 3)} <= {r.reportRunDate for r in rows}
    assert len({r.sourceMember for r in rows}) >= 2


def test_query_reads_later_filings_for_earlier_operating_dates():
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        if str(request.url) == INDEX_URL:
            return httpx.Response(200, text=f'<a href="{ARCHIVE_URL}">IDR PCV 2009</a>')
        assert str(request.url) == ARCHIVE_URL
        return httpx.Response(200, content=FIXTURE.read_bytes())

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.idr_compliance.rows(
                date_from=date(2008, 7, 8), date_to=date(2008, 7, 8), entity="Market"
            )
        )
        assert len(rows) == 1
        assert rows[0].reportRunDate == date(2009, 1, 4)
        assert rows[0].compliance == Decimal("0.9996")
        assert rows[0].sourceArchive == "idr_pcv_2009.zip"
        with pytest.raises(ValueError, match="date_from"):
            list(
                client.idr_compliance.rows(
                    date_from=date(2009, 1, 2), date_to=date(2009, 1, 1)
                )
            )
    assert requested == [INDEX_URL, ARCHIVE_URL]


def test_standalone_filename_and_real_excel_error_cells():
    member = "IDR PCV as of 05.23.2003.xls"
    with ZipFile(FIXTURE) as z:
        data = z.read(member)
    with Client() as client:
        rows = list(client.idr_compliance.read(data, filename=member, entity="MVEC"))
    assert rows and all(
        r.sourceMember == member and r.sourceArchive is None for r in rows
    )
    assert any(r.status == "#N/A" and r.compliance is None for r in rows)


def test_missing_run_date_is_not_inferred_from_filename():
    book = openpyxl.Workbook()
    book.active.append(["Date", "Market"])
    book.active.append(["2008/07/08", 0.9996])
    buf = BytesIO()
    book.save(buf)
    book.close()
    with Client() as client, pytest.raises(ValueError, match="Missing report date"):
        list(
            client.idr_compliance.read(
                buf.getvalue(), filename="IDR PCV as of 01.04.2009.xlsx"
            )
        )
