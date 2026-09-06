"""Project a current public contract from saved primary evidence, offline."""

import argparse
import datetime
import hashlib
import json
import keyword
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

SOURCE_URL = "https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview"
CATALOG = Path(__file__).resolve().parents[1] / "tinyercot/_catalog.json"
ROW_TYPES = {
    "DATE",
    "DATETIME",
    "VARCHAR",
    "DOUBLE",
    "DECIMAL",
    "FLOAT",
    "INTEGER",
    "LONG",
    "BOOLEAN",
}


def discover(
    *,
    spec: Path,
    response: Path,
    receipt: Path,
    path: str,
    allow_observed_nulls: bool = False,
) -> dict:
    """Project query and observed row metadata with exact source identities.

    Args:
        spec: Saved authoritative Public Reports OpenAPI export.
        response: Small saved public data response, including fields and rows.
        receipt: Public-only receipt for those exact response bytes.
        path: An observed public data GET path from the offline catalog.
        allow_observed_nulls: Record explicitly observed nullable fields while
            requiring their declared source types; default preserves strict pins.

    Returns:
        A compact contract with verified_observed, missing, or unknown row status.
        Empty rows and unknown field types do not establish typed coverage.
        Nulls require explicit opt-in and retain only their declared source type.

    Raises:
        ValueError: Source identity, hash, or public-operation evidence disagrees.
    """
    catalog = json.loads(CATALOG.read_text())
    spec_bytes = spec.read_bytes()
    if (
        hashlib.sha256(spec_bytes).hexdigest()
        != catalog["sources"]["public-reports"]["sha256"]
    ):
        raise ValueError("OpenAPI bytes do not match the primary-source catalog pin")
    if path not in {
        op["path"]
        for op in catalog["operations"]
        if op["service"] == "public-reports" and op["kind"] == "data"
    }:
        raise ValueError("Path is not an observed public data GET")
    raw = response.read_bytes()
    record = json.loads(receipt.read_text())
    if set(record) - {
        "source_url",
        "retrieved_at",
        "sha256",
        "byte_count",
        "bytes",
        "status",
        "query",
    }:
        raise ValueError(
            "Receipt contains unsupported metadata; headers are not accepted"
        )
    source = urlsplit(record["source_url"])
    if (
        source.scheme != "https"
        or source.fragment
        or source.netloc != "api.ercot.com"
        or source.path != "/api/public-reports" + path
        or record["status"] != 200
        or record["sha256"] != hashlib.sha256(raw).hexdigest()
        or record.get("byte_count", record.get("bytes")) != len(raw)
    ):
        raise ValueError("Response receipt does not identify the public bytes")
    specification = json.loads(spec.read_bytes())
    operation = specification["paths"][path]["get"]
    queries = [
        {"name": p["name"], "in": "query", "schema": p["schema"]}
        for p in operation["parameters"]
        if p["in"] == "query"
    ]
    query_names = {query["name"] for query in queries}
    if (
        set(parse_qs(source.query, keep_blank_values=True)) - query_names
        or set(record.get("query", {})) - query_names
    ):
        raise ValueError(
            "Receipt URL contains fields outside the public query contract"
        )
    body = json.loads(raw, parse_float=Decimal)
    fields = body.get("fields", [])
    status = "verified_observed"
    nullable = set()
    issues = []
    if not fields:
        status = "missing"
    elif not isinstance(fields, list):
        raise ValueError("Invalid response field metadata")
    else:
        names = [f["name"] for f in fields]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate response field names")
        if any(
            not name.isidentifier()
            or keyword.iskeyword(name)
            or name.startswith(("_", "model_"))
            for name in names
        ):
            raise ValueError("Response field cannot be represented safely")
        if any(f["dataType"] not in ROW_TYPES for f in fields):
            status = "unknown"
        rows = body.get("data")
        if not isinstance(rows, list) or not rows:
            status = "unknown"
        else:
            for row in rows:
                if isinstance(row, dict):
                    if set(row) != set(names):
                        raise ValueError("Response row keys differ from fields")
                    values = [row[name] for name in names]
                elif isinstance(row, list) and len(row) == len(names):
                    values = row
                else:
                    raise ValueError("Response row width differs from fields")
                if any(value is None for value in values) and not allow_observed_nulls:
                    status = "unknown"
                for descriptor, value in zip(fields, values, strict=True):
                    kind = descriptor["dataType"]
                    if value is None and allow_observed_nulls:
                        nullable.add(descriptor["name"])
                        continue
                    valid = True
                    if kind in {"DOUBLE", "FLOAT", "DECIMAL"}:
                        valid = (
                            type(value) in {int, Decimal} and Decimal(value).is_finite()
                        )
                    elif kind in {"INTEGER", "LONG"}:
                        valid = type(value) is int
                    elif kind == "BOOLEAN":
                        valid = type(value) is bool
                    elif kind in {"DATE", "DATETIME", "VARCHAR"}:
                        valid = type(value) is str
                        if valid and kind in {"DATE", "DATETIME"}:
                            try:
                                if kind == "DATE":
                                    valid = (
                                        datetime.date.fromisoformat(value).isoformat()
                                        == value
                                    )
                                else:
                                    datetime.datetime.fromisoformat(value)
                            except ValueError:
                                valid = False
                    if not valid:
                        status = "unknown"
                        issue = {
                            "field": descriptor["name"],
                            "declared_type": kind,
                            "observed_type": type(value).__name__,
                        }
                        if issue not in issues:
                            issues.append(issue)
    return {
        "format_version": 1,
        "service": "public-reports",
        "path": path,
        "observed_at": record["retrieved_at"],
        "row_schema": status,
        "query_parameters": queries,
        "fields": fields,
        "nullability_policy": (
            "Accept null only for explicitly observed nullable fields with declared source types; field presence stays required."
            if allow_observed_nulls
            else "Reject nulls; observed fields do not establish nullability."
        ),
        "source_url": SOURCE_URL,
        "query_source_sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
        "response_source": record,
        **({"schema_issues": issues} if issues else {}),
        **(
            {"observed_nullable_fields": sorted(nullable)}
            if allow_observed_nulls
            else {}
        ),
    }


def main() -> None:
    """Write a compact projection; never fetch upstream or alter legacy files."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("spec", "response", "receipt", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    contract = discover(
        spec=args.spec, response=args.response, receipt=args.receipt, path=args.path
    )
    args.output.write_text(json.dumps(contract, indent=2) + "\n")
    print(f"Projected row status: {contract['row_schema']}")


if __name__ == "__main__":
    main()
