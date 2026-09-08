import csv
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
from time import strptime
from zipfile import ZipFile

import httpx
import pytest
import xlrd

from tinyercot import Client, PublicFile, ZonalEnergyDay, ZonalEnergyTotal

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
FIXTURE = INPUTS / "public-tables/zonal-energy.zip"
MANIFEST = list(
    csv.DictReader(StringIO((INPUTS / "public-zonal-energy-sources.csv").read_text()))
)


def number(value):
    return None if value in ("", None) else Decimal(str(value))


def test_every_original_daily_quantity_and_source_number():
    counts = Counter()
    gaps = {}
    with ZipFile(FIXTURE) as archive, Client() as client:
        for file in MANIFEST:
            data = archive.read(file["member"])
            records = client.zonal_energy.read(data, filename=file["member"])
            with xlrd.open_workbook(file_contents=data) as book:
                for sheet in book.sheets():
                    header = sheet.row_values(0)
                    names = [str(v).strip().upper() for v in header]
                    date_col = next(
                        (
                            i
                            for i, h in enumerate(names)
                            if h in {"DATE", "TRADE DATE", "START TIME"}
                        ),
                        None,
                    )
                    if date_col is None:
                        continue
                    start = next(
                        i
                        for i, v in enumerate(header)
                        if isinstance(v, float) or str(v).startswith("Interval ")
                    )
                    for i in range(1, sheet.nrows):
                        raw = sheet.row_values(i)
                        if raw[date_col] == "":
                            continue
                        record = next(records)
                        day = (
                            xlrd.xldate_as_datetime(raw[date_col], book.datemode).date()
                            if isinstance(raw[date_col], float)
                            else date(*strptime(raw[date_col], "%m/%d/%y")[:3])
                        )
                        assert record.operatingDay == day
                        assert (
                            record.sourceMember,
                            record.sourceSheet,
                            record.sourceRow,
                        ) == (file["member"], sheet.name, i + 1)
                        assert record.kind == (
                            "generation" if "generation" in file["member"] else "load"
                        )
                        zone_col = next(
                            (
                                j
                                for j, h in enumerate(names)
                                if h.replace(" ", "") in {"CMZONE", "ZONE"}
                            ),
                            None,
                        )
                        assert record.zone == (
                            raw[zone_col] if zone_col is not None else sheet.name
                        )
                        mapped = {}
                        for interval in record.intervals:
                            j = start + interval.interval - 1
                            assert interval.energyMWh == number(raw[j])
                            if (
                                record.sourceSheet in {"H03", "N03", "S03", "W03"}
                                and day == date(2003, 10, 26)
                                or record.kind == "load"
                                and day == date(2005, 10, 30)
                            ):
                                assert interval.sourceLabel is None
                            elif isinstance(header[j], str):
                                assert interval.sourceLabel == header[j]
                            else:
                                minutes = round(header[j] * 1440) or 1440
                                assert (
                                    interval.sourceLabel
                                    == f"{minutes // 60:02}:{minutes % 60:02}"
                                )
                            mapped[j] = interval.energyMWh
                            counts["intervals"] += 1
                        total_col = next(
                            (
                                j
                                for j, h in enumerate(names)
                                if h in {"TOTAL", "TOTAL MWH"}
                            ),
                            None,
                        )
                        assert record.totalMWh == (
                            number(raw[total_col]) if total_col is not None else None
                        )
                        if total_col is not None:
                            mapped[total_col] = record.totalMWh
                        if "CHANNEL" in names:
                            mapped[names.index("CHANNEL")] = record.channel
                        for source in record.sourceNumbers:
                            j = source.column - 1
                            assert source.value == number(raw[j])
                            assert source.sourceHeader == (header[j] or None)
                            assert j not in mapped
                            mapped[j] = source.value
                            counts["sourceNumbers"] += 1
                        expected = {
                            j: number(v)
                            for j, v in enumerate(raw)
                            if isinstance(v, float)
                            and j != date_col
                            and not (
                                sheet.cell_type(i, j) == xlrd.XL_CELL_DATE
                                and j >= start + len(record.intervals)
                            )
                        }
                        assert {
                            j: v for j, v in mapped.items() if v is not None
                        } == expected
                        stamp_cols = [
                            j
                            for j in range(start + len(record.intervals), len(raw))
                            if sheet.cell_type(i, j) == xlrd.XL_CELL_DATE
                        ]
                        assert record.sourceTimestamp == (
                            xlrd.xldate_as_datetime(raw[stamp_cols[0]], book.datemode)
                            if stamp_cols
                            else None
                        )
                        for h, actual in [
                            ("RECORDER", record.recorder),
                            ("CUTNAME", record.recorder),
                            ("CHANNEL", record.channel),
                        ]:
                            if h in names:
                                assert actual == raw[names.index(h)]
                        counts["days"] += 1
                        if "2005_generation" in file["member"]:
                            gaps.setdefault(record.zone, set()).add(day)
                        if i == 1 or record.sourceNumbers:
                            assert (
                                ZonalEnergyDay.model_validate_json(
                                    record.model_dump_json()
                                )
                                == record
                            )
                assert next(records, None) is None
    assert counts == {"days": 13886, "intervals": 1361260, "sourceNumbers": 1170}
    missing = {date(2005, 6, 22) + timedelta(days=i) for i in range(37)}
    calendar = {date(2005, 1, 1) + timedelta(days=i) for i in range(365)}
    assert len(gaps) == 5
    assert all(calendar - days == missing for days in gaps.values())


def test_original_cached_totals_shares_and_undated_interval_aggregate():
    counts = Counter()
    generation_2001 = []
    with ZipFile(FIXTURE) as archive, Client() as client:
        for file in MANIFEST:
            data = archive.read(file["member"])
            with xlrd.open_workbook(file_contents=data) as book:
                for record in client.zonal_energy.read_totals(
                    data, filename=file["member"]
                ):
                    sheet = book.sheet_by_name(record.sourceSheet)
                    raw = sheet.row_values(record.sourceRow - 1)
                    header = next(
                        sheet.row_values(i)
                        for i in range(sheet.nrows)
                        if any(v != "" for v in sheet.row_values(i))
                    )
                    if record.scope == "summary":
                        assert record.totalMWh == number(raw[1])
                        assert record.share == number(raw[2])
                        assert record.sourceLabel == raw[0]
                        assert record.sourceTotalHeader == header[1]
                        assert record.sourceShareHeader == header[2]
                        counts["summary"] += 1
                    else:
                        start = next(
                            i
                            for i, v in enumerate(header)
                            if isinstance(v, float) or str(v).startswith("Interval ")
                        )
                        if record.sourceSheet == "W03":
                            assert record.totalMWh is None
                            assert record.sourceNumbers[0].value == number(raw[3])
                            assert record.sourceNumbers[0].sourceHeader == "ORIGIN"
                        else:
                            assert record.totalMWh == number(raw[start - 1])
                        if record.intervals:
                            assert record.sourceLabel == "Grand"
                            assert record.totalMWh is None
                            assert [r.energyMWh for r in record.intervals] == [
                                number(v) for v in raw[start:]
                            ]
                            counts["aggregateIntervals"] += len(record.intervals)
                        counts["detail"] += 1
                    assert (
                        ZonalEnergyTotal.model_validate_json(record.model_dump_json())
                        == record
                    )
                    if "2001_generation" in file["member"]:
                        generation_2001.append(record)
    assert counts == {"summary": 52, "detail": 36, "aggregateIntervals": 96}
    summary = next(r for r in generation_2001 if r.sourceLabel == "TOTAL ")
    detail = next(r for r in generation_2001 if r.scope == "detail_total")
    assert summary.totalMWh == Decimal("115512611.682897")
    assert detail.totalMWh == Decimal("115512613.08008096")
    assert summary.totalMWh != detail.totalMWh


def test_actual_discovery_anonymous_queries_and_saved_kind():
    with ZipFile(INPUTS / "loss-factors/indexes.zip") as z:
        pages = {n.removesuffix(".html"): z.read(n) for n in z.namelist()}
    with ZipFile(FIXTURE) as z:
        files = {f["url"]: z.read(f["member"]) for f in MANIFEST}
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        return httpx.Response(
            200,
            content=files[str(request.url)]
            if str(request.url) in files
            else pages[request.url.path.rsplit("/", 1)[-1]],
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        assert {(f.url, f.title) for f in client.zonal_energy.files()} == {
            (f["url"], f["title"]) for f in MANIFEST
        }
        requested.clear()
        rows = list(
            client.zonal_energy.rows(
                date_from=date(2001, 7, 31),
                date_to=date(2001, 7, 31),
                where=lambda r: r.zone == "N01",
            )
        )
        assert len(rows) == 1 and rows[0].kind == "generation"
        assert isinstance(rows[0].sourceFile, PublicFile)
        assert len(requested) == 36
        data = next(v for url, v in files.items() if "2001_load" in url)
        named = next(client.zonal_energy.read(data, kind="load"))
        assert named.operatingDay == date(2001, 8, 1)
        with pytest.raises(ValueError, match="Supply kind"):
            next(client.zonal_energy.read(data))
        assert (
            len(
                list(
                    client.zonal_energy.read_totals(
                        data, kind="load", where=lambda r: r.scope == "summary"
                    )
                )
            )
            == 4
        )
