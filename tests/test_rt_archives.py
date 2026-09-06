"""Public RT archive boundaries, streaming, and immutable cache behavior."""

import datetime
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from openpyxl import Workbook

from tinyercot.public._http import (
    AccessDeniedError,
    LimitError,
    Limits,
    SchemaMismatchError,
)
from tinyercot.public.archive_reports import (
    RTArchiveClient,
    RTArchivePrice,
    iter_rt_archive,
)

EVIDENCE = json.loads(
    (Path(__file__).parent / "fixtures/public/rt-archive-excerpt.json").read_text()
)


def workbook_zip(*, rows=None, header=None, second=True):
    """Build a tiny workbook from the recorded public source cells."""
    book = Workbook()
    book.active.title = "Dec_1"
    data = EVIDENCE["samples"][0]
    for sheet in [book.active] + ([book.create_sheet("Copy")] if second else []):
        sheet.append(header or data["header"])
        for row in data["rows"] if rows is None else rows:
            sheet.append(row)
    inner = io.BytesIO()
    book.save(inner)
    book.close()
    outer = io.BytesIO()
    with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("rt.xlsx", inner.getvalue())
    return outer.getvalue()


def client_for(raw, *, mutate=None):
    """Provide public listing and ZIP transport with request accounting."""
    document = dict(EVIDENCE["samples"][0]["listing_document"])
    document["ContentSize"] = str(len(raw))
    if mutate:
        document.update(mutate)
    calls = []

    def handle(request):
        calls.append(request.url)
        assert "authorization" not in request.headers
        if "IceDocListJsonWS" in request.url.path:
            assert request.url.params["reportTypeId"] == "13061"
            return httpx.Response(
                200,
                json={
                    "ListDocsByRptTypeRes": {"DocumentList": [{"Document": document}]}
                },
            )
        assert request.url.params["reportTypeId"] == "13061"
        return httpx.Response(200, content=raw)

    return RTArchiveClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handle)
    ), calls


def test_complete_iteration_and_cache(tmp_path):
    client, calls = client_for(workbook_zip())
    with client:
        documents, receipt = client.archives()
        assert receipt.source_url.endswith("reportTypeId=13061")
        download = client.download(documents[0], cache=tmp_path)
        rows = list(iter_rt_archive(download, max_rows=None, max_scan_rows=None))
        assert len(rows) == 6
        assert [r.sheet for r in rows] == ["Dec_1"] * 3 + ["Copy"] * 3
        assert rows[0].row == RTArchivePrice(
            delivery_date=datetime.date(2010, 12, 1),
            delivery_hour=1,
            delivery_interval=1,
            repeated_hour_flag="N",
            settlement_point_name="HB_BUSAVG",
            settlement_point_type="SH",
            settlement_point_price=Decimal("25.08"),
        )
        assert rows[0].row_number == 2
        cached = client.download(documents[0], cache=tmp_path)
        assert cached.cache_hit and cached.receipt == download.receipt
        assert len(calls) == 2
        with pytest.raises(LimitError, match="row budget"):
            list(iter_rt_archive(download, max_rows=1))
        with pytest.raises(LimitError, match="scan budget"):
            list(iter_rt_archive(download, max_scan_rows=1))
        with pytest.raises(SchemaMismatchError, match="absent"):
            list(iter_rt_archive(download, sheets=["missing"]))


@pytest.mark.parametrize(
    "change",
    [
        {"SecurityStatus": "S"},
        {"ReportTypeID": "13060"},
        {"DocID": "../1"},
        {"FriendlyName": "private"},
    ],
)
def test_listing_fail_closed(change):
    client, calls = client_for(workbook_zip(), mutate=change)
    with client, pytest.raises((AccessDeniedError, SchemaMismatchError)):
        client.archives()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "cells",
    [
        ["12/01/2010", "1", 1, "N", "HB_BUSAVG", "SH", 25.08],
        ["12/01/2010", 1, 5, "N", "HB_BUSAVG", "SH", 25.08],
        ["12/01/2010", 1, 1, "N", "HB_BUSAVG", "SH", "25.08"],
        ["12/01/2026", 1, 1, "N", "HB_BUSAVG", "SH", 25.08],
        ["12/01/2010", 1, 1, None, "HB_BUSAVG", "SH", 25.08],
    ],
)
def test_unknown_cell_contract(tmp_path, cells):
    client, _ = client_for(workbook_zip(rows=[cells]))
    with client:
        documents, _ = client.archives()
        download = client.download(documents[0], cache=tmp_path)
        with pytest.raises(SchemaMismatchError):
            list(iter_rt_archive(download))


def test_unknown_epoch(tmp_path):
    client, _ = client_for(workbook_zip(header=["unknown"] * 7))
    with client:
        documents, _ = client.archives()
        download = client.download(documents[0], cache=tmp_path)
        with pytest.raises(SchemaMismatchError, match="schema epoch"):
            list(iter_rt_archive(download))


def test_changed_cache_and_unlisted_document(tmp_path):
    client, calls = client_for(workbook_zip())
    with client:
        documents, _ = client.archives()
        with pytest.raises(AccessDeniedError):
            client.download(replace(documents[0], security="S"), cache=tmp_path)
        download = client.download(documents[0], cache=tmp_path)
        download.path.write_bytes(b"changed")
        with pytest.raises(SchemaMismatchError):
            client.download(documents[0], cache=tmp_path)
        with pytest.raises(SchemaMismatchError):
            list(iter_rt_archive(download))
        assert len(calls) == 2


def test_provenance_hashes():
    assert EVIDENCE["product_id"] == "NP6-785-ER"
    for sample in EVIDENCE["samples"]:
        assert len(sample["receipt"]["sha256"]) == hashlib.sha256().digest_size * 2
        assert sample["listing_document"]["SecurityStatus"] == "P"


def test_complete_iteration_exceeds_default_budget(tmp_path):
    source_row = EVIDENCE["samples"][0]["rows"][0]
    client, _ = client_for(workbook_zip(rows=[source_row] * 1001))
    with client:
        documents, _ = client.archives()
        download = client.download(documents[0], cache=tmp_path)
        assert (
            sum(1 for _ in iter_rt_archive(download, max_rows=None, max_scan_rows=None))
            == 2002
        )
        with pytest.raises(LimitError, match="row budget"):
            list(iter_rt_archive(download))


def test_html_success_is_not_a_download(tmp_path):
    client, _ = client_for(b"<html>No Document</html>")
    with client:
        documents, _ = client.archives()
        with pytest.raises(SchemaMismatchError, match="ZIP"):
            client.download(documents[0], cache=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_advertised_budget_is_checked_before_download(tmp_path):
    client, calls = client_for(workbook_zip(), mutate={"ContentSize": "16000001"})
    with client:
        documents, _ = client.archives()
        with pytest.raises(LimitError, match="Advertised"):
            client.download(documents[0], cache=tmp_path)
    assert len(calls) == 1
