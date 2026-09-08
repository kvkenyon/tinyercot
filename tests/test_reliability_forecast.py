from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl

from tinyercot import Client, ReliabilityLoadForecast
from tinyercot._load_forecast import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"


def sample():
    with ZipFile(INPUTS / "history/reliability-load-forecast.zip") as z:
        return z.read(z.namelist()[0])


def test_all_hours_and_published_peak():
    with Client() as client:
        result = client.load_forecast.read_reliability(sample(), filename="winter.xlsx")
    assert isinstance(result, ReliabilityLoadForecast)
    assert result.sourceMember == "winter.xlsx" and result.percentile == 75
    assert len(result.hours) == 2160 and len(result.peaks) == 1
    assert len({(r.operatingDay, r.hour) for r in result.hours}) == 2160
    first, last = result.hours[0], result.hours[-1]
    assert first.operatingDay == date(2025, 12, 1) and first.hour == 1
    assert last.operatingDay == date(2026, 2, 28) and last.hour == 24
    assert (last.sourceYear, last.sourceMonth, last.sourceDay) == (2026, 2, 28)
    assert first.baseLoadMW == Decimal("49173.39350581266")
    assert first.loadWithLargeLoadsMW == Decimal("53990.39350581266")
    peak = result.peaks[0]
    assert peak.operatingDay == date(2026, 1, 31) and peak.hour == 8
    assert peak.baseLoadMW == Decimal("77337.65987825058")
    assert peak.largeLoadAdditionsMW == Decimal(4817)
    assert peak.loadWithLargeLoadsMW == Decimal("82154.65987825058")
    corresponding = next(
        r
        for r in result.hours
        if (r.operatingDay, r.hour) == (peak.operatingDay, peak.hour)
    )
    assert corresponding.loadWithLargeLoadsMW == peak.loadWithLargeLoadsMW


def test_operator_values_and_explanations_remain_separate():
    with Client() as client:
        result = client.load_forecast.read_reliability(sample())
    first = result.hours[0]
    assert len(first.operators) == 21
    assert first.operators[0].name == "AEP Texas Central Company"
    assert first.operators[0].loadMW == Decimal("4091.226339683613")
    assert first.operators[0].sourceColumn == 8
    assert result.peaks[0].operators[0].sourceColumn == 6
    assert first.operators[-1].name == "Texas-New Mexico Power Company"
    assert first.operators[-1].loadMW == Decimal("1332.598964007523")
    assert len(result.notes) == 7
    assert result.notes[0].text == result.title
    assert (
        result.notes[2].sourceSheet == "Explanation" and result.notes[2].sourceRow == 3
    )
    assert "does not include the Large Load" in result.notes[2].text
    assert result.notes[-1].sourceSheet == "Peak" and result.notes[-1].sourceRow == 4
    assert "3,309 MW" in result.notes[-1].text and "1,508 MW" in result.notes[-1].text


def test_missing_zero_and_source_date_components_are_preserved():
    book = openpyxl.load_workbook(BytesIO(sample()))
    book["Forecast"]["H2"] = None
    book["Forecast"]["I2"] = 0
    book["Forecast"]["B2"] = 2024  # deliberately conflicting source year, no repair
    book["Peak"]["D2"] = None
    book["Explanation"]["A2"] = "These values use the 90th percentile load forecast."
    out = BytesIO()
    book.save(out)
    book.close()
    with Client() as client:
        result = client.load_forecast.read_reliability(out.getvalue())
    assert result.hours[0].operators[0].loadMW is None
    assert result.hours[0].operators[1].loadMW == Decimal(0)
    assert result.hours[0].sourceYear == 2024
    assert result.hours[0].operatingDay.year == 2025
    assert result.peaks[0].largeLoadAdditionsMW is None
    assert result.percentile == 90


def test_live_workflow_with_captured_public_responses():
    requests = []

    def handler(request):
        requests.append(str(request.url))
        assert "authorization" not in request.headers
        content = (
            (INPUTS / "public-load-forecast-index.html").read_bytes()
            if str(request.url) == INDEX_URL
            else sample()
        )
        return httpx.Response(200, content=content)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        archives = client.load_forecast.archives(kind="winter-reliability")
        assert len(archives) == 1
        assert (
            archives[0].section
            == "Winter 2025-2026 Load Forecast for Reliability Standard Magnitude"
        )
        result = client.load_forecast.reliability(archives[0])
    assert len(result.hours) == 2160 and len(requests) == 2
    assert result.sourceMember == archives[0].url.rsplit("/", 1)[-1]
