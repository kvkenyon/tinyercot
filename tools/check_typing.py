"""Check public types from an installed wheel outside the source checkout."""

import argparse
import ast
import json
import keyword
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def registry_assertions(source: str, bundle: dict) -> tuple[str, str, dict[str, int]]:
    """Build precise static consumers for every installed generated endpoint.

    Args:
        source: Installed generated registry source, used only to locate symbols.
        bundle: Installed pinned contracts, used for expected field/filter types.

    Returns:
        Positive assertions, negative filter uses, and exact proof counts. The
        emitted functions are type-checked only and never make data requests.

    Raises:
        ValueError: Registry identities or types do not match the pinned contracts.
    """
    imports = [
        '"""Installed static assertions; these functions are never executed."""',
        "from collections.abc import Iterator",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import assert_type",
        "from tinyercot import public",
        "from tinyercot.public import DataPage, Endpoint, ReportsClient, products",
        "from tinyercot.public import _generated as rows, _schemas as schemas",
        "",
    ]
    positive = list(imports)
    negative = [
        '"""Every installed endpoint must reject an unknown query filter."""',
        "from tinyercot.public import ReportsClient, products",
        "",
        "def invalid_registry(client: ReportsClient) -> None:",
    ]
    counts = {"endpoints": 0, "row_fields": 0, "filter_fields": 0, "invalid_uses": 0}
    observed_paths = set()
    row_types = {
        "DATE": "date",
        "DATETIME": "datetime",
        "VARCHAR": "str",
        "INTEGER": "int",
        "LONG": "int",
        "BOOLEAN": "bool",
        "DOUBLE": "Decimal",
        "DECIMAL": "Decimal",
        "FLOAT": "Decimal",
    }
    query_types = {
        "string": "str",
        "integer": "int",
        "number": "float | Decimal",
        "boolean": "bool",
    }
    examples = {
        "str": '"synthetic"',
        "int": "1",
        "float | Decimal": 'Decimal("1.25")',
        "bool": "False",
        "date": "date(2026, 9, 4)",
        "datetime": "datetime(2026, 9, 4, 1, 2, 3)",
    }
    for node in ast.parse(source).body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if not isinstance(node.value, ast.Call):
            raise TypeError("Unknown generated endpoint declaration")
        path, model, contract_name = (ast.unparse(arg) for arg in node.value.args)
        path = ast.literal_eval(path)
        contract_name = ast.literal_eval(contract_name)
        contract = bundle[contract_name]
        if contract["path"] != path or path in observed_paths:
            raise ValueError("Installed endpoint identity differs from its contract")
        observed_paths.add(path)
        constant = node.target.id
        filter_type = model + "Filters"
        product, method = path.strip("/").split("/")
        if not method.isidentifier() or keyword.iskeyword(method):
            method = "_" + method
        facade = "products." + product.replace("-", "_") + "." + method
        generic = f"Endpoint[rows.{model}, schemas.{filter_type}]"
        positive.extend(
            [
                f"def check_{constant}(client: ReportsClient, row: rows.{model}) -> None:",
                f"    assert_type(schemas.{constant}, {generic})",
                f"    assert_type({facade}, {generic})",
                f"    filters: schemas.{filter_type} = {{",
            ]
        )
        if constant in {
            "DAM_PRICES",
            "DAM_CAPACITY_PRICES",
            "RT_PRICES",
            "SYSTEM_LOAD",
        }:
            positive.insert(
                len(positive) - 1, f"    assert_type(public.{constant}, {generic})"
            )
        filters = []
        for parameter in contract["query_parameters"]:
            name, schema = parameter["name"], parameter["schema"]
            if name in {"page", "size", "sort", "dir"}:
                continue
            expected = query_types[schema["type"]]
            if schema.get("format") == "yyyy-MM-dd":
                expected = "date"
            elif schema.get("format") == "yyyy-MM-ddTH24:mm:ss":
                expected = "datetime"
            positive.append(f"        {name!r}: {examples[expected]},")
            filters.append((name, expected))
        positive.append("    }")
        for name, expected in filters:
            positive.append(f"    assert_type(filters[{name!r}], {expected})")
        positive.extend(
            [
                f"    assert_type(schemas.{constant}.page(client, filters=filters), DataPage[rows.{model}])",
                f"    assert_type(client.page(schemas.{constant}, filters=filters).rows, tuple[rows.{model}, ...])",
                f"    assert_type({facade}.pages(client, filters=filters), Iterator[DataPage[rows.{model}]])",
                f"    assert_type({facade}.iter_rows(client, filters=filters), Iterator[rows.{model}])",
            ]
        )
        for descriptor in contract["fields"]:
            name = descriptor["name"]
            expected = row_types[descriptor["dataType"]]
            if name in contract.get("observed_nullable_fields", []):
                expected += " | None"
            positive.append(f"    assert_type(row.{name}, {expected})")
        positive.append("")
        negative.append(
            f"    {facade}.page(client, filters={{'not_a_source_filter': 1}})"
        )
        counts["endpoints"] += 1
        counts["row_fields"] += len(contract["fields"])
        counts["filter_fields"] += len(filters)
        counts["invalid_uses"] += 1
    if observed_paths != {contract["path"] for contract in bundle.values()}:
        raise ValueError("Installed registry does not cover every bundled contract")
    return "\n".join(positive) + "\n", "\n".join(negative) + "\n", counts


def legacy_assertions(source: str) -> tuple[str, int]:
    """Build static calls for every frozen generated legacy method.

    Args:
        source: The installed legacy generated module's Python source.

    Returns:
        Uncalled functions checking method returns and row fields, and method count.
    """
    lines = [
        '"""Static legacy assertions; this function is never executed."""',
        "from collections.abc import AsyncIterator, Iterator",
        "from typing import assert_type",
        "import datetime",
        "from decimal import Decimal",
        "import pandas as pd",
        "from tinyercot import *",
        "",
        "async def verify_legacy() -> None:",
    ]
    count = 0
    field_checks = []
    for category in ast.parse(source).body:
        if not isinstance(category, ast.ClassDef):
            continue
        nested_models = {
            node.name for node in category.body if isinstance(node, ast.ClassDef)
        }
        for model in category.body:
            if not isinstance(model, ast.ClassDef) or not model.name.endswith("Row"):
                continue
            field_checks.extend(
                [
                    "",
                    f"def verify_{category.name}_{model.name}(row: {category.name}.{model.name}) -> None:",
                ]
            )
            for declaration in model.body:
                if isinstance(declaration, ast.AnnAssign) and isinstance(
                    declaration.target, ast.Name
                ):
                    field_checks.append(
                        f"    assert_type(row.{declaration.target.id}, {ast.unparse(declaration.annotation)})"
                    )
        for method in category.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if method.returns is None:
                raise ValueError("Legacy method lacks a return annotation")
            expected = (
                method.returns.value
                if isinstance(method.returns, ast.Constant)
                else ast.unparse(method.returns)
            )
            for model in nested_models:
                expected = re.sub(
                    rf"\b{re.escape(model)}\b", f"{category.name}.{model}", expected
                )
            await_call = isinstance(method, ast.AsyncFunctionDef) and not any(
                isinstance(node, (ast.Yield, ast.YieldFrom))
                for node in ast.walk(method)
            )
            call = f"{category.name}.{method.name}()"
            lines.append(
                f"    assert_type({'await ' if await_call else ''}{call}, {expected})"
            )
            count += 1
    return "\n".join(lines + field_checks) + "\n", count


def main() -> None:
    """Require precise public types and rejected invalid uses from a real wheel.

    Raises:
        SystemExit: The interpreter uses the checkout or a type check fails.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    result = subprocess.run(
        [
            str(args.python),
            "-I",
            "-c",
            (
                "import importlib.metadata,json,sys,tinyercot; "
                "dist=importlib.metadata.distribution('tinyercot'); "
                "print(json.dumps({'module':tinyercot.__file__,'prefix':sys.prefix,"
                "'base_prefix':sys.base_prefix,'isolated':sys.flags.isolated,"
                "'wheel':dist.read_text('WHEEL'),'origin':json.loads(dist.read_text('direct_url.json') or '{}')}))"
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    installation = json.loads(result.stdout)
    package = Path(installation["module"]).resolve().parent
    if (
        package == ROOT / "tinyercot"
        or not (package / "py.typed").is_file()
        or not installation["isolated"]
        or installation["prefix"] == installation["base_prefix"]
        or not package.is_relative_to(Path(installation["prefix"]).resolve())
        or "site-packages" not in package.parts
        or not installation["wheel"]
        or "archive_info" not in installation["origin"]
    ):
        raise SystemExit("Typing proof requires an installed PEP 561 wheel")
    installed_bundle = (package / "public/_contracts.json").read_bytes()
    if installed_bundle != (ROOT / "tinyercot/public/_contracts.json").read_bytes():
        raise SystemExit("Installed registry differs from the current pinned contracts")
    registry, invalid_registry, registry_counts = registry_assertions(
        (package / "public/_schemas.py").read_text(), json.loads(installed_bundle)
    )
    legacy, count = legacy_assertions((package / "_generated.py").read_text())
    if count != 510:
        raise SystemExit("Installed legacy method inventory changed")
    field_count = legacy.count("assert_type(") - count
    if field_count != 1334:
        raise SystemExit("Installed legacy row-field inventory changed")
    with tempfile.TemporaryDirectory(prefix="tinyercot-typing-") as directory:
        scratch = Path(directory)
        shutil.copyfile(
            ROOT / "tests/typing_public.py", scratch / "public_contracts.py"
        )
        shutil.copyfile(
            ROOT / "tests/typing_invalid.py", scratch / "invalid_contracts.py"
        )
        (scratch / "legacy_contracts.py").write_text(legacy)
        (scratch / "registry_contracts.py").write_text(registry)
        (scratch / "invalid_registry.py").write_text(invalid_registry)
        environment = {
            k: v for k, v in os.environ.items() if k not in {"MYPYPATH", "PYTHONPATH"}
        }
        command = [
            sys.executable,
            "-m",
            "mypy",
            "--python-executable",
            str(args.python),
            "--config-file",
            os.devnull,
            "--strict",
            "--no-incremental",
        ]
        positive = subprocess.run(
            command
            + ["public_contracts.py", "legacy_contracts.py", "registry_contracts.py"],
            cwd=scratch,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if positive.returncode:
            print(positive.stdout)
            raise SystemExit("Installed positive typing proof failed")
        negative = subprocess.run(
            command + ["invalid_contracts.py", "invalid_registry.py"],
            cwd=scratch,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        expected_invalid = 8 + registry_counts["invalid_uses"]
        if (
            negative.returncode != 1
            or negative.stdout.count(": error:") != expected_invalid
        ):
            print(negative.stdout)
            raise SystemExit(
                f"Installed typing proof did not reject exactly {expected_invalid} invalid uses"
            )
    print(
        f"Installed PEP 561 proof passed: {count} legacy methods, {field_count} legacy row fields, "
        f"{registry_counts['endpoints']} current endpoints and product facades, "
        f"{registry_counts['row_fields']} current row fields, {registry_counts['filter_fields']} filters, "
        f"live/archive/metadata surfaces, {expected_invalid} rejected invalid uses"
    )


if __name__ == "__main__":
    main()
