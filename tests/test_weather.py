from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import get_args
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, WeatherDay, WeatherVariable, WeatherZone
from tinyercot._weather import URL

FIXTURE = Path(__file__).resolve().parents[1] / "tools/inputs/weather/historical.zip"


@pytest.fixture(scope="module")
def weather():
    with Client() as client:
        return list(client.historical_weather.read(FIXTURE.read_bytes()))


def test_all_zones_and_variables_have_typed_hourly_values(weather):
    assert len(weather) == 192
    assert {r.weatherZone for r in weather} == set(get_args(WeatherZone))
    assert {r.variable for r in weather} == set(get_args(WeatherVariable))
    assert all([h.hour for h in r.hours] == list(range(1, 25)) for r in weather)
    assert WeatherDay.model_validate_json(weather[0].model_dump_json()) == weather[0]


def test_source_values_and_unknown_units_are_preserved(weather):
    rows = {
        r.variable: r
        for r in weather
        if r.weatherZone == "COAST" and r.operatingDay == date(1996, 1, 1)
    }
    assert rows["CLOUDCOVER"].hours[0].value == Decimal(10)
    assert rows["WINDSPEED"].hours[0].value == Decimal("1.5")
    assert rows["DEWPOINT"].hours[0].value == Decimal("58.2")
    assert rows["DRYBULB TEMP"].hours[0].value == Decimal("58.7")
    assert all(r.sourceUnit is None for r in weather)
    assert all(
        any("weighting scheme" in note for note in r.sourceNotes) for r in weather
    )


def test_source_dates_extend_beyond_filename_and_keep_leap_and_dst_days(weather):
    days = {r.operatingDay for r in weather}
    assert min(days) == date(1996, 1, 1) and max(days) == date(2001, 1, 10)
    assert {date(1996, 2, 29), date(1996, 4, 7), date(1996, 10, 27)} <= days
    assert all(len(r.hours) == 24 for r in weather)


def test_anonymous_query_uses_actual_dates_and_typed_filters():
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
            client.historical_weather.rows(
                date_from=date(2001, 1, 10),
                date_to=date(2001, 1, 10),
                weather_zone="COAST",
                variable="CLOUDCOVER",
            )
        )
        assert len(rows) == 1 and rows[0].operatingDay == date(2001, 1, 10)
        assert rows[0].hours[2].value == Decimal("9.4")
    assert requested == [URL]


def test_saved_workbook_uses_original_zone_filename():
    with ZipFile(FIXTURE) as z:
        name = "Weather '96-'00 North Central.xls"
        data = z.read(name)
    with Client() as client:
        rows = list(
            client.historical_weather.read(data, filename=name, variable="DEWPOINT")
        )
        assert len(rows) == 6 and all(r.weatherZone == "NCENT" for r in rows)
        with pytest.raises(ValueError, match="Cannot identify source weather zone"):
            list(client.historical_weather.read(data))


@pytest.mark.parametrize(
    "filters",
    [
        {"date_from": date(2000, 1, 2), "date_to": date(2000, 1, 1)},
        {"weather_zone": "MISSING"},
        {"variable": "MISSING"},
    ],
)
def test_invalid_query_filters_fail_before_download(filters):
    def handler(request):
        pytest.fail("Invalid query should not download the archive")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
        pytest.raises(ValueError),
    ):
        list(client.historical_weather.rows(**filters))


@pytest.mark.parametrize("valid_header", [True, False])
def test_missing_value_and_unknown_header(valid_header):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "WINDSPEED"
    sheet.append([None] + [f"Hour {i}" for i in range(1, 25)])
    sheet.append([datetime.fromisoformat("1996-01-01T00:00:00"), None] + [0] * 23)
    if not valid_header:
        sheet.cell(1, 25).value = "New column"
    buf = BytesIO()
    book.save(buf)
    book.close()
    with Client() as client:
        if valid_header:
            row = next(
                client.historical_weather.read(
                    buf.getvalue(), filename="Weather '96-'00 East.xlsx"
                )
            )
            assert row.hours[0].value is None and row.hours[1].value == Decimal(0)
        else:
            with pytest.raises(ValueError, match="Missing hourly weather columns"):
                list(
                    client.historical_weather.read(
                        buf.getvalue(), filename="Weather '96-'00 East.xlsx"
                    )
                )
