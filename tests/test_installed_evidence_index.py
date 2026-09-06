"""Keep live receipt accounting separate from generated and complete-query claims."""

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from tinyercot.public._schemas import ENDPOINTS

ROOT = Path(__file__).resolve().parents[1]


def test_installed_index_binds_generated_paths_and_both_source_directions():
    index = json.loads(
        (ROOT / "docs/evidence/installed-registry-index.json").read_text()
    )
    manifest = ROOT / "tools/inputs/current/provenance.json"
    assert index["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    paths = {entry["path"] for entry in index["paths"]}
    assert paths == {endpoint.path for endpoint in ENDPOINTS}
    assert (
        index["generated_unique_paths"] == index["installed_unique_paths"] == len(paths)
    )
    assert (
        index["current_unique_paths"]
        == index["oldest_first_unique_paths"]
        == len(paths)
    )
    assert not index["pending_generated_paths"]
    counts = {"current": 0, "historical": 0}
    for entry in index["paths"]:
        assert "site-packages" in entry["installed_module"]
        assert {record["period"] for record in entry["records"]} == set(counts)
        for record in entry["records"]:
            counts[record["period"]] += 1
            receipt = record["receipt"]
            assert record["status"] == "typed" and record["rows"] >= 1
            assert set(receipt) == {
                "source_url",
                "sha256",
                "byte_count",
                "retrieved_at",
                "status",
            }
            assert len(receipt["sha256"]) == 64 and receipt["status"] == 200
            url = urlsplit(receipt["source_url"])
            assert url.scheme == "https" and url.netloc == "api.ercot.com"
            assert url.path == "/api/public-reports" + entry["path"]
            if record["period"] == "historical":
                query = parse_qs(url.query)
                assert query["dir"] == ["asc"] and query["sort"] == [record["sort"]]
    assert counts == {
        "current": index["current_requests"],
        "historical": index["oldest_first_requests"],
    }


def test_pagination_claims_reference_actual_pages_and_matching_totals():
    index = json.loads(
        (ROOT / "docs/evidence/installed-registry-index.json").read_text()
    )
    evidence = json.loads(
        (ROOT / index["pagination"]["complete_selection"]["evidence"]).read_text()
    )
    pages = [
        r
        for r in evidence["receipts"]
        if r["kind"] == "typed-reports-complete-selection"
    ]
    assert [record["page"] for record in pages] == [1, 2]
    assert {record["total_records"] for record in pages} == {
        sum(r["rows"] for r in pages)
    }
    assert index["pagination"]["live_complete_selection_unique_paths"] == 1
    assert index["pagination"]["new_batch_pagination_requests"] == 0
    assert not index["pagination"]["complete_history_extraction"]
