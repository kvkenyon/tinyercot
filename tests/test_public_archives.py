import datetime
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from tinyercot.public import (
    AccessDeniedError,
    Limits,
    SchemaMismatchError,
    WebClient,
    sample_dam_archive,
)
from tinyercot.public._http import LimitError
from tinyercot.public.archives import checked_zip
from tinyercot.public.web import DOWNLOAD_URL, LIST_URL

FIXTURES = Path(__file__).parent / "fixtures/public"


def workbook_zip(*, extra=False, bad_header=False):
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Dec_1"
    # Cells transcribed from the first four rows of the real 2010 source file.
    rows = json.loads((FIXTURES / "annual-cells.json").read_text())["2010"]["rows"]
    if bad_header:
        rows[0][0] = "Unknown column"
    for row in rows:
        sheet.append([*row, "unexpected"] if extra else row)
    inner = io.BytesIO()
    book.save(inner)
    book.close()
    outer = io.BytesIO()
    with zipfile.ZipFile(outer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("DAMLZHBSPP_2010.xlsx", inner.getvalue())
    return outer.getvalue()


def source_fixture(raw):
    body = json.loads((FIXTURES / "dam-annual-list.json").read_text())
    entry = next(
        e
        for e in body["ListDocsByRptTypeRes"]["DocumentList"]
        if e["Document"]["FriendlyName"] == "DAMLZHBSPP_2010"
    )
    entry["Document"]["ContentSize"] = str(len(raw))
    body["ListDocsByRptTypeRes"]["DocumentList"] = [entry]
    return body


def test_download_decode_receipt_cache_and_revision_identity(tmp_path):
    raw = workbook_zip()
    listing = source_fixture(raw)
    calls = []

    def handler(request):
        calls.append(request)
        assert "Authorization" not in request.headers
        if str(request.url).startswith(LIST_URL):
            return httpx.Response(200, json=listing)
        assert str(request.url).startswith(DOWNLOAD_URL)
        return httpx.Response(200, content=raw)

    with WebClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        documents, receipt = client.dam_archives()
        assert receipt.sha256 and len(documents) == 1
        download = client.download_dam_archive(documents[0], cache=tmp_path)
        assert download.path.read_bytes() == raw
        sample = sample_dam_archive(download, sheet="Dec_1", max_rows=2)
        assert sample.rows[0].delivery_date == datetime.date(2010, 12, 1)
        assert str(sample.rows[1].settlement_point_price) == "35.33"
        assert sample.truncated
        cached = client.download_dam_archive(documents[0], cache=tmp_path)
        assert (
            cached.cache_hit and cached.receipt == download.receipt and len(calls) == 2
        )
        revised = replace(
            documents[0],
            published_at=documents[0].published_at + datetime.timedelta(days=1),
        )
        with pytest.raises(AccessDeniedError):
            client.download_dam_archive(revised, cache=tmp_path)
        download.path.write_bytes(b"tampered")
        with pytest.raises(SchemaMismatchError):
            client.download_dam_archive(documents[0], cache=tmp_path)
        assert len(calls) == 2


@pytest.mark.parametrize("security", ["C", "S", "", "unknown"])
def test_nonpublic_listing_never_allows_download(security):
    body = json.loads((FIXTURES / "dam-annual-list.json").read_text())
    body["ListDocsByRptTypeRes"]["DocumentList"][0]["Document"]["SecurityStatus"] = (
        security
    )
    with (
        WebClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=body)
            )
        ) as client,
        pytest.raises(AccessDeniedError),
    ):
        client.dam_archives()


@pytest.mark.parametrize(
    "bad",
    ["html", "traversal", "absolute", "duplicate", "symlink", "members", "expanded"],
)
def test_archive_structure_fails_closed(bad):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        if bad == "traversal":
            archive.writestr("../outside", b"x")
        elif bad == "absolute":
            archive.writestr("/outside", b"x")
        elif bad == "duplicate":
            archive.writestr("same", b"x")
            with pytest.warns(UserWarning):
                archive.writestr("same", b"y")
        elif bad == "symlink":
            item = zipfile.ZipInfo("link")
            item.external_attr = 0o120777 << 16
            archive.writestr(item, b"outside")
        elif bad == "members":
            archive.writestr("one", b"x")
            archive.writestr("two", b"y")
        else:
            archive.writestr("one", b"too large")
    raw = b"<html>No Document</html>" if bad == "html" else stream.getvalue()
    with pytest.raises((SchemaMismatchError, LimitError)):
        checked_zip(
            raw, max_members=1, max_expanded_bytes=1 if bad == "expanded" else 100
        )


@pytest.mark.parametrize("bad", ["extra", "header"])
def test_unknown_workbook_columns_are_not_silently_dropped(tmp_path, bad):
    raw = workbook_zip(extra=bad == "extra", bad_header=bad == "header")
    listing = source_fixture(raw)

    def handler(request):
        return (
            httpx.Response(200, json=listing)
            if str(request.url).startswith(LIST_URL)
            else httpx.Response(200, content=raw)
        )

    with WebClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        documents, _ = client.dam_archives()
        downloaded = client.download_dam_archive(documents[0], cache=tmp_path)
        with pytest.raises(SchemaMismatchError):
            sample_dam_archive(downloaded, sheet="Dec_1")


def test_failed_transfer_and_html_do_not_create_complete_receipt(tmp_path):
    raw = b"<html>No Document</html>"
    listing = source_fixture(raw)

    def handler(request):
        return (
            httpx.Response(200, json=listing)
            if str(request.url).startswith(LIST_URL)
            else httpx.Response(200, content=raw)
        )

    with WebClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        documents, _ = client.dam_archives()
        with pytest.raises(SchemaMismatchError):
            client.download_dam_archive(documents[0], cache=tmp_path)
        assert list(tmp_path.iterdir()) == []
