"""Check public types from an installed wheel outside the source checkout."""

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        [str(args.python), "-I", "-c", "import tinyercot; print(tinyercot.__file__)"],
        capture_output=True,
        text=True,
        check=True,
    )
    package = Path(result.stdout.strip()).resolve().parent
    if package == ROOT / "tinyercot" or not (package / "py.typed").is_file():
        raise SystemExit("Typing proof requires an installed PEP 561 wheel")
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
            command + ["public_contracts.py", "legacy_contracts.py"],
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
            command + ["invalid_contracts.py"],
            cwd=scratch,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if negative.returncode != 1 or negative.stdout.count(": error:") != 4:
            print(negative.stdout)
            raise SystemExit(
                "Installed typing proof did not reject exactly four invalid uses"
            )
    print(
        f"Installed PEP 561 proof passed: {count} legacy methods, {field_count} row fields, public surfaces, four rejected invalid uses"
    )


if __name__ == "__main__":
    main()
