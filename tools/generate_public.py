"""Generate current row models only from pinned observed field metadata."""

import argparse
import hashlib
import json
import keyword
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "tools/inputs/current/dam-prices.json"
CAPACITY_INPUT = ROOT / "tools/inputs/current/dam-capacity.json"
MANIFEST = ROOT / "tools/inputs/current/provenance.json"
OUTPUT = ROOT / "tinyercot/public/_generated.py"
REGISTRY_OUTPUT = ROOT / "tinyercot/public/_schemas.py"
PRODUCTS_OUTPUT = ROOT / "tinyercot/public/products.py"
BUNDLE_OUTPUT = ROOT / "tinyercot/public/_contracts.json"
TYPES = {
    "DATE": "date",
    "VARCHAR": "StrictStr",
    "DOUBLE": "Decimal",
    "BOOLEAN": "StrictBool",
    "INTEGER": "StrictInt",
    "LONG": "StrictInt",
    "DATETIME": "datetime",
    "FLOAT": "Decimal",
}


def contracts() -> list[tuple[dict, dict]]:
    """Load configured public contracts only when pins and schemas verify.

    Returns:
        Ordered generator names and their verified source projections.

    Raises:
        ValueError: A hash, public path, name, or row schema is not supported.
    """
    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads((ROOT / "tinyercot/_catalog.json").read_text())
    public_paths = {
        op["path"]
        for op in catalog["operations"]
        if op["service"] == "public-reports" and op["kind"] == "data"
    }
    result = []
    identities = set()
    symbols = {
        "Endpoint",
        "ENDPOINTS",
        "TypedDict",
        "BaseModel",
        "ConfigDict",
        "date",
        "datetime",
        "Decimal",
        "StrictBool",
        "StrictInt",
        "StrictStr",
    }
    for entry in manifest["contracts"]:
        path = (
            INPUT
            if entry["input"] == "dam-prices.json"
            else CAPACITY_INPUT
            if entry["input"] == "dam-capacity.json"
            else MANIFEST.parent / entry["input"]
        )
        if Path(entry["input"]).name != entry["input"]:
            raise ValueError("Generator input must be a local basename")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["inputs"][entry["input"]]:
            raise ValueError("Unverified current response metadata")
        contract = json.loads(raw)
        evidence = contract.get("product_evidence")
        if evidence is None and entry["input"] not in {
            "dam-prices.json",
            "dam-capacity.json",
            "rt-prices.json",
            "system-load.json",
        }:
            raise ValueError("New row contracts require public product evidence")
        if evidence is not None and (
            evidence.get("emilId", "").lower() != contract["path"].split("/")[1]
            or evidence.get("audience") != "Public"
            or evidence.get("securityClassification") != "Public"
            or evidence.get("status") != "Active"
            or evidence.get("contentType") != "DATA"
            or evidence.get("emilId", "").upper() in {"NP4-179-CD", "NP3-990-EX"}
        ):
            raise ValueError(
                "Product evidence does not permit current public row generation"
            )
        if (
            contract["service"] != "public-reports"
            or contract["path"] not in public_paths
        ):
            raise ValueError("No verified public operation for this contract")
        if contract.get("row_schema") != "verified_observed":
            raise ValueError("Missing or unknown row schemas cannot be generated")
        if (
            contract["query_source_sha256"]
            != catalog["sources"]["public-reports"]["sha256"]
        ):
            raise ValueError("Query evidence differs from the primary catalog pin")
        fields = contract["fields"]
        names = [f["name"] for f in fields]
        if not fields or len(set(names)) != len(names):
            raise ValueError("Missing or duplicate response fields")
        for name in [
            *names,
            entry["model"],
            entry["constant"],
            entry["fields_constant"],
        ]:
            if (
                not name.isidentifier()
                or keyword.iskeyword(name)
                or name.startswith(("_", "model_"))
            ):
                raise ValueError("Unsupported Python field or model name")
        if any(f["dataType"] not in TYPES for f in fields):
            raise ValueError("Unsupported response field type")
        if set(contract.get("observed_nullable_fields", [])) - set(names):
            raise ValueError("Nullable field lacks declared source metadata")
        declared = [
            entry["model"],
            entry["constant"],
            entry["fields_constant"],
            entry["model"] + "Filters",
        ]
        if len(set(declared)) != len(declared) or symbols.intersection(declared):
            raise ValueError("Colliding generated symbol")
        symbols.update(declared)
        query_names = [p["name"] for p in contract["query_parameters"]]
        if len(query_names) != len(set(query_names)):
            raise ValueError("Duplicate query fields")
        if contract["path"] in identities:
            raise ValueError("Duplicate public operation")
        identities.add(contract["path"])
        result.append((entry, contract))
    return result


DESCRIPTIONS = {
    "deliveryDate": "Source operating date, without an inferred timezone.",
    "hourEnding": "Source hour-ending label, including 24:00.",
    "settlementPoint": "Source hub, zone, or resource-node identifier.",
    "settlementPointPrice": "Decimal source price in dollars per MWh.",
    "ancillaryType": "Source ancillary-service identifier.",
    "MCPC": "Decimal source capacity clearing price.",
    "DSTFlag": "Raw source flag; no repeated-hour meaning is inferred.",
}


def render() -> str:
    """Render required public row fields with explicitly observed nullability.

    Returns:
        Model source for verified endpoints and their ordered fields.

    Raises:
        ValueError: A pin, field type, or supported endpoint differs.
    """
    lines = [
        "# Generated by tools/generate_public.py from pinned public field metadata.",
        '"""Observed public rows; undeclared fields and nullability fail decoding."""',
        "",
        "from datetime import "
        + ", ".join(
            sorted(
                {
                    TYPES[f["dataType"]]
                    for _, contract in contracts()
                    for f in contract["fields"]
                    if f["dataType"] in {"DATE", "DATETIME"}
                }
            )
        ),
        "from decimal import Decimal",
        "",
        "from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, StrictStr",
        "",
    ]
    for entry, contract in contracts():
        model, constant = entry["model"], entry["fields_constant"]
        fields = contract["fields"]
        lines.extend(
            [
                "",
                f"class {model}(BaseModel):",
                '    """A row from the observed public field contract.',
                "",
                "    Attributes:",
            ]
        )
        lines.extend(
            f"        {f['name']}: {DESCRIPTIONS.get(f['name'], 'Source ' + f['name'] + ' value.')}"
            for f in fields
        )
        lines.extend(
            [
                '    """',
                "",
                '    model_config = ConfigDict(extra="forbid", frozen=True)',
                "",
            ]
        )
        lines.extend(
            f"    {f['name']}: {TYPES[f['dataType']]}"
            + (
                " | None"
                if f["name"] in contract.get("observed_nullable_fields", [])
                else ""
            )
            for f in fields
        )
        lines.extend(["", "", f"{constant} = {{"])
        lines.extend(
            f"    {json.dumps(f['name'])}: {json.dumps(f['dataType'])}," for f in fields
        )
        lines.extend(["}", ""])
    return "\n".join(lines)


def render_registry() -> str:
    """Render typed filter dictionaries and operation identities.

    Returns:
        Registry source for the same verified row contracts.

    Raises:
        ValueError: A query field type or name is unsupported.
    """
    entries = contracts()
    lines = [
        "# Generated by tools/generate_public.py; do not edit.",
        '"""Verified public operation identities and complete query filter types."""',
        "",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import TypedDict",
        "",
        "from ._generated import (",
        *[f"    {name}," for name in sorted(e["model"] for e, _ in entries)],
        ")",
        "from .schema import Endpoint",
        "",
    ]
    for entry, contract in entries:
        model = entry["model"]
        lines.extend(
            [
                "",
                f"class {model}Filters(TypedDict, total=False):",
                '    """Optional filters from the pinned current query specification."""',
                "",
            ]
        )
        for parameter in contract["query_parameters"]:
            name = parameter["name"]
            if name in {"page", "size", "sort", "dir"}:
                continue
            if not name.isidentifier() or keyword.iskeyword(name):
                raise ValueError("Unsupported query field name")
            schema = parameter["schema"]
            kind = schema["type"]
            formats = {
                "string": {
                    None,
                    "abc123",
                    "yyyy-MM-dd",
                    "yyyy-MM-ddTH24:mm:ss",
                    "mm:ss",
                },
                "integer": {None, "###"},
                "number": {None, "####.###"},
                "boolean": {None, "true | false"},
            }
            if schema.get("format") not in formats.get(kind, set()):
                raise ValueError("Unsupported current query format")
            query_type = {
                "integer": "int",
                "number": "float | Decimal",
                "boolean": "bool",
                "string": "str",
            }.get(kind)
            if kind == "string" and schema.get("format") == "yyyy-MM-dd":
                query_type = "date"
            if kind == "string" and schema.get("format") == "yyyy-MM-ddTH24:mm:ss":
                query_type = "datetime"
            if query_type is None:
                raise ValueError("Unsupported current query type")
            lines.append(f"    {name}: {query_type}")
        lines.extend(
            [
                "",
                "",
                f"{entry['constant']}: Endpoint[{model}, {model}Filters] = Endpoint(",
                f"    {json.dumps(contract['path'])}, {model}, {json.dumps(entry['input'])}",
                ")",
                "",
            ]
        )
    lines.extend(
        ["", "ENDPOINTS = (", *[f"    {e['constant']}," for e, _ in entries], ")", ""]
    )
    # Imports vary with the current registry; use the pinned formatter/linter.
    formatted = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "F401,I001",
            "--fix",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--stdin-filename",
            str(REGISTRY_OUTPUT),
            "-",
        ],
        input="\n".join(lines),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--stdin-filename",
            str(REGISTRY_OUTPUT),
        ],
        input=formatted,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def render_products() -> str:
    """Generate typed product facades for every verified registry operation.

    Returns:
        Additive product namespaces; no legacy facade is imported or rewritten.
    """
    entries = contracts()
    lines = [
        '"""Generated typed public product facades; use with ReportsClient."""',
        "",
        "from . import _schemas",
        "",
    ]
    for product in sorted({contract["path"].split("/")[1] for _, contract in entries}):
        lines.extend(
            [
                "",
                f"class {product.replace('-', '_')}:",
                f'    """Verified operations for public product {product.upper()}."""',
                "",
            ]
        )
        for entry, contract in entries:
            if contract["path"].split("/")[1] == product:
                method = contract["path"].split("/")[2]
                if not method.isidentifier() or keyword.iskeyword(method):
                    method = "_" + method
                lines.append(f"    {method} = _schemas.{entry['constant']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Write or check additive models without changing legacy generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {
        OUTPUT: render(),
        REGISTRY_OUTPUT: render_registry(),
        PRODUCTS_OUTPUT: render_products(),
        BUNDLE_OUTPUT: json.dumps(
            {entry["input"]: contract for entry, contract in contracts()}, indent=2
        )
        + "\n",
    }
    if args.check:
        if any(path.read_text() != output for path, output in outputs.items()):
            raise SystemExit("Current generated models differ from the pinned inputs")
        print("Current models match pinned response metadata")
    else:
        for path, output in outputs.items():
            path.write_text(output)


if __name__ == "__main__":
    main()
