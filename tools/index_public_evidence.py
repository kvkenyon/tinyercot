"""Build an offline installed-retrieval index from allowlisted public receipts."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_KEYS = {"source_url", "retrieved_at", "sha256", "byte_count", "status"}


def build_index(directory: Path) -> dict:
    """Reconcile saved installed observations with the pinned generated registry.

    Args:
        directory: Directory of receipt-only registry probe JSON records.

    Returns:
        Exact unique path counts, source receipts and separate pagination limits.

    Raises:
        ValueError: Receipts lack public provenance or duplicate a path identity.
    """
    manifest_path = ROOT / "tools/inputs/current/provenance.json"
    manifest = json.loads(manifest_path.read_text())
    generated = {
        json.loads((manifest_path.parent / entry["input"]).read_text())["path"]
        for entry in manifest["contracts"]
    }
    paths = {}
    for name in ("installed-receipts.json", "installed-reports-receipts.json"):
        source = json.loads((ROOT / "docs/evidence" / name).read_text())
        for position, record in enumerate(source["receipts"]):
            url = urlsplit(record["source_url"])
            path = url.path.removeprefix("/api/public-reports")
            if path not in generated:
                continue
            kind = record["kind"]
            period = (
                "current"
                if kind.endswith("current")
                else "historical"
                if kind.endswith("historical")
                else None
            )
            if period is None:
                continue
            observation = {
                "period": period,
                "status": "typed",
                "rows": record["rows"],
                "sort": parse_qs(url.query).get("sort", [None])[0],
                "receipt": {key: record[key] for key in RECEIPT_KEYS},
                "evidence_ref": f"docs/evidence/{name}#/receipts/{position}",
            }
            paths.setdefault(
                path,
                {
                    "path": path,
                    "installed_module": source["installed_module"],
                    "records": [],
                },
            )["records"].append(observation)
    for file in sorted(directory.glob("*.json")):
        source = json.loads(file.read_text())
        if set(source) != {"path", "installed_module", "records"}:
            raise ValueError("Unexpected installed evidence fields")
        path = source["path"]
        if path in paths or path not in generated:
            raise ValueError("Duplicate or unregistered installed evidence")
        for record in source["records"]:
            if set(record) - {
                "period",
                "status",
                "rows",
                "sort",
                "source_time",
                "receipt",
            }:
                raise ValueError("Unexpected observation metadata")
            if record["period"] == "latest":
                record["period"] = "current"
            elif record["period"] == "oldest":
                record["period"] = "historical"
        paths[path] = source
    for path, source in paths.items():
        for record in source["records"]:
            receipt = record["receipt"]
            url = urlsplit(receipt["source_url"])
            if (
                set(receipt) != RECEIPT_KEYS
                or receipt["status"] != 200
                or url.scheme != "https"
                or url.netloc != "api.ercot.com"
                or url.path != "/api/public-reports" + path
                or url.fragment
                or record["status"] != "typed"
                or record["rows"] < 1
            ):
                raise ValueError("Observation lacks successful public typed evidence")
            if record["period"] == "historical" and (
                not record["sort"] or parse_qs(url.query).get("dir") != ["asc"]
            ):
                raise ValueError(
                    "Historical claim lacks explicit ascending source sort"
                )
    records = [record for source in paths.values() for record in source["records"]]
    return {
        "format_version": 1,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "generated_unique_paths": len(generated),
        "installed_unique_paths": len(paths),
        "current_unique_paths": sum(
            any(r["period"] == "current" for r in source["records"])
            for source in paths.values()
        ),
        "current_requests": sum(r["period"] == "current" for r in records),
        "oldest_first_unique_paths": sum(
            any(r["period"] == "historical" for r in source["records"])
            for source in paths.values()
        ),
        "oldest_first_requests": sum(r["period"] == "historical" for r in records),
        "observed_public_data_paths": 243,
        "pending_generated_paths": sorted(generated - paths.keys()),
        "pagination": {
            "live_paginated_unique_paths": 2,
            "live_complete_selection_unique_paths": 1,
            "partial_selection": {
                "path": "/np4-190-cd/dam_stlmnt_pnt_prices",
                "pages": [1, 2],
                "total_pages": 12,
                "evidence": "docs/evidence/installed-receipts.json",
            },
            "complete_selection": {
                "path": "/np6-905-cd/spp_node_zone_hub",
                "pages": [1, 2],
                "total_records": 2,
                "evidence": "docs/evidence/installed-reports-receipts.json",
            },
            "new_batch_pagination_requests": 0,
            "complete_history_extraction": False,
            "annual_complete_iteration": "Offline synthetic multi-worksheet proof only; live source files sampled from verified cache.",
        },
        "limits": "One-row newest/oldest source-directed selections for the 52-path batch. Oldest is scoped to source retention and optional filters, not all historical availability. No cross-epoch schema or full-history completeness claim.",
        "authenticated_public_requests": True,
        "restricted_requests": False,
        "historical_bulk_extraction": False,
        "paths": [paths[path] for path in sorted(paths)],
    }


def main() -> None:
    """Print a reviewable index without modifying evidence or making requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_index(args.registry), indent=2))


if __name__ == "__main__":
    main()
