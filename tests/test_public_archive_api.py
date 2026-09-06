"""Verify generic archive receipts and failure boundaries without a network."""

import copy
import csv
import datetime
import hashlib
import io
import json
import stat
import zipfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from tinyercot.public._http import (
    AccessDeniedError,
    AuthenticationError,
    LimitError,
    RateLimitError,
    Receipt,
    SchemaMismatchError,
    SourceUnavailableError,
)
from tinyercot.public.api import Credentials
from tinyercot.public.api_archives import APIArchive, APIArchiveFile, APIBundle
from tinyercot.public.archive_api import ArchiveAPIClient, Limits
from tinyercot.public.archive_rows import sample_capacity_bundle, sample_retired_offers

FIXTURES = Path(__file__).parent / "fixtures/public"
SOURCE = json.loads((FIXTURES / "api-archive-excerpt.json").read_text())
BUNDLE = json.loads((FIXTURES / "api-bundle-excerpt.json").read_text())


def zip_bytes(name="unknown.csv", body=b"unknown\n1\n", mode=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        info = zipfile.ZipInfo(name)
        if mode is not None:
            info.external_attr = mode << 16
        archive.writestr(info, body)
    return stream.getvalue()


def make_client(*, kind="archive", response=None, limits=None, change=None):
    evidence = BUNDLE if kind == "bundle" else SOURCE
    product = copy.deepcopy(evidence["product"])
    listing = copy.deepcopy(evidence[kind + "_excerpt"])
    listing["_meta"]["totalRecords"] = len(listing[kind + "s"])
    if change:
        change(product, listing)
    calls = []

    def handle(request):
        calls.append(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"id_token": "synthetic-secret", "expires_in": 3600}
            )
        if request.url.path.endswith("/public-reports/"):
            return httpx.Response(200, json={"_embedded": {"products": [product]}})
        if request.method == "POST":
            return (
                response(request)
                if response
                else httpx.Response(
                    200,
                    content=zip_bytes(),
                    headers={"Content-Type": "application/zip"},
                )
            )
        return httpx.Response(200, json=listing)

    return ArchiveAPIClient(
        Credentials("synthetic-user", "synthetic-password", "synthetic-key"),
        limits=limits or Limits(min_interval=0, attempts=1),
        transport=httpx.MockTransport(handle),
    ), calls


@pytest.mark.parametrize("kind", ["archive", "bundle"])
def test_document_selection_verb_mime_receipt_and_route(kind):
    client, calls = make_client(kind=kind)
    identity = "NP4-190-CD" if kind == "bundle" else "NP3-988-ER"
    with client:
        client.products()
        page = (
            client.bundles(identity) if kind == "bundle" else client.archives(identity)
        )
        document = page.documents[0]
        downloaded = (
            client.download_bundle(document)
            if kind == "bundle"
            else client.download(document)
        )
        request = calls[-1]
        assert request.method == "POST"
        assert request.url.path.endswith(f"/{kind}/{identity.lower()}/download")
        assert json.loads(request.content) == {"docIds": [document.document_id]}
        assert request.headers["content-type"] == "application/json"
        assert downloaded.row_schema == "unknown"
        assert downloaded.members == ("unknown.csv",)
        assert downloaded.receipt.sha256 == hashlib.sha256(downloaded.body).hexdigest()
        assert len(client.exchanges) == 3
        assert client.exchanges[-1].document_ids == (document.document_id,)
        assert client.exchanges[-1].complete
        assert "synthetic-secret" not in repr(client.exchanges)
        assert "synthetic-key" not in repr(client.exchanges)
        assert all("token" not in x.receipt.source_url for x in client.exchanges)


@pytest.mark.parametrize(
    "status,error",
    [
        (400, SourceUnavailableError),
        (401, AuthenticationError),
        (403, AccessDeniedError),
        (404, SourceUnavailableError),
        (302, SourceUnavailableError),
        (429, RateLimitError),
        (500, SourceUnavailableError),
        (502, SourceUnavailableError),
    ],
)
def test_exact_failed_bundle_status_without_fallback(status, error):
    body = b'{"message":"synthetic error"}'
    client, calls = make_client(
        kind="bundle",
        response=lambda r: httpx.Response(
            status,
            content=body,
            headers={
                "Content-Type": "application/json",
                "Location": "https://other.invalid/",
            },
        ),
    )
    with client:
        client.products()
        document = client.bundles("NP4-190-CD").documents[0]
        with pytest.raises(error):
            client.download_bundle(document)
        receipt = client.exchanges[-1].receipt
        assert receipt.status == status
        assert receipt.sha256 == hashlib.sha256(body).hexdigest()
        assert receipt.byte_count == len(body)
        assert len(calls) == 4


@pytest.mark.parametrize(
    "media", ["text/html", "application/json", "application/octet-stream", ""]
)
def test_zip_requires_documented_content_type(media):
    client, _ = make_client(
        response=lambda r: httpx.Response(
            200,
            content=zip_bytes(),
            headers={"content-type": media},
        )
    )
    with client:
        client.products()
        document = client.archives("NP3-988-ER").documents[0]
        with pytest.raises(SchemaMismatchError, match="content type"):
            client.download(document)
        assert client.exchanges[-1].receipt.status == 200


@pytest.mark.parametrize(
    "raw",
    [
        b"not a ZIP",
        zip_bytes("../outside"),
        zip_bytes("/absolute"),
        zip_bytes("C:drive"),
        zip_bytes("a\\b"),
        zip_bytes("link", mode=stat.S_IFLNK | 0o777),
    ],
)
def test_malformed_zip_and_paths(raw):
    client, _ = make_client(
        response=lambda r: httpx.Response(
            200,
            content=raw,
            headers={"content-type": "application/zip"},
        )
    )
    with client:
        client.products()
        with pytest.raises(SchemaMismatchError):
            client.download(client.archives("NP3-988-ER").documents[0])


def test_zip_crc_and_expansion_limits():
    good = zip_bytes(body=b"unique payload")
    bad = good.replace(b"unique payload", b"broken payload", 1)
    for raw, error, kwargs in [
        (bad, SchemaMismatchError, {}),
        (good, LimitError, {"max_expanded_bytes": 1}),
    ]:
        client, _ = make_client(
            response=lambda r, raw=raw: httpx.Response(
                200,
                content=raw,
                headers={"content-type": "application/zip"},
            )
        )
        with client:
            client.products()
            with pytest.raises(error):
                client.download(client.archives("NP3-988-ER").documents[0], **kwargs)


def test_response_size_prefix_receipt_and_no_retry():
    raw = b"x" * 70000
    client, calls = make_client(
        response=lambda r: httpx.Response(
            200,
            content=raw,
            headers={"content-type": "application/zip"},
        ),
        limits=Limits(max_bytes=16000, min_interval=0, attempts=3),
    )
    with client:
        client.products()
        document = client.archives("NP3-988-ER").documents[0]
        with pytest.raises(LimitError):
            client.download(document)
        exchange = client.exchanges[-1]
        assert not exchange.complete
        assert exchange.receipt.byte_count == 16000
        assert exchange.receipt.sha256 == hashlib.sha256(raw[:16000]).hexdigest()
        assert len(calls) == 4


def test_retry_and_total_request_budgets():
    client, calls = make_client(
        response=lambda r: httpx.Response(
            503,
            content=b"busy",
            headers={"Retry-After": "0"},
        ),
        limits=Limits(min_interval=0, attempts=3, max_requests=5),
    )
    with client:
        client.products()
        document = client.archives("NP3-988-ER").documents[0]
        with pytest.raises(LimitError, match="request budget"):
            client.download(document)
        assert len(calls) == 5
        assert [x.receipt.status for x in client.exchanges[-2:]] == [503, 503]


def test_retry_after_cannot_extend_budget():
    client, calls = make_client(
        response=lambda r: httpx.Response(
            429,
            content=b"busy",
            headers={"Retry-After": "999"},
        ),
        limits=Limits(min_interval=0, attempts=3, max_retry_wait=1),
    )
    with client:
        client.products()
        with pytest.raises(RateLimitError, match="wait budget"):
            client.download(client.archives("NP3-988-ER").documents[0])
        assert len(calls) == 4


@pytest.mark.parametrize("access", ["Secure", "Certified", "unknown", None])
def test_access_is_fail_closed(access):
    client, calls = make_client(
        change=lambda p, l: p.update(securityClassification=access)
    )
    with client:
        client.products()
        with pytest.raises(AccessDeniedError):
            client.archives("NP3-988-ER")
        assert len(calls) == 2


def test_binary_retired_history_is_supported_file_access():
    client, _ = make_client(
        change=lambda p, l: p.update(contentType="BINARY", status="Retired")
    )
    with client:
        products, _ = client.products()
        assert products[0].content_type == "BINARY"
        page = client.archives("NP3-988-ER")
        assert page.lifecycle == "retired-or-inactive"
        assert client.download(page.documents[0]).row_schema == "unknown"
        with pytest.raises(AccessDeniedError):
            client.download(replace(page.documents[0], document_id=1))
        client.products()
        with pytest.raises(AccessDeniedError):
            client.download(page.documents[0])


def test_source_contract_has_no_listing_query_or_get_download():
    source = json.loads((FIXTURES / "archive_api/source-contracts.json").read_text())
    assert source["selection_schema"]["required"] == ["docIds"]
    for op in source["operations"]:
        assert op["query"] == []
        if op["urlTemplate"].endswith("/download"):
            assert op["method"] == "POST"
            assert op["request_media"] == ["application/json"]
            assert op["responses"][0] == {"status": 200, "media": ["application/zip"]}


def sample_file(index, change=None, inner_path=None):
    source = json.loads((FIXTURES / "archive_api/rows.json").read_text())["samples"][
        index
    ]
    rows = [source["header"], *source["rows_excerpt"]]
    if change:
        change(rows)
    stream = io.StringIO(newline="")
    csv.writer(stream).writerows(rows)
    inner = zip_bytes(inner_path or source["inner_member"], stream.getvalue().encode())
    raw = zip_bytes(source["outer_member"], inner)
    document = (APIBundle if index == 0 else APIArchive)(**source["document"])
    receipt = Receipt(
        source["receipt"]["source_url"],
        datetime.datetime.now(datetime.UTC),
        hashlib.sha256(raw).hexdigest(),
        len(raw),
    )
    return APIArchiveFile(document, receipt, (source["outer_member"],), raw)


@pytest.mark.parametrize(
    "index,decoder", [(0, sample_capacity_bundle), (1, sample_retired_offers)]
)
def test_source_backed_nested_csv_sample(index, decoder):
    file = sample_file(index)
    sample = decoder(file, member=file.members[0], max_rows=1)
    assert sample.truncated and len(sample.rows) == 1
    assert sample.receipt == file.receipt
    assert sample.rows[0].hour_ending == "01:00"
    if index == 0:
        assert sample.rows[0].mcpc == Decimal("1.64")
        assert sample.rows[0].delivery_date == datetime.date(2026, 8, 13)
    else:
        assert sample.rows[0].regdn == Decimal("5677.8")
        assert sample.rows[0].delivery_date == datetime.date(2025, 12, 5)


@pytest.mark.parametrize(
    "change",
    [
        lambda rows: rows[0].__setitem__(0, "UnknownHeader"),
        lambda rows: rows[1].__setitem__(3, "NaN"),
        lambda rows: rows[1].__setitem__(0, "02/30/2026"),
        lambda rows: rows[1].__setitem__(1, "25:00"),
        lambda rows: rows[1].__setitem__(-1, "unknown"),
        lambda rows: rows[1].pop(),
    ],
)
def test_nested_csv_schema_and_values_fail_closed(change):
    file = sample_file(0, change)
    with pytest.raises(SchemaMismatchError):
        sample_capacity_bundle(file, member=file.members[0])


def test_nested_zip_path_receipt_and_selection_checks():
    file = sample_file(0, inner_path="../outside.csv")
    with pytest.raises(SchemaMismatchError):
        sample_capacity_bundle(file, member=file.members[0])
    file = sample_file(0)
    with pytest.raises(AccessDeniedError):
        sample_retired_offers(file, member=file.members[0])
    with pytest.raises(SchemaMismatchError):
        sample_capacity_bundle(
            replace(file, body=file.body + b"changed"), member=file.members[0]
        )
    with pytest.raises(SchemaMismatchError):
        sample_capacity_bundle(file, member="unlisted.zip")
    with pytest.raises(ValueError):
        sample_capacity_bundle(file, member=file.members[0], max_rows=0)
