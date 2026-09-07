from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from itertools import islice
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, ScheduledGeneration
from tinyercot._zonal_generation import URL

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/history/scheduled-zonal-generation.zip"
)


def year_zip(year):
    with ZipFile(FIXTURE) as archive:
        return archive.read(f"{year}.zip")


@pytest.mark.parametrize(
    "year,count",
    [
        (2001, 44064),
        (2002, 140144),
        (2003, 140144),
        (2004, 175660),
        (2005, 175180),
        (2006, 175180),
        (2007, 38768),
    ],
)
def test_original_annual_counts(year, count):
    with Client() as client:
        assert sum(1 for _ in client.zonal_generation.read(year_zip(year))) == count


def test_outer_zip_and_source_types():
    with Client() as client:
        first = list(islice(client.zonal_generation.read(FIXTURE.read_bytes()), 2))
    assert all(isinstance(r, ScheduledGeneration) for r in first)
    assert [(r.zoneId, r.scheduledMW) for r in first] == [
        (240, Decimal(6187)),
        (242, Decimal(12501)),
    ]
    assert first[0].periodEnding == datetime.fromisoformat("2007-01-01T00:15:00")
    assert first[0].periodEnding.tzinfo is None and first[0].sourceMember == "2007.txt"


def test_anonymous_query_includes_midnight_on_the_operating_day():
    requests = []

    def handler(request):
        assert str(request.url) == URL
        assert "authorization" not in request.headers
        requests.append(request)
        return httpx.Response(200, content=year_zip(2007))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.zonal_generation.rows(
                date_from=date(2007, 4, 11), date_to=date(2007, 4, 11)
            )
        )
    assert len(requests) == 1 and len(rows) == 384
    assert all(r.operatingDay == date(2007, 4, 11) for r in rows)
    assert rows[-1].periodEnding == datetime.fromisoformat("2007-04-12T00:00:00")
    assert rows[-1].scheduledMW == 1843


def test_missing_source_day_is_not_filled():
    with Client() as client:
        dates = {r.operatingDay for r in client.zonal_generation.read(year_zip(2001))}
    assert date(2001, 8, 8) in dates and date(2001, 8, 10) in dates
    assert date(2001, 8, 9) not in dates


def test_plain_text_retains_repeated_period_and_zone_rows():
    with ZipFile(BytesIO(year_zip(2001))) as archive:
        header, first = archive.read("2001.txt").splitlines()[:2]
    data = b"\n".join([header, first, first])
    with Client() as client:
        rows = list(client.zonal_generation.read(data, filename="saved.txt"))
    assert len(rows) == 2 and rows[0] == rows[1]
    assert rows[0].zoneId == 24 and rows[0].scheduledMW == 3490
    assert rows[0].sourceMember == "saved.txt"
