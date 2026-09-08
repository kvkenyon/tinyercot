"""Compare the full original workbook with an independent spreadsheet reader."""

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest
from python_calamine import CalamineWorkbook

from tinyercot import Client, WinterLoadForecast

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
URL = "https://www.ercot.com/files/docs/2025/10/06/ERCOT-Adjusted-Load-Forecast-Winter-2025-2026-for-RS-Magnitude-2025.10.07-.xlsx"


def original():
    with ZipFile(INPUTS / "winter-forecasts/source.zip") as archive:
        return archive.read("winter-2025-2026.xlsx")


def test_every_original_hour_peak_and_operator_value():
    data = original()
    with Client() as client:
        decoded = list(client.winter_load_forecasts.read(data))
    assert len(decoded) == 2161
    numbers = 0
    with CalamineWorkbook.from_filelike(BytesIO(data)) as book:
        grids = {
            name: book.get_sheet_by_name(name).to_python()
            for name in ("Forecast", "Peak")
        }
        for row in decoded:
            cells = grids[row.sourceSheet]
            raw = cells[row.sourceRow - 1]
            peak = row.kind == "peak"
            assert row.forecastDate == date.fromisoformat(str(raw[0])[:10])
            assert row.sourceDate == row.forecastDate
            assert row.hour == raw[1 if peak else 4]
            assert row.percentile == 75 and row.sourceFile is None
            assert len(row.sourceNotes) == 7
            assert "3,309 MW" in row.sourceNotes[-1]
            assert "1,508 MW" in row.sourceNotes[-1]
            assert row.baseLoad == Decimal(str(raw[2 if peak else 5]))
            assert row.loadWithLargeLoads == Decimal(str(raw[4 if peak else 6]))
            numbers += 2
            assert row.largeLoadAdditions == (Decimal(str(raw[3])) if peak else None)
            numbers += int(peak)
            start = 5 if peak else 7
            assert len(row.transmissionOperators) == 21
            assert list(row.transmissionOperators) == cells[0][start:]
            for value, expected in zip(
                row.transmissionOperators.values(), raw[start:], strict=True
            ):
                assert value == Decimal(str(expected))
                numbers += 1
    assert numbers == 49704
    assert decoded[0].forecastDate == date(2025, 12, 1)
    assert decoded[-2].forecastDate == date(2026, 2, 28)
    assert decoded[-2].hour == 24
    assert decoded[-1].forecastDate == date(2026, 1, 31)
    assert decoded[-1].hour == 8 and decoded[-1].largeLoadAdditions == 4817
    for row in (decoded[0], decoded[-1]):
        assert WinterLoadForecast.model_validate_json(row.model_dump_json()) == row


def test_anonymous_discovery_and_peak_filter_use_original_metadata():
    with ZipFile(INPUTS / "peak-forecasts/indexes.zip") as archive:
        indexes = {name: archive.read(name) for name in archive.namelist()}
    downloads = []

    def respond(request):
        assert "Authorization" not in request.headers
        if str(request.url) == URL:
            downloads.append(str(request.url))
            return httpx.Response(200, content=original())
        name = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(
            200, content=indexes[("root" if name == "forecast" else name) + ".html"]
        )

    with (
        httpx.Client(transport=httpx.MockTransport(respond)) as http,
        Client(client=http) as client,
    ):
        assert [f.url for f in client.winter_load_forecasts.files()] == [URL]
        rows = list(client.winter_load_forecasts.rows(where=lambda r: r.kind == "peak"))
    assert len(rows) == 1 and downloads == [URL]
    assert rows[0].sourceFile.url == URL
    assert rows[0].sourceSheet == "Peak" and rows[0].sourceRow == 2


def test_unrelated_workbook_does_not_return_empty_forecasts():
    import openpyxl

    book = openpyxl.Workbook()
    output = BytesIO()
    book.save(output)
    with Client() as client, pytest.raises(ValueError, match="No winter load forecast"):
        list(client.winter_load_forecasts.read(output.getvalue()))
