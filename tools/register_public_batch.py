"""Project observed public operation batches into reviewable, pinned inputs."""

import argparse
import hashlib
import json
from pathlib import Path

from tinyercot.public.metadata import RETIRED_PRODUCTS
from tools.discover_public import discover

ROOT = Path(__file__).resolve().parents[1]


def project_batch(directory: Path, spec: Path) -> tuple[list[dict], dict]:
    """Cross-check metadata identities and both bounded observation periods.

    Args:
        directory: Public metadata, response and receipt capture directory.
        spec: Exact pinned primary current OpenAPI export.

    Returns:
        Verified contract projections and explicit observation status records.

    Raises:
        ValueError: Root bytes or source identities lack matching provenance.
    """
    raw = (directory / "root.json").read_bytes()
    receipt = json.loads((directory / "root-receipt.json").read_text())
    if set(receipt) - {"source_url", "retrieved_at", "sha256", "byte_count", "status"}:
        raise ValueError("Root receipt includes unsupported metadata")
    if (
        hashlib.sha256(raw).hexdigest() != receipt["sha256"]
        or len(raw) != receipt["byte_count"]
        or receipt["source_url"] != "https://api.ercot.com/api/public-reports/"
        or receipt["status"] != 200
    ):
        raise ValueError("Root product metadata lacks matching public provenance")
    products = json.loads(raw)["_embedded"]["products"]
    verified = []
    states = {"root_receipt": receipt, "products": len(products), "operations": {}}
    for product in products:
        for artifact in product["artifacts"]:
            url = artifact.get("_links", {}).get("endpoint", {}).get("href", "")
            path = url.removeprefix("https://api.ercot.com/api/public-reports")
            if not path.startswith("/" + product["emilId"].lower() + "/"):
                raise ValueError("Artifact does not belong to its source product")
            state = {"product": product["emilId"], "status": "pending", "periods": {}}
            states["operations"][path] = state
            if (
                product["emilId"].upper() in RETIRED_PRODUCTS
                or product["status"] != "Active"
            ):
                state["status"] = "retired-or-inactive"
                continue
            if (
                product["audience"] != "Public"
                or product["securityClassification"] != "Public"
            ):
                state["status"] = "restricted-or-unknown"
                continue
            if product["contentType"] != "DATA":
                state["status"] = "binary-row-schema-unsupported"
                continue
            projections = []
            for period in ("current", "historical"):
                source = directory / (
                    path.strip("/").replace("/", "--") + "--" + period + ".json"
                )
                if not source.exists():
                    state["periods"][period] = "not-observed"
                    continue
                try:
                    projection = discover(
                        spec=spec,
                        response=source,
                        receipt=source.with_name(source.stem + "-receipt.json"),
                        path=path,
                        allow_observed_nulls=True,
                    )
                    state["periods"][period] = projection["row_schema"]
                    if projection.get("schema_issues"):
                        state.setdefault("schema_issues", {})[period] = projection[
                            "schema_issues"
                        ]
                    if projection["row_schema"] == "verified_observed":
                        projections.append(projection)
                except (KeyError, TypeError, ValueError) as error:
                    state["periods"][period] = "ambiguous: " + str(error)
            if not projections:
                state["status"] = (
                    "pending"
                    if all(
                        value == "not-observed" for value in state["periods"].values()
                    )
                    else "schema-unverified"
                )
                continue
            current = projections[0]
            field_types = {f["name"]: f["dataType"] for f in current["fields"]}
            if any(
                {f["name"]: f["dataType"] for f in p["fields"]} != field_types
                for p in projections
            ):
                state["status"] = "ambiguous-schema-epochs"
                continue
            current["observed_nullable_fields"] = sorted(
                {name for p in projections for name in p["observed_nullable_fields"]}
            )
            current["nullability_policy"] = (
                "Accept null only for fields observed null in pinned samples; field presence stays required. Unobserved nullability remains unknown."
            )
            current["observations"] = [p["response_source"] for p in projections]
            current["product_evidence"] = {
                "emilId": product["emilId"],
                "status": product["status"],
                "audience": product["audience"],
                "securityClassification": product["securityClassification"],
                "contentType": product["contentType"],
                "artifactReportTypeId": artifact["reportTypeId"],
                "root_sha256": receipt["sha256"],
            }
            state["status"] = "schema-verified-awaiting-installed-retrieval"
            verified.append(current)
    return verified, states


def main() -> None:
    """Write deterministic evidence projections; never fetch or edit legacy code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contracts, states = project_batch(args.evidence, args.spec)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "tools/inputs/current/provenance.json"
    manifest = json.loads(manifest_path.read_text())
    existing = {
        json.loads((manifest_path.parent / entry["input"]).read_text())["path"]
        for entry in manifest["contracts"]
    }
    additions = []
    for contract in sorted(contracts, key=lambda c: c["path"]):
        if contract["path"] in existing:
            continue
        product, method = contract["path"].strip("/").split("/")
        filename = product + "--" + method + ".json"
        model = "".join(
            part[:1].upper() + part[1:]
            for part in (product + "_" + method).replace("-", "_").split("_")
        )
        constant = (product + "_" + method).replace("-", "_").upper()
        raw = (json.dumps(contract, indent=2) + "\n").encode()
        (args.output / filename).write_bytes(raw)
        additions.append(
            {
                "input": filename,
                "model": model,
                "constant": constant,
                "fields_constant": constant + "_FIELDS",
            }
        )
        manifest["inputs"][filename] = hashlib.sha256(raw).hexdigest()
    manifest["contracts"].extend(additions)
    (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output / "discovery-status.json").write_text(
        json.dumps(states, indent=2) + "\n"
    )
    print(
        f"Projected {len(additions)} new contracts; {len(states['operations'])} artifact paths classified"
    )


if __name__ == "__main__":
    main()
