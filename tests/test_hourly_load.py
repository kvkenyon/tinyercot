from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_STORED, BadZipFile, ZipFile

import httpx
import pytest
from openpyxl import Workbook

from tinyercot import Client
from tinyercot._load import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"
COLUMNS = (
    "coast",
    "east",
    "farWest",
    "north",
    "northC",
    "southern",
    "southC",
    "west",
    "total",
)


def sample(year):
    return (INPUTS / f"hourly-load-{year}.zip").read_bytes()


@pytest.fixture(scope="module")
def rows():
    with Client() as client:
        return {
            year: list(client.hourly_load.read_weather_zones(sample(year)))
            for year in [2002, 2016, 2022]
        }


def test_legacy_xls_values_and_hour_24(rows):
    data = rows[2002]
    assert len(data) == 8760
    row = data[0]
    assert (row.operatingDay, row.hourEnding) == (date(2002, 1, 1), 1)
    assert [getattr(row, name) for name in COLUMNS] == [
        Decimal(v)
        for v in (
            "8331.469266026934",
            "1111.0965494424045",
            "1094.045495798935",
            "995.2983921124664",
            "10336.304899346236",
            "2165.0075712469265",
            "4793.193560266372",
            "843.747177253755",
            "29670.162911494022",
        )
    ]
    assert row.sourceMember == "2002_ercot_hourly_load_data.xls"
    assert row.sourceSheet == "native_Load_2002"
    assert row.sourceHourEnding == "2002-01-01 01:00:00.003000"
    assert (data[1].operatingDay, data[1].hourEnding) == (date(2002, 1, 1), 2)
    assert data[1].sourceHourEnding == "2002-01-01 01:59:59.997000"
    assert (data[23].operatingDay, data[23].hourEnding) == (date(2002, 1, 1), 24)
    assert (data[-1].operatingDay, data[-1].hourEnding) == (date(2002, 12, 31), 24)


def test_oversized_sheet_dimensions_and_missing_hour_values(rows):
    data = rows[2016]
    assert len(data) == 8784
    assert data[0].total == Decimal("33852.7585869574")
    assert data[-1].operatingDay == date(2016, 12, 31)
    (missing,) = [
        r for r in data if r.operatingDay == date(2016, 11, 6) and r.hourEnding == 24
    ]
    assert all(getattr(missing, name) is None for name in COLUMNS)
    assert all(r.total is not None for r in data if r is not missing)


def test_dst_labels_and_mixed_excel_datetime(rows):
    data = rows[2022]
    assert len(data) == 8760
    assert data[0].total == Decimal("38006.938896")
    repeated = [
        r for r in data if r.operatingDay == date(2022, 11, 6) and r.hourEnding == 2
    ]
    assert [(r.dstLabel, r.total) for r in repeated] == [
        (None, Decimal("34706.875462")),
        ("DST", Decimal("34067.955296")),
    ]
    assert len([r for r in data if r.operatingDay == date(2022, 11, 6)]) == 25
    assert len([r for r in data if r.operatingDay == date(2022, 3, 13)]) == 23
    (mixed,) = [
        r for r in data if r.operatingDay == date(2022, 12, 1) and r.hourEnding == 1
    ]
    assert mixed.sourceHourEnding == "2022-12-01 01:00:00"
    assert mixed.total == Decimal("42313.98967")
    assert data[-1].hourEnding == 24
    assert data[-1].operatingDay == date(2022, 12, 31)


def test_anonymous_discovery_and_operating_date_filter():
    url = "https://www.ercot.com/files/docs/2015/10/22/2002_ercot_hourly_load_data.xls"
    old = "https://www.ercot.com/files/docs/2004/07/26/erceei95.txt"
    recent = "https://www.ercot.com/files/docs/2023/02/09/Native_Load_2023.zip"
    html = f'<a href="{url}"><span>2002 ERCOT Hourly Load Data</span></a><a href="{old}">1995 ERCOT Hourly Load Data</a><a href="{recent}">2023 ERCOT Hourly Load Data </a>'
    requests = []
    with ZipFile(BytesIO(sample(2002))) as z:
        data = z.read(z.namelist()[0])

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
        assert [a.year for a in client.hourly_load.archives()] == [1995, 2002, 2023]
        data = list(
            client.hourly_load.weather_zones(
                date_from=date(2002, 12, 31), date_to=date(2002, 12, 31)
            )
        )
    assert [r.hourEnding for r in data] == list(range(1, 25))
    assert requests == [INDEX_URL, INDEX_URL, url]


def workbook(header, row):
    book = Workbook()
    book.active.append(header)
    book.active.append(row)
    out = BytesIO()
    book.save(out)
    book.close()
    return out.getvalue()


def test_unrecognized_control_area_header_fails():
    data = workbook(
        ["MONTH", "DAY", "YEAR", "HOUR ENDING", "AENX"], [1, 1, 1998, 1, 846000]
    )
    with (
        Client() as client,
        pytest.raises(ValueError, match="unsupported weather-zone header"),
    ):
        list(client.hourly_load.read_weather_zones(data))


def test_missing_and_invalid_source_cells():
    header = [
        "Hour Ending",
        "COAST",
        "EAST",
        "FWEST",
        "NORTH",
        "NCENT",
        "SOUTH",
        "SCENT",
        "WEST",
        "ERCOT",
    ]
    with Client() as client:
        (row,) = client.hourly_load.read_weather_zones(
            workbook(header, ["01/01/2024 01:00", None, 0, 1, 2, 3, 4, 5, 6, 21])
        )
        assert row.coast is None
        assert row.east == 0
        with pytest.raises(ValueError, match="nonnumeric load"):
            list(
                client.hourly_load.read_weather_zones(
                    workbook(
                        header, ["01/01/2024 01:00", "missing", 0, 1, 2, 3, 4, 5, 6, 21]
                    )
                )
            )


def test_zip_integrity_errors_propagate():
    data = BytesIO()
    with ZipFile(data, "w", compression=ZIP_STORED) as z:
        z.writestr("data.xlsx", b"original-content")
    corrupt = data.getvalue().replace(b"original-content", b"modified-content")
    with Client() as client, pytest.raises(BadZipFile, match="CRC"):
        list(client.hourly_load.read_weather_zones(corrupt))
