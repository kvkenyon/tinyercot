"""Mocked archive transport with source-derived public document metadata."""

import copy
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from tinyercot.public import Credentials, Limits
from tinyercot.public._http import (
    AccessDeniedError,
    LimitError,
    SchemaMismatchError,
)
from tinyercot.public.api_archives import APIArchive, APIArchiveClient

EVIDENCE = json.loads(
    (Path(__file__).parent / "fixtures/public/api-archive-excerpt.json").read_text()
)


def archive_client(*, product_change=None, archive_change=None, raw=None):
    product = copy.deepcopy(EVIDENCE["product"])
    product.update(product_change or {})
    listing = copy.deepcopy(EVIDENCE["archive_excerpt"])
    listing["_meta"]["totalRecords"] = 2
    if archive_change:
        archive_change(listing)
    if raw is None:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as zipped:
            zipped.writestr("unknown.csv", "UnverifiedColumn\nvalue\n")
        raw = stream.getvalue()
    calls = []

    def handle(request):
        calls.append(request)
        if request.method == "POST" and "token" in request.url.path:
            return httpx.Response(
                200, json={"id_token": "synthetic-token", "expires_in": 3600}
            )
        if request.url.path.endswith("/public-reports/"):
            return httpx.Response(200, json={"_embedded": {"products": [product]}})
        if request.method == "POST":
            assert request.url.path.endswith("/archive/np3-988-er/download")
            assert request.headers["content-type"].startswith("application/json")
            assert json.loads(request.content) == {"docIds": [1270779234]}
            return httpx.Response(200, content=raw)
        return httpx.Response(200, json=listing)

    client = APIArchiveClient(
        Credentials("synthetic@example.test", "synthetic-password", "synthetic-key"),
        limits=Limits(min_interval=0),
        transport=httpx.MockTransport(handle),
    )
    return client, calls


def test_public_metadata_gate_and_single_selected_download():
    client, calls = archive_client()
    with client:
        with pytest.raises(ValueError, match="products"):
            client.archives("np3-988-er")
        assert not calls
        client.products()
        page = client.archives("NP3-988-ER")
        assert page.total_records == 2 and page.current_page == page.total_pages == 1
        assert len(page.documents) == 2
        document = page.documents[0]
        assert document.post_datetime == "2026-09-05T05:02:43.000"
        downloaded = client.download(document)
        assert downloaded.row_schema == "unknown"
        assert downloaded.members == ("unknown.csv",)
        assert "UnverifiedColumn" not in repr(downloaded)
        assert downloaded.receipt.byte_count == len(downloaded.body)
        assert len(calls) == 4


@pytest.mark.parametrize("classification", ["Secure", "Certified", "Unknown", None])
def test_nonpublic_gate_before_archive_request(classification):
    client, calls = archive_client(
        product_change={"securityClassification": classification}
    )
    with client:
        client.products()
        with pytest.raises(AccessDeniedError):
            client.archives("np3-988-er")
        assert len(calls) == 2


@pytest.mark.parametrize("status", ["Inactive", "Retired"])
def test_public_inactive_history_remains_selectable(status):
    client, calls = archive_client(product_change={"status": status})
    with client:
        client.products()
        page = client.archives("np3-988-er")
        assert page.lifecycle == "retired-or-inactive"
        assert client.download(page.documents[0]).row_schema == "unknown"
        assert len(calls) == 4


def test_audited_retirement_is_visible_without_blocking_public_listing():
    def retired_listing(body):
        body["product"]["emilId"] = "NP6-569-CD"
        body["_links"]["self"]["href"] = body["_links"]["self"]["href"].replace(
            "np3-988-er", "np6-569-cd"
        )
        for item in body["archives"]:
            link = item["_links"]["endpoint"]
            link["href"] = link["href"].replace("np3-988-er", "np6-569-cd")

    client, _ = archive_client(
        product_change={"emilId": "NP6-569-CD"}, archive_change=retired_listing
    )
    with client:
        client.products()
        page = client.archives("np6-569-cd")
        assert page.lifecycle == "retired-or-inactive"
        assert len(page.documents) == 2


def test_unlisted_changed_and_refreshed_documents_fail_closed():
    client, calls = archive_client()
    with client:
        client.products()
        page = client.archives("np3-988-er")
        with pytest.raises(AccessDeniedError):
            client.download(APIArchive("private", 123, "unknown", "unknown"))
        with pytest.raises(AccessDeniedError):
            client.download(replace(page.documents[0], document_id=123))
        assert len(calls) == 3
        client.products()
        with pytest.raises(AccessDeniedError):
            client.download(page.documents[0])
        assert len(calls) == 4


@pytest.mark.parametrize(
    "change",
    [
        lambda body: body["product"].update(emilId="private"),
        lambda body: body["_meta"].update(totalRecords=3),
        lambda body: body["archives"][0].update(docId=True),
        lambda body: body["archives"][0].update(postDatetime="yesterday"),
        lambda body: body["archives"][0]["_links"]["endpoint"].update(
            href="https://example.test/private"
        ),
    ],
)
def test_metadata_contract_drift(change):
    client, _ = archive_client(archive_change=change)
    with client:
        client.products()
        with pytest.raises(SchemaMismatchError):
            client.archives("np3-988-er")


def test_html_download_and_zip_expansion_limits():
    for raw, error in [
        (b"<html>No Document</html>", SchemaMismatchError),
        (None, LimitError),
    ]:
        client, _ = archive_client(raw=raw)
        with client:
            client.products()
            document = client.archives("np3-988-er").documents[0]
            with pytest.raises(error):
                client.download(document, max_expanded_bytes=1)
