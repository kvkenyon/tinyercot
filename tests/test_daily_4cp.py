import json
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, CoincidentPeakDay, PublicFile

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
FIXTURE = INPUTS / "coincident-peaks/daily-2017.xlsx"
SOURCE = json.loads((INPUTS / "public-daily-4cp-evidence.json").read_text())


def test_every_original_interval_and_settlement():
    original = openpyxl.load_workbook(FIXTURE, read_only=True, data_only=True)
    counts = Counter()
    dates = {}
    first = {}
    with Client() as client:
        records = client.coincident_peaks.read_daily(
            FIXTURE.read_bytes(), filename=FIXTURE.name
        )
        try:
            for sheet in original:
                rows = sheet.values
                units = next(rows)
                headers = next(rows)
                for line, values in enumerate(rows, 3):
                    record = next(records)
                    assert record.entity == values[0]
                    assert record.operatingDay == values[1].date()
                    assert record.channel == values[2]
                    assert record.settlement == sheet.title
                    assert record.sourceSheet == sheet.title
                    assert record.sourceRow == line
                    assert record.sourceUnitHeader == units[0]
                    assert record.sourceMember == FIXTURE.name
                    assert record.sourceFile is None
                    assert len(record.intervals) == 96
                    for i, (interval, label, value) in enumerate(
                        zip(record.intervals, headers[3:], values[3:], strict=True), 1
                    ):
                        assert interval.interval == i
                        assert interval.sourceLabel == str(label)
                        assert interval.energyMWh == Decimal(str(value))
                        counts["numericMWh"] += 1
                    dates.setdefault((record.settlement, record.entity), set()).add(
                        record.operatingDay
                    )
                    counts[record.settlement] += 1
                    if record.settlement not in first:
                        first[record.settlement] = record
                        assert (
                            CoincidentPeakDay.model_validate_json(
                                record.model_dump_json()
                            )
                            == record
                        )
            assert next(records, None) is None
        finally:
            original.close()
    assert counts == {"INITIAL": 16445, "FINAL": 16445, "numericMWh": 3157440}
    assert first["INITIAL"].channel == 1 and first["FINAL"].channel == 2
    assert first["INITIAL"].intervals[0].energyMWh == Decimal("9578.99825")
    assert first["FINAL"].intervals[0].energyMWh == Decimal("9582.152845")
    assert first["FINAL"].intervals[-1].sourceLabel == "24:00"
    assert len(dates) == 270
    complete = {date(2017, 6, 1) + timedelta(days=i) for i in range(122)}
    for (settlement, entity), actual in dates.items():
        if entity == "FARMERS ELECTRIC CO OP INC PRTN RC (TDSP)":
            assert len(actual) == 97 and actual < complete
        else:
            assert actual == complete


def test_actual_index_discovery_and_anonymous_date_filtered_query():
    with ZipFile(INPUTS / "loss-factors/indexes.zip") as z:
        pages = {n.removesuffix(".html"): z.read(n) for n in z.namelist()}
    requested = []
    data = FIXTURE.read_bytes()

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        return httpx.Response(
            200,
            content=data
            if str(request.url) == SOURCE["url"]
            else pages[request.url.path.rsplit("/", 1)[-1]],
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        files = client.coincident_peaks.daily_files()
        assert files == [PublicFile(url=SOURCE["url"], title=SOURCE["title"])]
        requested.clear()
        records = list(
            client.coincident_peaks.daily(
                date_from=date(2017, 6, 1),
                date_to=date(2017, 6, 1),
                where=lambda r: r.entity == "ERCOT",
            )
        )
    assert len(requested) == 27
    assert len(records) == 2
    assert {r.settlement for r in records} == {"INITIAL", "FINAL"}
    assert all(r.sourceFile == files[0] for r in records)
    assert all(r.operatingDay == date(2017, 6, 1) for r in records)


def test_inverted_bounds_fail_before_download_or_parse():
    def handler(request):
        pytest.fail("Inverted dates must not trigger a download")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        for query in [
            client.coincident_peaks.daily,
            lambda **kw: client.coincident_peaks.read_daily(b"", **kw),
        ]:
            with pytest.raises(ValueError, match="date_from must not be after date_to"):
                list(query(date_from=date(2017, 9, 1), date_to=date(2017, 6, 1)))
