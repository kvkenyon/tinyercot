"""Compare all published cells, including DST labels, with captured public HTML."""

import re
from datetime import date, datetime
from decimal import Decimal
from html import unescape
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client

FIXTURES = Path(__file__).parents[1] / "tools/inputs/market-displays/displays.zip"
METHODS = {
    "dam_mcpc": "day_ahead_ancillary_prices",
    "dam_spp": "day_ahead_prices",
    "real_time_spp": "real_time_prices",
    "actual_loads_of_forecast_zones": "actual_forecast_zone_load",
    "actual_loads_of_weather_zones": "actual_weather_zone_load",
}
with ZipFile(FIXTURES) as archive:
    FILES = archive.namelist()


def source(name):
    with ZipFile(FIXTURES) as archive:
        return archive.read(name).decode()


def original_rows(body):
    return [
        [
            " ".join(unescape(re.sub(r"<[^>]+>", " ", cell)).split())
            for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.DOTALL)
        ]
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", body, re.DOTALL)
    ]


@pytest.mark.parametrize("name", FILES)
def test_every_original_display_cell_and_date(name):
    body = source(name)
    prefix, _, suffix = name.removesuffix(".html").partition("_")
    requested = date.fromisoformat(prefix) if prefix.isdigit() else None
    table = suffix if requested else name.removesuffix(".html")

    def handler(request):
        assert request.url.path == f"/content/cdr/html/{name}"
        assert "authorization" not in request.headers
        assert "ocp-apim-subscription-key" not in request.headers
        return httpx.Response(200, text=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        read = getattr(Client(client=http).dashboards, METHODS[table])
        if name in ("20251102_dam_spp.html", "20251102_dam_mcpc.html"):
            with pytest.raises(ValueError, match="requested operating day"):
                read(requested)
            return
        result = read(requested)
    headers, *rows = original_rows(body)
    assert result.periodType == headers[1]
    assert len(result.data) == len(rows)
    for actual, raw in zip(result.data, rows, strict=True):
        assert actual.operatingDay == datetime.strptime(raw[0], "%m/%d/%Y").date()  # noqa: DTZ007
        assert actual.operatingDay == result.operatingDay
        assert actual.periodEnding == raw[1]
        assert actual.values == dict(
            zip(headers[2:], map(Decimal, raw[2:]), strict=True)
        )
    if requested is not None:
        assert result.operatingDay == requested
    updated = re.search(r"(?:Last Updated|Last Date and Time):\s*([^<]+)", body)[
        1
    ].strip()
    assert result.lastUpdated == datetime.strptime(updated, "%b %d, %Y %H:%M")  # noqa: DTZ007
    assert result.lastUpdated.tzinfo is None
    if requested == date(2025, 11, 2):
        assert len(rows) == (100 if table == "real_time_spp" else 25)
        assert any("*" in row.periodEnding for row in result.data)
    if requested == date(2026, 3, 8):
        assert len(rows) == (92 if table == "real_time_spp" else 23)


@pytest.mark.parametrize(
    "change", ["heading", "row-date", "missing", "extra", "unknown", "number"]
)
def test_wrong_dates_or_changed_columns_never_become_plausible_prices(change):
    body = source("20260903_dam_spp.html")
    if change == "heading":
        body = body.replace('value="09/03/2026"', 'value="09/04/2026"')
    elif change == "row-date":
        body = body.replace(">09/03/2026</td>", ">09/04/2026</td>", 1)
    elif change == "unknown":
        body = body.replace("HB_HOUSTON", "UNKNOWN_HUB")
    else:
        cell = re.search(r"<td[^>]*>[^<]*</td>", body)[0]
        replacement = {
            "missing": "",
            "extra": cell + cell,
            "number": cell.replace("09/03/2026", "not-a-date"),
        }[change]
        body = body.replace(cell, replacement, 1)
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        ) as http,
        pytest.raises(ValueError),
    ):
        Client(client=http).dashboards.day_ahead_prices(date(2026, 9, 3))


def test_reordered_price_columns_follow_labels_and_duplicate_rows_survive():
    body = source("20260903_dam_spp.html")
    body = (
        body.replace("HB_HOUSTON", "temporary")
        .replace("HB_NORTH", "HB_HOUSTON")
        .replace("temporary", "HB_NORTH")
    )
    row = re.findall(r"<tr\b[^>]*>.*?</tr>", body, re.DOTALL)[1]
    body = body.replace(row, row + row, 1)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
    ) as http:
        result = Client(client=http).dashboards.day_ahead_prices(date(2026, 9, 3))
    headers, *rows = original_rows(body)
    assert len(result.data) == 25
    assert result.data[0] == result.data[1]
    assert result.data[0].values == dict(
        zip(headers[2:], map(Decimal, rows[0][2:]), strict=True)
    )


def test_empty_midnight_table_is_distinct_from_unavailable_market():
    body = source("actual_loads_of_weather_zones.html")
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", body, re.DOTALL)
    for row in rows[1:]:
        body = body.replace(row, "")
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
    ) as http:
        assert Client(client=http).dashboards.actual_weather_zone_load().data == []
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, text=source("20251102_dam_mcpc.html"))
            )
        ) as http,
        pytest.raises(ValueError, match="No published market table"),
    ):
        Client(client=http).dashboards.day_ahead_ancillary_prices()


def test_unretained_date_keeps_http_error():
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(404))
        ) as http,
        pytest.raises(httpx.HTTPStatusError),
    ):
        Client(client=http).dashboards.real_time_prices(date(2010, 12, 1))
