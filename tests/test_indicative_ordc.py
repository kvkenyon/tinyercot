import csv
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, IndicativeOrdcPrice

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/public-tables/indicative-ordc.zip"
)
ARCHIVE_URL = "https://www.ercot.com/files/docs/2018/04/20/Indicative_Real-Time_Reserve_ORDC_Price_Adder__1_.zip"


@pytest.fixture(scope="module")
def prices():
    with Client() as client:
        return list(client.indicative_ordc.read(FIXTURE.read_bytes()))


def test_every_original_csv_value_timestamp_and_flag(prices):
    actual = iter(prices)
    with ZipFile(FIXTURE) as archive:
        members = [n for n in archive.namelist() if n.endswith(".csv")]
        assert len(members) == 34
        for member in members:
            source = csv.DictReader(StringIO(archive.read(member).decode("utf-8-sig")))
            for cells in source:
                row = next(actual)
                assert row.indicative is True and row.sourceMember == member
                assert row.sourceTimestamp == cells["SCED_TIMESTAMP"]
                assert row.repeatedHourFlag == cells["REPEATED_HOUR_FLAG"]
                day, clock, meridiem = cells["SCED_TIMESTAMP"].split()
                month, day_number, year = map(int, day.split("/"))
                hour, minute, second = map(int, clock.split(":"))
                hour = hour % 12 + (12 if meridiem == "PM" else 0)
                expected = f"{year:04}-{month:02}-{day_number:02}T{hour:02}:{minute:02}:{second:02}"
                assert row.scedTimestamp == datetime.fromisoformat(expected)
                assert (
                    row.systemLambda,
                    row.rtolcap,
                    row.rtoffcap,
                    row.rtorpa,
                    row.rtoffpa,
                ) == tuple(
                    Decimal(cells[k])
                    for k in (
                        "SYSTEM_LAMBDA",
                        "RTOLCAP",
                        "RTOFFCAP",
                        "RTORPA",
                        "RTOFFPA",
                    )
                )
    assert next(actual, None) is None
    assert len(prices) == 9826
    assert min(r.scedTimestamp for r in prices) == datetime.fromisoformat(
        "2013-10-17T00:00:16"
    )
    assert max(r.scedTimestamp for r in prices) == datetime.fromisoformat(
        "2013-11-19T23:55:08"
    )
    assert len({r.scedTimestamp.date() for r in prices}) == 34
    assert (
        IndicativeOrdcPrice.model_validate_json(prices[0].model_dump_json())
        == prices[0]
    )


def test_midnight_and_repeat_hour_keep_original_identity(prices):
    assert prices[0].sourceTimestamp == "10/17/2013 00:00:16 AM"
    assert prices[0].scedTimestamp.hour == 0
    assert Counter(r.repeatedHourFlag for r in prices) == {"N": 9814, "Y": 12}
    repeated = [r for r in prices if r.repeatedHourFlag == "Y"]
    assert {r.scedTimestamp.date() for r in repeated} == {date(2013, 11, 3)}
    assert all(r.scedTimestamp.tzinfo is None for r in prices)


def test_discovery_and_typed_predicate_use_actual_source_dates():
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        if str(request.url) == ARCHIVE_URL:
            return httpx.Response(200, content=FIXTURE.read_bytes())
        return httpx.Response(
            200,
            text=f'<a href="{ARCHIVE_URL}">Indicative Real-Time Reserve ORDC Price Adder </a>',
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.indicative_ordc.rows(where=lambda r: r.repeatedHourFlag == "Y")
        )
    assert len(rows) == 12
    assert all(r.scedTimestamp.year == 2013 for r in rows)
    assert requested == ["https://www.ercot.com/mktinfo/rtm", ARCHIVE_URL]


def test_saved_csv_and_nested_archives_preserve_overlaps():
    with ZipFile(FIXTURE) as archive:
        member = next(n for n in archive.namelist() if n.endswith(".csv"))
        data = archive.read(member)
    nested = BytesIO()
    with ZipFile(nested, "w") as archive:
        archive.writestr("one.CSV", data)
    outer = BytesIO()
    with ZipFile(outer, "w") as archive:
        archive.writestr("nested.zip", nested.getvalue())
        archive.writestr("two.csv", data)
    with Client() as client:
        saved = list(client.indicative_ordc.read(data, filename="saved.csv"))
        rows = list(client.indicative_ordc.read(outer.getvalue()))
    assert saved and all(r.sourceMember == "saved.csv" for r in saved)
    assert len(rows) == 2 * len(saved)
    assert {r.sourceMember for r in rows} == {"one.CSV", "two.csv"}


def test_unknown_column_does_not_silently_change_price_meaning():
    with ZipFile(FIXTURE) as archive:
        member = next(n for n in archive.namelist() if n.endswith(".csv"))
        data = archive.read(member).replace(b"RTORPA", b"NEW_ADDER")
    with Client() as client, pytest.raises(ValueError, match="changed.csv"):
        list(client.indicative_ordc.read(data, filename="changed.csv"))
