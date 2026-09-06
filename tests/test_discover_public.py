"""Test offline projection and generation rejection with compact fixtures."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "discover_public", ROOT / "tools/discover_public.py"
)
assert SPEC and SPEC.loader
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    pin = json.loads((ROOT / "tools/inputs/current/rt-prices.json").read_text())
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {"paths": {pin["path"]: {"get": {"parameters": pin["query_parameters"]}}}}
        )
    )
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
                    {"service": "public-reports", "kind": "data", "path": pin["path"]}
                ],
            }
        )
    )
    monkeypatch.setattr(discovery, "CATALOG", catalog)
    response = tmp_path / "response.json"
    response.write_bytes(
        (ROOT / "tests/fixtures/public/rt-prices-current.json").read_bytes()
    )
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(pin["response_source"]))
    return {"spec": spec, "response": response, "receipt": receipt, "path": pin["path"]}


def test_projection_is_deterministic_and_checks_primary_pins(evidence):
    first = discovery.discover(**evidence)
    assert first == discovery.discover(**evidence)
    assert first["row_schema"] == "verified_observed"
    assert all(p["in"] == "query" for p in first["query_parameters"])
    evidence["spec"].write_text("{}")
    with pytest.raises(ValueError, match="primary-source"):
        discovery.discover(**evidence)


@pytest.mark.parametrize(
    "fault,status",
    [
        ("missing", "missing"),
        ("empty", "unknown"),
        ("null", "unknown"),
        ("unknown_type", "unknown"),
        ("wrong_type", "unknown"),
    ],
)
def test_missing_or_unknown_response_contract_is_explicit(evidence, fault, status):
    body = json.loads(evidence["response"].read_bytes())
    if fault == "missing":
        body.pop("fields")
    elif fault == "empty":
        body["data"] = []
    elif fault == "null":
        body["data"][0][0] = None
    elif fault == "wrong_type":
        body["data"][0][1] = "not an integer"
    else:
        body["fields"][0]["dataType"] = "UNVERIFIED"
    raw = json.dumps(body).encode()
    evidence["response"].write_bytes(raw)
    receipt = json.loads(evidence["receipt"].read_text())
    receipt.update(sha256=hashlib.sha256(raw).hexdigest(), byte_count=len(raw))
    evidence["receipt"].write_text(json.dumps(receipt))
    assert discovery.discover(**evidence)["row_schema"] == status


def test_unknown_schema_is_never_generated(monkeypatch, tmp_path):
    from tools import generate_public

    pin = json.loads(generate_public.INPUT.read_text())
    pin["row_schema"] = "unknown"
    changed = tmp_path / "dam-prices.json"
    changed.write_text(json.dumps(pin))
    manifest = json.loads(generate_public.MANIFEST.read_text())
    manifest["inputs"][changed.name] = hashlib.sha256(changed.read_bytes()).hexdigest()
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(generate_public, "INPUT", changed)
    monkeypatch.setattr(generate_public, "MANIFEST", path)
    with pytest.raises(ValueError, match="unknown"):
        generate_public.render()


@pytest.mark.parametrize(
    "fault",
    [
        "missing_status",
        "source_hash",
        "duplicate_symbol",
        "private_field",
        "unknown_format",
        "duplicate_query",
    ],
)
def test_generator_rejects_unverified_or_ambiguous_contracts(
    monkeypatch, tmp_path, fault
):
    from tools import generate_public

    manifest = json.loads(generate_public.MANIFEST.read_text())
    for name in manifest["inputs"]:
        (tmp_path / name).write_bytes(
            (generate_public.MANIFEST.parent / name).read_bytes()
        )
    path = tmp_path / "dam-prices.json"
    pin = json.loads(path.read_text())
    if fault == "missing_status":
        pin.pop("row_schema")
    elif fault == "source_hash":
        pin["query_source_sha256"] = "unverified"
    elif fault == "duplicate_symbol":
        manifest["contracts"][0]["constant"] = manifest["contracts"][0]["model"]
    elif fault == "private_field":
        pin["fields"][0]["name"] = "_hidden"
    elif fault == "unknown_format":
        pin["query_parameters"][0]["schema"]["format"] = "unknown"
    else:
        pin["query_parameters"].append(pin["query_parameters"][0])
    path.write_text(json.dumps(pin))
    manifest["inputs"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path = tmp_path / "provenance.json"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(generate_public, "INPUT", path)
    monkeypatch.setattr(
        generate_public, "CAPACITY_INPUT", tmp_path / "dam-capacity.json"
    )
    monkeypatch.setattr(generate_public, "MANIFEST", manifest_path)
    with pytest.raises(ValueError):
        generate_public.render_registry()


def test_registered_models_and_filter_generation_are_deterministic():
    from tools import generate_public

    assert generate_public.render() == generate_public.OUTPUT.read_text()
    assert (
        generate_public.render_registry() == generate_public.REGISTRY_OUTPUT.read_text()
    )
