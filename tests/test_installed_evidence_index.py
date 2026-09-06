"""Keep live receipt accounting separate from generated and complete-query claims."""

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from tinyercot.public._schemas import ENDPOINTS
from tools import index_public_evidence

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
        index["generated_unique_paths"] == index["attempted_unique_paths"] == len(paths)
    )
    assert not index["pending_generated_paths"]
    counts = {"current": 0, "historical": 0}
    typed = {"current": set(), "historical": set()}
    failures = empties = attempts = 0
    for entry in index["paths"]:
        assert "site-packages" in entry["installed_module"]
        assert {record["period"] for record in entry["records"]} == set(counts)
        for record in entry["records"]:
            attempts += 1
            if record["status"] == "failed":
                failures += 1
                assert set(record) == {"period", "status", "error_type"}
                assert record["error_type"] in index_public_evidence.ERROR_TYPES
                continue
            counts[record["period"]] += 1
            receipt = record["receipt"]
            if record["status"] == "typed":
                assert record["rows"] >= 1
                typed[record["period"]].add(entry["path"])
            else:
                assert record["status"] == "empty" and record["rows"] == 0
                empties += 1
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
    assert index["attempted_operations"] == attempts
    assert index["successful_response_receipts"] == sum(counts.values())
    assert index["failed_operations"] == failures
    assert index["empty_operations"] == empties
    assert index["installed_unique_paths"] == len(
        typed["current"] | typed["historical"]
    )
    assert index["current_unique_paths"] == len(typed["current"])
    assert index["oldest_first_unique_paths"] == len(typed["historical"])
    both = typed["current"] & typed["historical"]
    assert index["both_period_typed_unique_paths"] == len(both)
    assert index["pending_generated_both_period_paths"] == sorted(paths - both)


@pytest.fixture
def synthetic_builder(tmp_path, monkeypatch):
    """Provide a complete tiny registry with no live observations or network."""
    monkeypatch.setattr(index_public_evidence, "ROOT", tmp_path)
    inputs = tmp_path / "tools/inputs/current"
    evidence = tmp_path / "docs/evidence"
    registry = tmp_path / "registry"
    for directory in (inputs, evidence, registry):
        directory.mkdir(parents=True)
    entries = []
    for name in ("both", "partial", "empty", "failed", "pending"):
        contract = {
            "path": "/sample/" + name,
            "fields": [{"name": "day", "dataType": "DATE", "sortable": True}],
            "query_parameters": [{"name": name} for name in ("sort", "dir")],
        }
        (inputs / (name + ".json")).write_text(json.dumps(contract))
        entries.append({"input": name + ".json"})
    (inputs / "provenance.json").write_text(json.dumps({"contracts": entries}))
    for name in ("installed-receipts.json", "installed-reports-receipts.json"):
        (evidence / name).write_text(json.dumps({"receipts": []}))

    def write(name, statuses):
        records = []
        for period, status in zip(("latest", "oldest"), statuses, strict=True):
            record = {"period": period, "status": status}
            if status == "failed":
                record["error_type"] = "SourceUnavailableError"
            else:
                direction = "desc" if period == "latest" else "asc"
                record.update(
                    {
                        "rows": int(status == "typed"),
                        "sort": "day",
                        "receipt": {
                            "source_url": f"https://api.ercot.com/api/public-reports/sample/{name}?sort=day&dir={direction}",
                            "retrieved_at": "2026-09-06T00:00:00+00:00",
                            "sha256": "a" * 64,
                            "byte_count": 100,
                            "status": 200,
                        },
                    }
                )
            records.append(record)
        file = registry / (name + ".json")
        file.write_text(
            json.dumps(
                {
                    "path": "/sample/" + name,
                    "installed_module": "/tmp/venv/lib/site-packages/tinyercot/__init__.py",
                    "records": records,
                }
            )
        )
        return file

    return registry, write


def test_failed_and_empty_operations_cannot_inflate_typed_coverage(synthetic_builder):
    registry, write = synthetic_builder
    write("both", ("typed", "typed"))
    write("partial", ("typed", "failed"))
    write("empty", ("empty", "empty"))
    write("failed", ("failed", "failed"))
    index = index_public_evidence.build_index(registry)
    assert index["generated_unique_paths"] == 5
    assert index["attempted_unique_paths"] == 4
    assert index["attempted_operations"] == 8
    assert index["installed_unique_paths"] == index["current_unique_paths"] == 2
    assert (
        index["both_period_typed_unique_paths"]
        == index["oldest_first_unique_paths"]
        == 1
    )
    assert index["failed_operations"] == 3
    assert index["empty_operations"] == 2
    assert index["successful_response_receipts"] == 5
    assert index["current_requests"] == 3
    assert index["oldest_first_requests"] == 2
    assert index["pending_generated_paths"] == ["/sample/pending"]
    assert index["pending_generated_both_period_paths"] == [
        "/sample/empty",
        "/sample/failed",
        "/sample/partial",
        "/sample/pending",
    ]
    assert [entry["path"] for entry in index["paths"]] == [
        "/sample/both",
        "/sample/empty",
        "/sample/failed",
        "/sample/partial",
    ]


@pytest.mark.parametrize(
    "change",
    [
        "secret-error",
        "message",
        "failed-receipt",
        "wrong-host",
        "fragment",
        "unknown-query",
        "duplicate-query",
        "wrong-sort",
        "wrong-direction",
        "bad-hash",
        "bool-size",
        "naive-time",
        "empty-rows",
        "unknown-period",
    ],
)
def test_builder_rejects_unsafe_or_misleading_evidence(synthetic_builder, change):
    registry, write = synthetic_builder
    file = write("partial", ("typed", "failed"))
    source = json.loads(file.read_text())
    typed, failed = source["records"]
    receipt = typed["receipt"]
    if change == "secret-error":
        failed["error_type"] = "Request failed with credential material"
    elif change == "message":
        failed["message"] = "Never retain request objects or bodies"
    elif change == "failed-receipt":
        failed["receipt"] = receipt
    elif change == "wrong-host":
        receipt["source_url"] = receipt["source_url"].replace(
            "api.ercot.com", "example.org"
        )
    elif change == "fragment":
        receipt["source_url"] += "#secret"
    elif change == "unknown-query":
        receipt["source_url"] += "&token=secret"
    elif change == "duplicate-query":
        receipt["source_url"] += "&sort=day"
    elif change == "wrong-sort":
        typed["sort"] = "unverified"
    elif change == "wrong-direction":
        typed["period"] = "oldest"
    elif change == "bad-hash":
        receipt["sha256"] = "z" * 64
    elif change == "bool-size":
        receipt["byte_count"] = True
    elif change == "naive-time":
        receipt["retrieved_at"] = "2026-09-06T00:00:00"
    elif change == "empty-rows":
        typed["status"] = "empty"
    else:
        failed["period"] = "unknown"
    file.write_text(json.dumps(source))
    with pytest.raises(ValueError):
        index_public_evidence.build_index(registry)


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
    for category, expected in (
        ("token_reacquisition", 1),
        ("complete_selection", 2),
        ("dam_pagination_current_overlap", 2),
    ):
        other = index["other_evidence"][category]
        assert (
            other["successful_response_receipts"]
            == len(other["evidence_refs"])
            == expected
        )
        assert other["overlaps_designated_current"] == (
            category == "dam_pagination_current_overlap"
        )
        for reference in other["evidence_refs"]:
            filename, pointer = reference.split("#")
            source = json.loads((ROOT / filename).read_text())
            receipt = source["receipts"][int(pointer.rsplit("/", 1)[1])]
            assert receipt["status"] == 200 and receipt["rows"] > 0


def test_other_receipts_are_validated_but_do_not_inflate_designated_counts(
    synthetic_builder,
):
    registry, write = synthetic_builder
    file = write("both", ("typed", "typed"))
    record = json.loads(file.read_text())["records"][0]
    receipts = []
    for kind in (
        "typed-api-after-token-reacquisition",
        "typed-reports-complete-selection",
        "typed-reports-complete-selection",
    ):
        receipts.append({**record["receipt"], "kind": kind, "rows": 1})
    target = index_public_evidence.ROOT / "docs/evidence/installed-receipts.json"
    target.write_text(json.dumps({"receipts": receipts}))
    index = index_public_evidence.build_index(registry)
    assert index["successful_response_receipts"] == index["attempted_operations"] == 2
    assert index["current_requests"] == index["oldest_first_requests"] == 1
    assert (
        index["other_evidence"]["token_reacquisition"]["successful_response_receipts"]
        == 1
    )
    assert (
        index["other_evidence"]["complete_selection"]["successful_response_receipts"]
        == 2
    )
    receipts[0]["source_url"] += "&token=secret"
    target.write_text(json.dumps({"receipts": receipts}))
    with pytest.raises(ValueError):
        index_public_evidence.build_index(registry)
