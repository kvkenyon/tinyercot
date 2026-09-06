"""Build an offline installed-retrieval index from allowlisted public receipts."""

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_KEYS = {"source_url", "retrieved_at", "sha256", "byte_count", "status"}
ERROR_TYPES = {
    "AccessDeniedError",
    "AuthenticationError",
    "LimitError",
    "PublicDataError",
    "RateLimitError",
    "SchemaMismatchError",
    "SourceUnavailableError",
    "ValueError",
    "TypeError",
    "RuntimeError",
    "TimeoutError",
}


def validate_record(record: dict, path: str, contract: dict) -> None:
    """Validate redacted operation evidence without inferring HTTP attempt counts.

    Args:
        record: One typed, empty, or failed installed-client operation.
        path: Generated public operation identity.
        contract: Pinned row and query metadata for this operation.

    Raises:
        ValueError: Metadata, receipt identity, or source sorting is unsupported.
    """
    if record.get("period") not in {"current", "historical"}:
        raise ValueError("Unknown observation period")
    if record.get("status") == "failed":
        if (
            set(record) != {"period", "status", "error_type"}
            or record["error_type"] not in ERROR_TYPES
        ):
            raise ValueError("Failed operation must contain only a safe error type")
        return
    if set(record) - {
        "period",
        "status",
        "rows",
        "sort",
        "source_time",
        "receipt",
        "evidence_ref",
    }:
        raise ValueError("Unexpected observation metadata")
    if (
        record.get("status") not in {"typed", "empty"}
        or type(record.get("rows")) is not int
        or record["rows"] < 0
        or (record["status"] == "typed") != (record["rows"] > 0)
        or record.get("source_time") is not None
        and not isinstance(record["source_time"], str)
    ):
        raise ValueError("Observation status differs from its row count")
    receipt = record.get("receipt", {})
    if (
        set(receipt) != RECEIPT_KEYS
        or type(receipt["status"]) is not int
        or receipt["status"] != 200
        or type(receipt["byte_count"]) is not int
        or receipt["byte_count"] < 1
        or not isinstance(receipt["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"]) is None
    ):
        raise ValueError("Observation lacks a successful response receipt")
    try:
        retrieved = datetime.datetime.fromisoformat(receipt["retrieved_at"])
        url = urlsplit(receipt["source_url"])
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid public receipt timestamp or URL") from error
    queries = parse_qs(url.query, keep_blank_values=True)
    allowed = {parameter["name"] for parameter in contract["query_parameters"]}
    sort = record.get("sort")
    sortable = {field["name"] for field in contract["fields"] if field.get("sortable")}
    if (
        retrieved.tzinfo is None
        or url.scheme != "https"
        or url.netloc != "api.ercot.com"
        or url.path != "/api/public-reports" + path
        or url.fragment
        or set(queries) - allowed
        or any(len(values) != 1 for values in queries.values())
        or (sort is not None and sort not in sortable)
        or queries.get("sort") != ([sort] if sort is not None else None)
        or queries.get("dir") not in (["asc"], ["desc"])
    ):
        raise ValueError("Response receipt differs from the public query identity")
    if record["period"] == "historical" and (not sort or queries.get("dir") != ["asc"]):
        raise ValueError("Historical claim lacks explicit ascending source sort")


def build_index(directory: Path) -> dict:
    """Reconcile saved installed observations with the pinned generated registry.

    Args:
        directory: Directory of receipt-only registry probe JSON records.

    Returns:
        Separate generated, attempted, typed and both-period path counts. Failed
        operations lack receipts and never imply an HTTP request count.

    Raises:
        ValueError: Receipts lack public provenance or duplicate a path identity.
    """
    manifest_path = ROOT / "tools/inputs/current/provenance.json"
    manifest = json.loads(manifest_path.read_text())
    contracts = {}
    for entry in manifest["contracts"]:
        contract = json.loads((manifest_path.parent / entry["input"]).read_text())
        contracts[contract["path"]] = contract
    generated = set(contracts)
    paths = {}
    other_refs = {
        "token_reacquisition": [],
        "complete_selection": [],
        "dam_pagination_current_overlap": [],
    }
    for name in ("installed-receipts.json", "installed-reports-receipts.json"):
        source = json.loads((ROOT / "docs/evidence" / name).read_text())
        for position, record in enumerate(source["receipts"]):
            url = urlsplit(record["source_url"])
            path = url.path.removeprefix("/api/public-reports")
            if path not in generated:
                continue
            kind = record["kind"]
            evidence_ref = f"docs/evidence/{name}#/receipts/{position}"
            category = {
                "typed-api-after-token-reacquisition": "token_reacquisition",
                "typed-reports-complete-selection": "complete_selection",
            }.get(kind)
            if category:
                validate_record(
                    {
                        "period": "current",
                        "status": "typed",
                        "rows": record["rows"],
                        "sort": parse_qs(url.query).get("sort", [None])[0],
                        "receipt": {key: record[key] for key in RECEIPT_KEYS},
                    },
                    path,
                    contracts[path],
                )
                other_refs[category].append(evidence_ref)
            if (
                kind == "typed-api-current"
                and path == "/np4-190-cd/dam_stlmnt_pnt_prices"
            ):
                other_refs["dam_pagination_current_overlap"].append(evidence_ref)
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
                "evidence_ref": evidence_ref,
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
                "error_type",
            }:
                raise ValueError("Unexpected observation metadata")
            if record["period"] == "latest":
                record["period"] = "current"
            elif record["period"] == "oldest":
                record["period"] = "historical"
        paths[path] = source
    for path, source in paths.items():
        if (
            not isinstance(source["installed_module"], str)
            or "site-packages/tinyercot/__init__.py" not in source["installed_module"]
            or not source["records"]
        ):
            raise ValueError("Observation lacks an installed module or operations")
        for record in source["records"]:
            validate_record(record, path, contracts[path])
    records = [record for source in paths.values() for record in source["records"]]
    typed_periods = {
        path: {r["period"] for r in source["records"] if r["status"] == "typed"}
        for path, source in paths.items()
    }
    both_periods = {
        path
        for path, periods in typed_periods.items()
        if periods == {"current", "historical"}
    }
    successful = [record for record in records if record["status"] != "failed"]
    return {
        "format_version": 2,
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "generated_unique_paths": len(generated),
        "attempted_unique_paths": len(paths),
        "attempted_operations": len(records),
        "installed_unique_paths": sum(
            bool(periods) for periods in typed_periods.values()
        ),
        "both_period_typed_unique_paths": len(both_periods),
        "successful_response_receipts": len(successful),
        "failed_operations": sum(r["status"] == "failed" for r in records),
        "empty_operations": sum(r["status"] == "empty" for r in records),
        "current_unique_paths": sum(
            "current" in periods for periods in typed_periods.values()
        ),
        "current_requests": sum(r["period"] == "current" for r in successful),
        "oldest_first_unique_paths": sum(
            "historical" in periods for periods in typed_periods.values()
        ),
        "oldest_first_requests": sum(r["period"] == "historical" for r in successful),
        "observed_public_data_paths": 243,
        "pending_generated_paths": sorted(generated - paths.keys()),
        "pending_generated_both_period_paths": sorted(generated - both_periods),
        "count_basis": "Path/operation and current/oldest counts use designated current and historical selections only. The prior 56-path baseline has 57 current and 56 historical receipts. Token-reacquisition and complete-selection receipts are separately referenced below; DAM pagination overlaps designated current selections. These counts do not represent all HTTP requests.",
        "other_evidence": {
            category: {
                "successful_response_receipts": len(refs),
                "evidence_refs": refs,
                "overlaps_designated_current": category
                == "dam_pagination_current_overlap",
            }
            for category, refs in other_refs.items()
        },
        "request_count_policy": "The current_requests and oldest_first_requests fields count saved successful response receipts, including empty responses. Failed operations have no HTTP attempt count. Authentication and retry totals are not retained.",
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
        "limits": "Registry batches select one row per newest/oldest source direction. Oldest is scoped to source retention and optional filters, not all historical availability. No cross-epoch schema or full-history completeness claim.",
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
