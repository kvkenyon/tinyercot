"""Wind table expectations transcribed from the rendered public PDFs."""

# Source clocks have no UTC offsets.
# ruff: noqa: DTZ001
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest
from pypdf import PdfReader

from tinyercot import Client
from tinyercot._wind import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"


def sample(name):
    return (INPUTS / f"wind-{name}.pdf").read_bytes()


def zipped(files):
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return data.getvalue()


@pytest.mark.parametrize(
    "name,report_date,peak,hour,record,record_date,maximum,clock,percent,wind_over_peak",
    [
        (
            "penetration",
            date(2010, 8, 9),
            "63467",
            17,
            "7016",
            date(2010, 6, 12),
            "4062",
            time(22, 24, 24),
            "7.98",
            None,
        ),
        (
            "2012",
            date(2012, 1, 1),
            "32512",
            20,
            "7400",
            date(2011, 10, 7),
            "6326",
            time(0, 24),
            "23.99",
            "1288",
        ),
        (
            "2015",
            date(2015, 1, 1),
            "45758",
            19,
            "10957",
            date(2014, 12, 25),
            "872",
            time(0, 0),
            "2.19",
            "227",
        ),
        (
            "record",
            date(2010, 12, 11),
            "33199",
            19,
            "7016",
            date(2010, 6, 12),
            "7227",
            time(7, 16, 32),
            "25.80",
            None,
        ),
        (
            "typo",
            date(2013, 5, 14),
            "45450",
            17,
            "9674",
            date(2013, 5, 2),
            "7720",
            time(18, 44),
            "17.62",
            "5458",
        ),
        (
            "winter",
            date(2011, 2, 10),
            "57283",
            8,
            "7227",
            date(2010, 12, 11),
            "3622",
            time(22, 55, 32),
            "7.97",
            None,
        ),
    ],
)
def test_legacy_tables(
    name,
    report_date,
    peak,
    hour,
    record,
    record_date,
    maximum,
    clock,
    percent,
    wind_over_peak,
):
    with Client() as client:
        (row,) = client.wind_integration.read(sample(name))
    assert row.reportDate == report_date
    assert row.peakLoadMW == Decimal(peak)
    assert row.peakLoadHour == hour
    assert row.recordWindMW == Decimal(record)
    assert row.recordWindDate == record_date
    assert row.recordWindTime is None
    assert row.maxWindMW == Decimal(maximum)
    assert row.maxWindTime == clock
    assert row.windAtPeakLoadMW == (Decimal(wind_over_peak) if wind_over_peak else None)
    if name == "penetration":
        assert row.reportType == "Penetration"
        assert row.windPenetrationPercent == Decimal(percent)
        assert row.windIntegrationPercent is None
    else:
        assert row.reportType == "Integration"
        assert row.windIntegrationPercent == Decimal(percent)
        assert row.windPenetrationPercent is None
    assert row.penetrationAtMaxWindPercent is None
    assert row.maxWindPenetrationPercent is None
    assert row.maxWindPenetrationTime is None
    assert row.windAtMaxPenetrationMW is None
    assert row.penetrationAtRecordWindPercent is None
    assert row.recordWindPenetrationPercent is None
    assert row.recordWindPenetrationTime is None
    assert row.windAtRecordPenetrationMW is None
    if name == "record":
        assert row.recordWindLabel == "Previous Wind Record"
        assert row.maxWindLabel == "New Wind Record"
    if name == "typo":
        assert row.reportDateText == "05/14/12013"
    if name == "winter":
        assert row.peakLoadLabel == "New Record Winter Peak"
    if name == "2015":
        assert "instantaneous values" in row.sourceNotes
        assert "expected commercial operation date" in row.sourceNotes


def test_modern_table():
    with Client() as client:
        (row,) = client.wind_integration.read(sample("Jan2016"))
    assert row.reportDate == date(2016, 1, 1)
    assert row.reportDateText == "01/01/2016"
    assert row.peakLoadMW == Decimal(41153)
    assert row.peakLoadHour == 19
    assert row.windAtPeakLoadMW == Decimal(2181)
    assert row.maxWindMW == row.windAtMaxPenetrationMW == Decimal(4807)
    assert row.maxWindTime == row.maxWindPenetrationTime == time(4, 29)
    assert (
        row.penetrationAtMaxWindPercent
        == row.maxWindPenetrationPercent
        == Decimal("14.40")
    )
    assert row.recordWindMW == Decimal(13883)
    assert row.recordWindDate == date(2015, 12, 20)
    assert row.recordWindTime == time(11, 7)
    assert row.penetrationAtRecordWindPercent == Decimal("41.27")
    assert row.recordWindPenetrationPercent == Decimal("44.71")
    assert row.recordWindPenetrationTime == datetime(2015, 12, 20, 3, 5)
    assert row.windAtRecordPenetrationMW == Decimal(13057)
    assert row.windIntegrationPercent is row.windPenetrationPercent is None


def test_anonymous_discovery_download_filtering_and_revisions():
    base = "https://www.ercot.com/files/docs/2020/05/05/"
    url = base + "ERCOTWindIntegrationReport_2010.zip"
    other = base + "ERCOTWindIntegrationReport_Jan2016.zip"
    html = f'<a href="{url}">2010</a><a href="{url}">duplicate link</a><a href="{other}">2016</a>'
    html += '<a href="https://mis.ercot.com/anything.zip">MIS</a>'
    data = zipped(
        {
            "report.pdf": sample("penetration"),
            "revision.PDF": sample("penetration"),
            "december.pdf": sample("record"),
            "readme.txt": b"Missing dates",
            "nested.zip": zipped({"copy.Pdf": sample("penetration")}),
        }
    )
    requests = []

    def handle(request):
        requests.append(str(request.url))
        assert "authorization" not in request.headers
        assert "ocp-apim-subscription-key" not in request.headers
        if str(request.url) == INDEX_URL:
            return httpx.Response(200, text=html)
        assert str(request.url) == url
        return httpx.Response(200, content=data)

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        Client(client=http) as client,
    ):
        archives = client.wind_integration.archives()
        assert [(a.year, a.month) for a in archives] == [(2010, None), (2016, 1)]
        rows = list(
            client.wind_integration.rows(
                date_from=date(2010, 8, 9), date_to=date(2010, 8, 9)
            )
        )
    assert len(rows) == 3  # Revisions are not silently deduplicated.
    assert {r.sourceMember for r in rows} == {
        "report.pdf",
        "revision.PDF",
        "copy.Pdf",
    }
    assert requests == [INDEX_URL, INDEX_URL, url]


@pytest.mark.parametrize("data", [zipped({"readme.txt": b"No reports"}), zipped({})])
def test_missing_pdfs_fail(data):
    with Client() as client, pytest.raises(ValueError, match="no wind PDF"):
        list(client.wind_integration.read(data))


def test_missing_table_value_is_not_silently_dropped():
    text = " ".join(
        PdfReader(BytesIO(sample("Jan2016"))).pages[0].extract_text().split()
    )
    with Client() as client, pytest.raises(ValueError, match="summary table"):
        client.wind_integration._read_text(
            text.replace("4,807 MW", "missing MW", 1), "broken.pdf"
        )


def test_unknown_year_typo_is_not_truncated():
    text = " ".join(PdfReader(BytesIO(sample("typo"))).pages[0].extract_text().split())
    with Client() as client, pytest.raises(ValueError):
        client.wind_integration._read_text(text.replace("12013", "22013"), "broken.pdf")


def test_missing_index_and_http_failure_are_visible():
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, text=""))
        ) as http,
        Client(client=http) as client,
        pytest.raises(ValueError, match="No wind archives"),
    ):
        client.wind_integration.archives()
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(503))
        ) as http,
        Client(client=http) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        client.wind_integration.archives()
