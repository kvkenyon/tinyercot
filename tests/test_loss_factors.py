from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, LossFactorDay
from tinyercot._loss_factors import INDEX_URL

FIXTURE = (
    Path(__file__).resolve().parents[1] / "tools/inputs/loss-factors/historical.xlsx"
)
ARCHIVE_URL = "https://www.ercot.com/files/docs/2025/02/14/Historical-Loss-Factors_2026-01-01_thru_2026-07-31_20260805.xlsx"


@pytest.fixture(scope="module")
def loss_days():
    with Client() as client:
        return list(
            client.loss_factors.read(FIXTURE.read_bytes(), filename=FIXTURE.name)
        )


def test_source_series_identifiers_and_typed_roundtrip(loss_days):
    assert Counter(r.sourceSheet for r in loss_days) == {
        "ACTUAL_TLF": 4,
        "FORECASTED_TLF": 4,
        "ACTUAL_DLF": 68,
        "FORECASTED_DLF": 68,
    }
    assert len({(r.kind, r.level, r.tdsp, r.lossCode) for r in loss_days}) == 36
    assert all(r.sourceMember == FIXTURE.name for r in loss_days)
    first = loss_days[0]
    assert first.kind == "actual" and first.level == "transmission"
    assert first.recorder == "ACTLOSSFACT"
    assert first.tdsp is None and first.lossCode is None
    assert first.sourceStartTime == datetime.fromisoformat("2026-01-01T00:00:00")
    assert first.sourceLastTime == datetime.fromisoformat("2026-01-02T00:18:01")
    assert first.intervals[0].factor == Decimal("0.0194541811943054")
    assert LossFactorDay.model_validate_json(first.model_dump_json()) == first


def test_all_original_interval_cells_and_timestamps(loss_days):
    book = openpyxl.load_workbook(FIXTURE, read_only=True, data_only=True)
    records = iter(loss_days)
    try:
        for sheet in book:
            # Source dimensions incorrectly declare 1,048,576 rows.
            assert sheet.max_row == 1048576
            sheet.reset_dimensions()
            source = sheet.values
            columns = {label: n for n, label in enumerate(next(source))}
            for cells in source:
                row = next(records)
                assert row.sourceStartTime == cells[columns["STARTTIME"]]
                assert row.sourceLastTime == cells[columns["LSTIME"]]
                assert row.recorder == cells[columns["SAVERECORDER"]]
                assert row.tdsp == (
                    cells[columns["TDSPNAME"]] if "TDSPNAME" in columns else None
                )
                assert row.lossCode == (
                    cells[columns["LOSSCODE"]] if "LOSSCODE" in columns else None
                )
                assert len(row.intervals) == 100
                for n, interval in enumerate(row.intervals, 1):
                    value = cells[columns[f"INTV{n}"]]
                    assert interval.interval == n
                    assert interval.factor == (
                        None if value is None else Decimal(str(value))
                    )
        assert next(records, None) is None
    finally:
        book.close()


def test_short_day_and_unused_columns_remain_in_source_order(loss_days):
    for row in loss_days:
        present = 92 if row.operatingDay == date(2026, 3, 8) else 96
        assert sum(v.factor is not None for v in row.intervals) == present
        assert [v.interval for v in row.intervals] == list(range(1, 101))
        assert all(v.factor is None for v in row.intervals[96:])


def test_query_discovers_actual_href_and_filters_operating_date():
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        if str(request.url) == INDEX_URL:
            return httpx.Response(
                200,
                text=f'<a href="{ARCHIVE_URL}">Historical Loss Factors_2026-01-01_thru_2026-07-31_20260706</a>',
            )
        assert str(request.url) == ARCHIVE_URL
        return httpx.Response(200, content=FIXTURE.read_bytes())

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.loss_factors.rows(
                date_from=date(2026, 1, 1),
                date_to=date(2026, 1, 1),
                where=lambda r: r.kind == "forecast" and r.level == "transmission",
            )
        )
    assert len(rows) == 1
    assert rows[0].operatingDay == date(2026, 1, 1)
    assert rows[0].sourceLastTime == datetime.fromisoformat("2025-12-30T01:15:53")
    assert rows[0].sourceMember == ARCHIVE_URL.rsplit("/", 1)[-1]
    assert requested == [INDEX_URL, ARCHIVE_URL]


def test_saved_archives_preserve_overlapping_members_and_typed_filter():
    archive = BytesIO()
    with ZipFile(archive, "w") as z:
        z.writestr("first.xlsx", FIXTURE.read_bytes())
        z.writestr("revised.xlsx", FIXTURE.read_bytes())
    with Client() as client:
        rows = list(
            client.loss_factors.read(
                archive.getvalue(),
                date_from=date(2026, 7, 31),
                where=lambda r: (
                    r.level == "distribution"
                    and r.tdsp == "AEP TEXAS CENTRAL COMPANY"
                    and r.lossCode == "A"
                ),
            )
        )
    assert len(rows) == 4
    assert {r.sourceMember for r in rows} == {"first.xlsx", "revised.xlsx"}
    assert {r.kind for r in rows} == {"actual", "forecast"}


def test_reversed_bounds_fail_before_network_access():
    with Client() as client:
        for reader in (
            client.loss_factors.rows,
            lambda **kw: client.loss_factors.read(b"", **kw),
        ):
            with pytest.raises(ValueError, match="date_from"):
                list(reader(date_from=date(2026, 2, 1), date_to=date(2026, 1, 1)))


def test_changed_header_reports_source_instead_of_silent_misalignment():
    book = openpyxl.load_workbook(FIXTURE)
    book["ACTUAL_TLF"]["C1"] = "RENAMED_INTERVAL"
    data = BytesIO()
    book.save(data)
    book.close()
    with Client() as client, pytest.raises(ValueError, match="changed.xlsx/ACTUAL_TLF"):
        list(client.loss_factors.read(data.getvalue(), filename="changed.xlsx"))
