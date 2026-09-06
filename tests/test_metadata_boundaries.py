"""Adversarial metadata must not authorize restricted or unknown retrieval."""

import hashlib
import json

import httpx
import pytest

from tinyercot.catalog import Access
from tinyercot.public import Credentials, StreamingLimits
from tinyercot.public._http import AccessDeniedError, SchemaMismatchError
from tinyercot.public.api import BASE
from tinyercot.public.api_archives import APIArchiveClient
from tinyercot.public.metadata import decode_product
from tools import discover_public, generate_public, register_public_batch


def product(**changes):
    result = {
        "emilId": "NP4-190-CD",
        "name": "Synthetic public product",
        "status": "Active",
        "contentType": "DATA",
        "securityClassification": "Public",
        "audience": "Public",
        "artifacts": [
            {
                "reportTypeId": 12345,
                "displayName": "Synthetic artifact",
                "_links": {
                    "endpoint": {"href": BASE + "/np4-190-cd/dam_stlmnt_pnt_prices"}
                },
            }
        ],
    }
    result.update(changes)
    return result


@pytest.mark.parametrize(
    "security,audience,expected",
    [
        ("Public", "Public", Access.PUBLIC),
        ("Public", "Certified", Access.RESTRICTED),
        ("Public", "Secure", Access.RESTRICTED),
        ("Public", None, Access.UNKNOWN),
        ("Public", "new-audience", Access.UNKNOWN),
        ("Secure", "Public", Access.RESTRICTED),
        ("Certified", "Public", Access.RESTRICTED),
        (None, "Public", Access.UNKNOWN),
    ],
)
def test_access_requires_consistent_explicit_public_evidence(
    security, audience, expected
):
    assert (
        decode_product(
            product(securityClassification=security, audience=audience)
        ).access
        is expected
    )


def test_missing_audience_is_not_public():
    body = product()
    body.pop("audience")
    assert decode_product(body).access is Access.UNKNOWN


@pytest.mark.parametrize("audience", [True, 1, [], {}])
def test_unknown_audience_types_fail_closed(audience):
    with pytest.raises(SchemaMismatchError):
        decode_product(product(audience=audience))


@pytest.mark.parametrize(
    "url",
    [
        "http://api.ercot.com/api/public-reports/np4-190-cd/dam_stlmnt_pnt_prices",
        "https://evil.example/api/public-reports/np4-190-cd/dam_stlmnt_pnt_prices",
        "https://api.ercot.com@evil.example/api/public-reports/np4-190-cd/dam_stlmnt_pnt_prices",
        BASE + "/np4-190-cd/dam_stlmnt_pnt_prices?private=1",
        BASE + "/np4-190-cd/dam_stlmnt_pnt_prices#token",
        BASE + "/np4-190-cd/../participant-only",
        BASE + "/np4-190-cd/%2e%2e/participant-only",
        BASE + "/np4-188-cd/dam_clear_price_for_cap",
    ],
)
def test_malicious_or_cross_product_artifact_links_fail_closed(url):
    body = product()
    body["artifacts"][0]["_links"]["endpoint"]["href"] = url
    with pytest.raises(SchemaMismatchError):
        decode_product(body)


@pytest.mark.parametrize("audience", ["Certified", "Secure", "new-audience", None])
def test_nonpublic_audience_cannot_authorize_archive_request(audience):
    requests = []

    def transport(request):
        requests.append(str(request.url))
        if request.method == "POST":
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        if str(request.url) == BASE + "/":
            return httpx.Response(
                200, json={"_embedded": {"products": [product(audience=audience)]}}
            )
        pytest.fail("Nonpublic metadata authorized an archive request")

    with APIArchiveClient(
        Credentials("test", "test", "test"),
        limits=StreamingLimits(min_interval=0),
        transport=httpx.MockTransport(transport),
    ) as client:
        client.products()
        with pytest.raises(AccessDeniedError):
            client.archives("np4-190-cd")
    assert len(requests) == 2


def write_root(directory, products, **receipt_changes):
    raw = json.dumps({"_embedded": {"products": products}}).encode()
    (directory / "root.json").write_bytes(raw)
    receipt = {
        "source_url": BASE + "/",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_count": len(raw),
        "status": 200,
        "retrieved_at": "2026-09-06T00:00:00+00:00",
    }
    receipt.update(receipt_changes)
    (directory / "root-receipt.json").write_text(json.dumps(receipt))


def test_batch_root_receipts_reject_headers_before_preserving_provenance(tmp_path):
    write_root(tmp_path, [], headers={"Authorization": "synthetic-must-not-be-copied"})
    with pytest.raises(ValueError):
        register_public_batch.project_batch(tmp_path, tmp_path / "unused.json")


@pytest.mark.parametrize(
    "changes",
    [{"status": "Inactive"}, {"status": "Retired"}, {"contentType": "BINARY"}],
)
def test_batch_does_not_project_inactive_or_binary_rows(tmp_path, monkeypatch, changes):
    write_root(tmp_path, [product(**changes)])
    source = tmp_path / "np4-190-cd--dam_stlmnt_pnt_prices--current.json"
    source.write_text("{}")

    def unexpected_discovery(**kwargs):
        pytest.fail("Inactive or binary product reached row schema discovery")

    monkeypatch.setattr(register_public_batch, "discover", unexpected_discovery)
    contracts, _ = register_public_batch.project_batch(
        tmp_path, tmp_path / "unused.json"
    )
    assert contracts == []


@pytest.fixture
def schema_evidence(tmp_path, monkeypatch):
    path = "/np4-190-cd/dam_stlmnt_pnt_prices"
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"paths": {path: {"get": {"parameters": []}}}}))
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "sources": {
                    "public-reports": {
                        "sha256": hashlib.sha256(spec.read_bytes()).hexdigest()
                    }
                },
                "operations": [
                    {"service": "public-reports", "kind": "data", "path": path}
                ],
            }
        )
    )
    monkeypatch.setattr(discover_public, "CATALOG", catalog)
    return {
        "spec": spec,
        "response": tmp_path / "row.json",
        "receipt": tmp_path / "receipt.json",
        "path": path,
    }


def write_response(evidence, *, kind="INTEGER", value=None, suffix=""):
    raw = json.dumps(
        {"fields": [{"name": "observedField", "dataType": kind}], "data": [[value]]}
    ).encode()
    evidence["response"].write_bytes(raw)
    evidence["receipt"].write_text(
        json.dumps(
            {
                "source_url": BASE + evidence["path"] + suffix,
                "retrieved_at": "2026-09-06T00:00:00+00:00",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "byte_count": len(raw),
                "status": 200,
            }
        )
    )


def test_null_observation_is_opt_in_and_does_not_create_installed_proof(
    schema_evidence,
):
    write_response(schema_evidence)
    assert discover_public.discover(**schema_evidence)["row_schema"] == "unknown"
    projected = discover_public.discover(**schema_evidence, allow_observed_nulls=True)
    assert projected["row_schema"] == "verified_observed"
    assert projected["observed_nullable_fields"] == ["observedField"]
    assert "installed" not in projected


@pytest.mark.parametrize(
    "kind,value",
    [("UUID", None), ("STRUCT", {}), ("INTEGER", True), ("INTEGER", "123")],
)
def test_opt_in_nulls_do_not_bypass_unsupported_types(schema_evidence, kind, value):
    write_response(schema_evidence, kind=kind, value=value)
    assert (
        discover_public.discover(**schema_evidence, allow_observed_nulls=True)[
            "row_schema"
        ]
        == "unknown"
    )


@pytest.mark.parametrize("suffix", ["#token=synthetic", "?Authorization="])
def test_observation_receipt_rejects_nonquery_fragments_and_blank_unknown_keys(
    schema_evidence, suffix
):
    write_response(schema_evidence, value=123, suffix=suffix)
    with pytest.raises(ValueError):
        discover_public.discover(**schema_evidence)


@pytest.mark.parametrize(
    "changes",
    [
        {"audience": "Certified"},
        {"securityClassification": "Secure"},
        {"status": "Retired"},
        {"contentType": "BINARY"},
    ],
)
def test_generator_rejects_pinned_but_ineligible_product_evidence(
    tmp_path, monkeypatch, changes
):
    manifest = json.loads(generate_public.MANIFEST.read_text())
    entry, pin = next(
        (
            entry,
            json.loads((generate_public.MANIFEST.parent / entry["input"]).read_text()),
        )
        for entry in manifest["contracts"]
        if "product_evidence"
        in json.loads((generate_public.MANIFEST.parent / entry["input"]).read_text())
    )
    pin["product_evidence"].update(changes)
    raw = json.dumps(pin).encode()
    (tmp_path / entry["input"]).write_bytes(raw)
    manifest_path = tmp_path / "provenance.json"
    manifest_path.write_text(
        json.dumps(
            {
                "inputs": {entry["input"]: hashlib.sha256(raw).hexdigest()},
                "contracts": [entry],
            }
        )
    )
    monkeypatch.setattr(generate_public, "MANIFEST", manifest_path)
    with pytest.raises(ValueError):
        generate_public.contracts()
