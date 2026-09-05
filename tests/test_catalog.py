import dataclasses
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from tinyercot.catalog import Access, classify_access, operations, sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "label, expected",
    [
        ("Public", Access.PUBLIC),
        (" public ", Access.PUBLIC),
        ("Secure", Access.RESTRICTED),
        ("Certified", Access.RESTRICTED),
        (None, Access.UNKNOWN),
        ("", Access.UNKNOWN),
        ("Active", Access.UNKNOWN),
        ("Greybox", Access.UNKNOWN),
        ("public-ish", Access.UNKNOWN),
        ("Public; Certified", Access.UNKNOWN),
    ],
)
def test_access_boundary_fails_closed(label, expected):
    assert classify_access(label) is expected


def test_catalog_inventory_distinguishes_paths_from_typed_coverage():
    inventory = operations()
    assert len(inventory) == 257
    assert len({(op.service, op.path, op.method) for op in inventory}) == 257
    assert Counter(op.service for op in inventory) == {
        "public-reports": 249,
        "public-data": 8,
    }
    data = [op for op in inventory if op.kind == "data"]
    assert len(data) == 243
    assert Counter(op.row_schema for op in data) == {
        "cached_unverified": 203,
        "missing": 40,
    }
    assert sum(op.legacy_path for op in data) == 102
    assert sum(op.query_drift == "contract" for op in data) == 39
    assert sum(op.query_drift == "order_only" for op in data) == 1
    assert all(
        op.access is Access.PUBLIC and op.support == "metadata_only" for op in inventory
    )
    assert all(op.method == "GET" for op in data)
    assert len(operations(service="public-data")) == 8
    assert operations(service="unknown") == ()
    assert all(op.observed_at == "2026-09-05" for op in inventory)
    assert all(
        op.source_url.startswith("https://apiexplorer.ercot.com/") for op in inventory
    )


def test_archive_bundle_methods_and_media_remain_distinct():
    for service in ("public-reports", "public-data"):
        generic = [op for op in operations(service=service) if op.kind == "service"]
        assert len(generic) == 7
        assert Counter(op.method for op in generic) == {"GET": 5, "POST": 2}
        downloads = [op for op in generic if op.method == "POST"]
        assert {op.path.split("/")[1] for op in downloads} == {"archive", "bundle"}
        assert all(op.request_media == ("application/json",) for op in downloads)
        assert all(op.response_media == ("application/zip",) for op in downloads)
        assert all(op.row_schema == "not_applicable" for op in generic)


def test_boundaries_are_metadata_only_and_immutable():
    boundaries = {item.source_id: item for item in sources()}
    assert {s.access for s in boundaries.values()} == set(Access)
    for name in ("secure-products", "certified-products", "ews-private-records"):
        assert boundaries[name].access is Access.RESTRICTED
        assert boundaries[name].authentication == "entitlement"
    assert boundaries["load-2001"].access is Access.UNAVAILABLE
    assert boundaries["unclassified-products"].access is Access.UNKNOWN
    assert all(item.support == "metadata_only" for item in boundaries.values())
    with pytest.raises(dataclasses.FrozenInstanceError):
        boundaries["secure-products"].access = Access.PUBLIC
    with pytest.raises(dataclasses.FrozenInstanceError):
        operations()[0].row_schema = "verified"


def test_catalog_snapshot_matches_recorded_hash():
    provenance = json.loads((ROOT / "tools/inputs/public-provenance.json").read_text())
    assert (
        hashlib.sha256((ROOT / "tinyercot/_catalog.json").read_bytes()).hexdigest()
        == provenance["catalog_sha256"]
    )


def test_catalog_import_and_use_need_no_credentials_or_network():
    script = """
import os, socket
for name in ("ERCOT_USERNAME", "ERCOT_PASSWORD", "ERCOT_SUBSCRIPTION_KEY"):
    os.environ.pop(name, None)
def denied(*args, **kwargs):
    raise AssertionError("network or credentials requested")
socket.socket.connect = denied
socket.getaddrinfo = denied
import tinyercot._client as client
client._resolve_creds = denied
client._get = denied
client._aget = denied
from tinyercot.catalog import operations, sources
assert len(operations()) == 257
assert len(sources()) == 8
assert not client._tok_cache
"""
    subprocess.run([sys.executable, "-c", script], cwd=ROOT, check=True)
