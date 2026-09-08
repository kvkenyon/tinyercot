from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client
from tinyercot._load_forecast import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
MONTHLY = "2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx"
WEEKLY = "p90_peaks_may.xlsx"
WEATHER = "ERCOT-Peak-Demand-Scenarios.xlsx"
SEASONAL = "Summer-and-Winter-Peaks.xlsx"


def sample(name):
    with ZipFile(INPUTS / "history/load-forecast-summaries.zip") as archive:
        return archive.read(name)


@pytest.mark.parametrize(
    "name,reader,count",
    [
        (MONTHLY, "read_monthly", 481),
        (WEEKLY, "read_weekly", 936),
        (WEATHER, "read_peaks", 238),
        (SEASONAL, "read_peaks", 504),
    ],
)
def test_complete_published_summaries(name, reader, count):
    with Client() as client:
        rows = list(getattr(client.load_forecast, reader)(sample(name), filename=name))
    assert len(rows) == count
    assert all(r.sourceMember == name for r in rows)
    assert len({(r.sourceSheet, r.sourceRow, r.sourceColumn) for r in rows}) == count


def test_monthly_keeps_misaligned_tsp_dates_and_energy_label():
    with Client() as client:
        rows = list(client.load_forecast.read_monthly(sample(MONTHLY)))
    adjusted = [r for r in rows if r.scenario == "ERCOT Adjusted"]
    tsp = [r for r in rows if r.scenario == "TSP Provided"]
    assert len(adjusted) == 240 and len(tsp) == 241
    assert adjusted[0].year == 2025 and adjusted[0].month == 1
    assert adjusted[0].peakDemandMW == Decimal("70716.52")
    assert adjusted[0].energy == Decimal("38585578.513")
    assert all(r.energyLabel == "Annual Energy" for r in rows)
    # Original H3/I3 have values alongside F3/G3 = literal year/month headers.
    assert tsp[0].sourceYear == "year" and tsp[0].sourceMonth == "month"
    assert tsp[0].year is None and tsp[0].month is None
    assert tsp[0].peakDemandMW == adjusted[0].peakDemandMW
    assert tsp[1].year == 2025 and tsp[1].month == 1
    assert tsp[1].peakDemandMW == Decimal("69131.27")
    assert tsp[-1].year == 2044 and tsp[-1].month == 12
    assert tsp[-1].peakDemandMW is None and tsp[-1].energy is None
    assert adjusted[-1].energy == Decimal("108373689.46")


def test_weather_year_scenarios_and_published_percentile_are_distinct():
    with Client() as client:
        rows = list(client.load_forecast.read_peaks(sample(WEATHER)))
    assert Counter(r.scenario for r in rows) == {
        "TSP Provided": 119,
        "ERCOT Adjusted": 119,
    }
    assert {r.year for r in rows} == set(range(2025, 2032))
    assert {r.weatherYear for r in rows} == {*range(2008, 2024), None}
    assert all(r.region == "ERCOT" and r.season == "Summer" for r in rows)
    adjusted = [r for r in rows if r.scenario == "ERCOT Adjusted" and r.year == 2025]
    assert adjusted[0].weatherYear == 2008
    assert adjusted[0].peakDemandMW == Decimal("83648.38016797218")
    assert adjusted[-1].weatherYear is None and adjusted[-1].percentile == 90
    assert adjusted[-1].peakDemandMW == Decimal("85758.65034329833")
    assert all(r.coincident is None for r in rows)


def test_seasonal_keeps_winter_spans_coincidence_regions_and_totals():
    with Client() as client:
        rows = list(client.load_forecast.read_peaks(sample(SEASONAL)))
    assert len({r.region for r in rows}) == 9
    assert Counter((r.season, r.coincident) for r in rows) == {
        ("Summer", True): 126,
        ("Summer", False): 126,
        ("Winter", True): 126,
        ("Winter", False): 126,
    }
    winter = next(r for r in rows if r.season == "Winter")
    assert winter.year == 2025 and winter.yearTo == 2026
    assert winter.periodLabel == "2025-2026" and winter.region == "COAST"
    assert winter.peakDemandMW == Decimal(16551)
    # Preserve the independently published total, even when regional cells differ.
    first = rows[:9]
    assert first[-1].region == "ERCOT"
    assert first[-1].peakDemandMW == Decimal("93655.26")
    assert sum(r.peakDemandMW for r in first[:-1]) != first[-1].peakDemandMW


def test_weekly_includes_all_104_weeks_beyond_title_year():
    with Client() as client:
        rows = list(client.load_forecast.read_weekly(sample(WEEKLY)))
    assert len({r.beginDate for r in rows}) == 104
    first, last = rows[8], rows[-1]
    assert first.region == last.region == "ERCOT"
    assert first.beginDate == date(2025, 5, 4) and first.endDate == date(2025, 5, 10)
    assert first.peakDate == date(2025, 5, 9) and first.peakHour == 17
    assert first.peakDemandMW == Decimal("76619.08347045985")
    assert last.endDate == date(2027, 5, 1) and last.peakDate == date(2027, 4, 27)
    assert last.peakDemandMW == Decimal("94014.72290856337")


def test_blank_and_zero_forecasts_are_distinct():
    book = openpyxl.load_workbook(BytesIO(sample(WEEKLY)))
    book.active["E2"] = None
    book.active["F2"] = 0
    content = BytesIO()
    book.save(content)
    book.close()
    with Client() as client:
        rows = list(client.load_forecast.read_weekly(content.getvalue()))
    assert len(rows) == 936
    assert rows[0].peakDemandMW is None and rows[1].peakDemandMW == Decimal(0)


def test_discovery_and_all_queries_are_anonymous():
    requests = []

    def handler(request):
        requests.append(str(request.url))
        assert "authorization" not in request.headers
        assert "ocp-apim-subscription-key" not in request.headers
        if str(request.url) == INDEX_URL:
            return httpx.Response(
                200, content=(INPUTS / "public-load-forecast-index.html").read_bytes()
            )
        return httpx.Response(200, content=sample(request.url.path.rsplit("/", 1)[-1]))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        forecasts = client.load_forecast
        archives = forecasts.archives()
        assert len(archives) == 4 and len({a.url for a in archives}) == 4
        assert all("2025" in a.section for a in archives)
        assert len(forecasts.archives(kind="monthly")) == 1
        for a in archives:
            method = (
                "monthly"
                if a.kind == "monthly"
                else "weekly"
                if a.kind == "weekly-p90"
                else "peaks"
            )
            assert list(getattr(forecasts, method)(a))
        with pytest.raises(ValueError, match="weekly P90"):
            list(forecasts.weekly(next(a for a in archives if a.kind == "monthly")))
    assert len(requests) == 6  # two index reads and exactly one download per query


def test_unknown_index_is_not_reported_as_empty_coverage():
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, text="changed"))
        ) as http,
        Client(client=http) as client,
        pytest.raises(ValueError, match="No load forecast summaries"),
    ):
        client.load_forecast.archives()
