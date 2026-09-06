"""Explicit signed bundle IDs and route separation from source metadata."""

import copy
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from tinyercot.public import Credentials, Limits
from tinyercot.public._http import AccessDeniedError, SchemaMismatchError
from tinyercot.public.api_archives import (
    APIArchive,
    APIArchiveClient,
    APIBundle,
    APIBundlePage,
)

EVIDENCE = json.loads(
    (Path(__file__).parent / "fixtures/public/api-bundle-excerpt.json").read_text()
)


def bundle_client(change=None):
    body = copy.deepcopy(EVIDENCE["bundle_excerpt"])
    body["_meta"]["totalRecords"] = len(body["bundles"])
    if change:
        change(body)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipped:
        zipped.writestr("unknown.csv", "Unknown\n1\n")
    calls = []

    def handle(request):
        calls.append(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        if request.url.path.endswith("/public-reports/"):
            return httpx.Response(
                200, json={"_embedded": {"products": [EVIDENCE["product"]]}}
            )
        if request.method == "POST":
            assert request.url.path.endswith("/bundle/np4-190-cd/download")
            assert json.loads(request.content) == {"docIds": [-1257192853]}
            return httpx.Response(200, content=buffer.getvalue())
        assert request.url.path.endswith("/bundle/np4-190-cd")
        return httpx.Response(200, json=body)

    return APIArchiveClient(
        Credentials("synthetic", "synthetic", "synthetic"),
        limits=Limits(min_interval=0),
        transport=httpx.MockTransport(handle),
    ), calls


def test_signed_bundle_contract_and_explicit_download():
    client, calls = bundle_client()
    with client:
        client.products()
        page = client.bundles("NP4-190-CD")
        assert isinstance(page, APIBundlePage)
        assert isinstance(page.documents[0], APIBundle)
        assert page.documents[0].document_id == -1257192853
        file = client.download_bundle(page.documents[0])
        assert file.row_schema == "unknown"
        assert file.document == page.documents[0]
        assert len(calls) == 4


def test_bundle_and_archive_routes_never_fall_back():
    client, calls = bundle_client()
    with client:
        client.products()
        document = client.bundles("NP4-190-CD").documents[0]
        with pytest.raises(AccessDeniedError):
            client.download(document)
        with pytest.raises(AccessDeniedError):
            client.download_bundle(replace(document, document_id=123))
        ordinary = APIArchive(
            document.emil_id,
            document.document_id,
            document.friendly_name,
            document.post_datetime,
        )
        with pytest.raises(AccessDeniedError):
            client.download_bundle(ordinary)
        assert len(calls) == 3


@pytest.mark.parametrize(
    "change",
    [
        lambda body: body["bundles"][0].update(docId=0),
        lambda body: body["bundles"][0].update(docId=-(2**63) - 1),
        lambda body: body["bundles"][0]["_links"]["endpoint"].update(
            href="https://api.ercot.com/api/public-reports/archive/np4-190-cd?download=-1257192853"
        ),
    ],
)
def test_bundle_contract_drift(change):
    client, _ = bundle_client(change)
    with client:
        client.products()
        with pytest.raises(SchemaMismatchError):
            client.bundles("np4-190-cd")
