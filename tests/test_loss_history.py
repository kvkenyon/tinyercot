import csv
import json
import re
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import xlrd

from tinyercot import Client, LoadArchive, LossFactorDay

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
EVIDENCE = json.loads((INPUTS / "public-loss-history-evidence.json").read_text())


def fixture_rows(client, archive, f):
    source = LoadArchive(
        year=int(re.search(r"\d{4}", f["title"])[0]), title=f["title"], url=f["url"]
    )
    return client.loss_factors.read(
        archive.read(f["member"]), filename=f["member"], source_file=source
    )


def test_all_captured_year_indexes_discover_every_interval_archive():
    requested = []
    with ZipFile(INPUTS / "loss-factors/indexes.zip") as z:
        pages = {n.removesuffix(".html"): z.read(n) for n in z.namelist()}
    manifest = list(
        csv.DictReader(
            StringIO((INPUTS / "public-loss-history-sources.csv").read_text())
        )
    )

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        return httpx.Response(200, content=pages[request.url.path.rsplit("/", 1)[-1]])

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        archives = client.loss_factors.archives()
    assert len(archives) == len(manifest) == 72
    assert {(a.title, a.url) for a in archives} == {
        (f["title"], f["url"]) for f in manifest
    }
    assert {a.year for a in archives} == set(range(2001, 2027))
    assert len(requested) == len(set(requested)) == 26


def test_all_original_legacy_values_and_identifiers():
    with Client() as client, ZipFile(INPUTS / "loss-factors/legacy.zip") as archive:
        for f in EVIDENCE["fixture"]["workbooks"]:
            data = archive.read(f["member"])
            if data.startswith(b"\xd0\xcf"):
                book = xlrd.open_workbook(file_contents=data)
                source = [
                    (
                        sheet.name,
                        [
                            tuple(
                                xlrd.xldate_as_datetime(c.value, book.datemode)
                                if c.ctype == xlrd.XL_CELL_DATE
                                else c.value
                                for c in sheet.row(i)
                            )
                            for i in range(1, sheet.nrows)
                        ],
                    )
                    for sheet in book.sheets()
                ]
                book.release_resources()
            else:
                book = openpyxl.load_workbook(
                    BytesIO(data), read_only=True, data_only=True
                )
                source = [(s.title, list(s.values)[1:]) for s in book]
                book.close()
            records = fixture_rows(client, archive, f)
            count = 0
            for sheet, rows in source:
                for cells in rows:
                    if cells[2] in (None, ""):
                        # Blank/styled rows and orphan code labels have no observations.
                        assert all(
                            c in (None, "") for i, c in enumerate(cells) if i != 1
                        )
                        continue
                    r = next(records)
                    count += 1
                    last = max(i for i, c in enumerate(cells) if c not in (None, ""))
                    assert r.sourceSheet == sheet and r.sourceMember == f["member"]
                    assert r.sourceStartTime == cells[2]
                    stamp = cells[last]
                    assert r.sourceLastTime == (
                        datetime.strptime(stamp.strip(), "%m/%d/%Y %H:%M:%S")  # noqa: DTZ007 -- source has no offset
                        if isinstance(stamp, str)
                        else stamp
                    )
                    assert [v.factor for v in r.intervals] == [
                        None if c in (None, "") else Decimal(str(c))
                        for c in cells[4:last]
                    ]
                    assert [v.interval for v in r.intervals] == list(range(1, last - 3))
                    assert (r.recorder or r.tdsp) == cells[0]
                    assert r.sourceSecondaryIdentifier == (
                        cells[1] if cells[1] not in (None, "") else None
                    )
                    assert r.sourceMarker == (
                        cells[3] if cells[3] not in (None, "") else None
                    )
            assert next(records, None) is None
            assert count == f["rows"]


def test_repeated_clocks_extra_intervals_and_raw_identifiers():
    days = []
    cases = {
        "2001_historical_actual": date(2001, 10, 28),
        "tlf_actual_for_2013": date(2013, 11, 3),
        "dlf_forecasted_for_2014": date(2014, 11, 2),
        "2004_historical_distribution": date(2004, 10, 31),
    }
    with Client() as client, ZipFile(INPUTS / "loss-factors/legacy.zip") as archive:
        for prefix, day in cases.items():
            f = next(
                f
                for f in EVIDENCE["fixture"]["workbooks"]
                if f["member"].startswith(prefix)
            )
            days.extend(
                r for r in fixture_rows(client, archive, f) if r.operatingDay == day
            )
    fallback = next(
        r
        for r in days
        if r.sourceMember.startswith("2001_historical_actual")
        and "DST" in r.sourceSheet
    )
    assert len(fallback.intervals) == 100
    assert len({v.sourceLabel for v in fallback.intervals}) == 96
    extra = next(
        r
        for r in days
        if r.sourceMember.startswith("tlf_actual_for_2013")
        and len(r.intervals) == 100
        and r.sourceSheet == "TLF for 2013"
    )
    assert extra.operatingDay == date(2013, 11, 3)
    assert all(v.sourceLabel is None for v in extra.intervals)
    assert extra.sourceLastTime == datetime.fromisoformat("2013-11-04T01:00:10")
    missing = [r for r in days if r.recorder and r.recorder.startswith("DISTLOSSFACT_")]
    assert len(missing) == 19
    assert all(r.tdsp is None and r.lossCode is None for r in missing)
    assert missing[0].recorder == "DISTLOSSFACT_1_D"
    assert missing[0].sourceSecondaryIdentifier == 1
    assert isinstance(missing[0].sourceSecondaryIdentifier, int)
    assert missing[0].kind == "forecast"
    assert any(r.sourceMarker == "C" for r in days)
    assert LossFactorDay.model_validate_json(missing[0].model_dump_json()) == missing[0]


def test_early_distribution_kind_requires_published_label():
    f = next(
        f
        for f in EVIDENCE["fixture"]["workbooks"]
        if f["member"].startswith("2001_historical_distribution")
    )
    with ZipFile(INPUTS / "loss-factors/legacy.zip") as z:
        data = z.read(f["member"])
    index = "https://www.ercot.com/mktinfo/data_agg"

    def handler(request):
        if str(request.url) == index:
            return httpx.Response(200, text=f'<a href="{f["url"]}">{f["title"]}</a>')
        return httpx.Response(200, content=data)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.loss_factors.rows(
                date_from=date(2001, 10, 28),
                date_to=date(2001, 10, 28),
                where=lambda r: r.kind == "forecast",
            )
        )
        saved = next(client.loss_factors.read(data))
    assert saved.kind is None and saved.sourceFile is None
    assert len(rows) == 14
    assert all(r.kind == "forecast" and len(r.intervals) == 100 for r in rows)
    assert all(r.sourceFile.title == f["title"] for r in rows)
    assert Counter(r.level for r in rows) == {"distribution": 14}
