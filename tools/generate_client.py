"""Reproduce the legacy client from hash-pinned local metadata.

This tool cannot refresh metadata or generate current API models. Use --check
to compare the frozen output without writing it. No network access is needed.
"""

import argparse
import hashlib
import json
import keyword
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "api_response_fields.json"
SPEC_FILE = ROOT / "tools/inputs/legacy-openapi.json"
PROVENANCE_FILE = ROOT / "tools/inputs/legacy-provenance.json"
OUTPUT_FILE = ROOT / "tinyercot/_generated.py"

# Preserve the legacy query type policy.
TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "Decimal",
    "boolean": "bool",
}
FORMAT_MAP = {
    "yyyy-MM-dd": "datetime.date",
    "yyyy-MM-ddTH24:mm:ss": "datetime.datetime",
}

# Preserve the legacy response type policy.
RESPONSE_TYPE_MAP = {
    "BOOLEAN": "bool",
    "DATE": "datetime.date",
    "DATETIME": "datetime.datetime",
    "DOUBLE": "Decimal",
    "INTEGER": "int",
    "TIME": "datetime.time",
    "VARCHAR": "str",
}


class GenerationError(ValueError):
    """Pinned metadata cannot safely reproduce the legacy client."""


def read_pinned(path: Path) -> dict:
    """Read a local input after checking its recorded content hash.

    Args:
        path: Input inside the repository with a recorded SHA-256.

    Returns:
        The decoded input, with JSON object order preserved.

    Raises:
        GenerationError: The input is missing, changed, or invalid JSON.
    """
    try:
        manifest = json.loads(PROVENANCE_FILE.read_text())
        data = path.read_bytes()
        expected = manifest["files"][path.relative_to(ROOT).as_posix()]
        if hashlib.sha256(data).hexdigest() != expected:
            raise GenerationError(f"Unverified input: {path}")
        return json.loads(data)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise GenerationError(f"Cannot read pinned input: {path}") from exc


def load_response_fields() -> dict:
    """Load the frozen row cache without authentication or network access.

    Returns:
        Ordered legacy field definitions, not current schema evidence.

    Raises:
        GenerationError: The pinned cache is missing or changed.
    """
    return read_pinned(CACHE_FILE)


def strip_html(s: str) -> str:
    """Remove markup with the frozen legacy whitespace policy.

    Args:
        s: Source description.

    Returns:
        Text used in the legacy class documentation.
    """
    return re.sub(r"<[^>]+>", " ", s).replace("  ", " ").strip()


def get_type(param: dict) -> str:
    """Map a query parameter under the explicit legacy format policy.

    Args:
        param: Inline OpenAPI query parameter metadata.

    Returns:
        The original Python annotation text.

    Raises:
        GenerationError: The type, format, or reference has no legacy policy.
    """
    schema = param.get("schema", {})
    fmt = schema.get("format", "")
    allowed = {
        "string": {"", "abc123", "mm:ss", *FORMAT_MAP},
        "integer": {"", "###"},
        "number": {"", "####.###"},
        "boolean": {"", "true | false"},
    }
    if (
        "$ref" in param
        or "$ref" in schema
        or fmt not in allowed.get(schema.get("type"), set())
    ):
        raise GenerationError(f"Unsupported query schema: {param}")
    return FORMAT_MAP.get(fmt) or TYPE_MAP[schema["type"]]


def parse_openapi() -> tuple[dict, dict]:
    """Parse the pinned projection of the legacy ERCOT OpenAPI export.

    Returns:
        Endpoint query definitions and product descriptions in source order.

    Raises:
        GenerationError: Inputs drift or a query schema is unsupported.
    """
    spec = read_pinned(SPEC_FILE)
    tags = {
        t["name"].lower(): strip_html(t.get("description", ""))
        for t in spec.get("tags", [])
    }
    endpoints = {}
    for path, methods in spec.get("paths", {}).items():
        if path.startswith("/{") or path in ("/", "/version"):
            continue
        get = methods.get("get", {})
        params = get.get("parameters", [])
        query_params = {
            p["name"]: get_type(p) for p in params if p.get("in") == "query"
        }
        if query_params:
            endpoints[path.lstrip("/")] = (query_params, get.get("summary", ""))
    return endpoints, tags


def safe_name(s: str) -> str:
    """Convert a legacy path segment into a Python identifier.

    Args:
        s: Nonempty endpoint or product path segment.

    Returns:
        The legacy name, including the prefix for numeric suffixes.
    """
    n = s.replace("-", "_")
    return f"_{n}" if n[0].isdigit() else n


def pascal(s: str) -> str:
    """Convert a path suffix into the legacy nested model name.

    Args:
        s: Nonempty endpoint suffix.

    Returns:
        The model name prefix, including any leading underscore.
    """
    result = "".join(w.capitalize() for w in s.replace("-", "_").split("_"))
    return f"_{result}" if result[0].isdigit() else result


def compact_fields(fields: dict[str, str], per_line: int = 4) -> list[str]:
    """Format ordered model fields with the legacy grouping policy.

    Args:
        fields: Field names and Python annotation text in source order.
        per_line: Maximum number of fields per output line.

    Returns:
        Source lines without leading indentation.
    """
    items = list(fields.items())
    lines = []
    for i in range(0, len(items), per_line):
        group = items[i : i + per_line]
        lines.append("; ".join(f"{fn}: {ft}" for fn, ft in group))
    return lines


def validate_inputs(endpoints: dict, tags: dict, response_fields: dict) -> None:
    """Reject unsafe names, missing row schemas, and unverified metadata.

    Args:
        endpoints: Ordered query contracts keyed by endpoint path.
        tags: Product documentation keyed by product identifier.
        response_fields: Ordered field definitions keyed by endpoint path.

    Raises:
        GenerationError: Input cannot reproduce the verified legacy baseline.
    """
    namespaces: dict[str, set[str]] = {}
    product_names: set[str] = set()
    products: set[str] = set()
    for ep, (params, summary) in endpoints.items():
        parts = ep.split("/")
        if len(parts) != 2 or not all(parts):
            raise GenerationError(f"Invalid endpoint path: {ep}")
        emil, suffix = parts
        product = safe_name(emil)
        if emil not in products:
            if product in product_names:
                raise GenerationError(f"Product collision: {ep}")
            products.add(emil)
            product_names.add(product)
        names = [
            safe_name(suffix) + tail
            for tail in ("", "_iter", "_df", "_iter_async", "_df_async")
        ] + [pascal(suffix) + tail for tail in ("Row", "Response")]
        seen = namespaces.setdefault(product, set())
        if len(set(names)) != len(names) or seen.intersection(names):
            raise GenerationError(f"Member collision: {ep}")
        seen.update(names)
        fields = response_fields.get(ep)
        if not fields:
            raise GenerationError(f"Missing or empty row schema: {ep}")
        for name in [product, *names, *params, *fields]:
            if not name.isidentifier() or keyword.iskeyword(name):
                raise GenerationError(f"Invalid Python identifier: {name}")
        if any(kind not in RESPONSE_TYPE_MAP for kind in fields.values()):
            raise GenerationError(f"Unsupported row type: {ep}")
        if any(name.startswith("_") for name in fields):
            raise GenerationError(f"Private row field: {ep}")
        for doc in (summary, tags.get(emil, "")):
            if '"""' in doc:
                raise GenerationError(f"Unsafe documentation: {ep}")
    expected_endpoints, expected_tags = parse_openapi()
    # Equality alone ignores field and parameter order, which is contractual.
    actual = json.dumps([endpoints, tags, response_fields])
    expected = json.dumps([expected_endpoints, expected_tags, load_response_fields()])
    if actual != expected:
        raise GenerationError(
            "Unverified metadata; legacy generation requires pinned inputs"
        )


def generate(endpoints: dict, tags: dict, response_fields: dict) -> str:
    """Render the exact legacy source without writing files.

    Args:
        endpoints: Frozen query contracts from parse_openapi().
        tags: Frozen product descriptions from parse_openapi().
        response_fields: Frozen row definitions from load_response_fields().

    Returns:
        Python source with the recorded legacy output hash.

    Raises:
        GenerationError: Inputs are unsafe, unverified, or change the output.
    """
    validate_inputs(endpoints, tags, response_fields)
    by_emil: dict[str, list] = {}
    for ep, (params, summary) in endpoints.items():
        emil, suffix = ep.split("/", 1)
        resp_fields = response_fields.get(ep, {})
        by_emil.setdefault(emil, []).append((suffix, params, summary, resp_fields))

    class_names = [safe_name(e) for e in sorted(by_emil)]
    lines = [
        "# AUTO-GENERATED — do not edit",
        "from __future__ import annotations",
        "import datetime",
        "from collections.abc import AsyncIterator, Iterator",
        "from decimal import Decimal",
        "from typing import ClassVar",
        "import pandas as pd",
        "from pydantic import BaseModel",
        "from tinyercot._client import _get, _aget, ErcotResponse",
        "",
        f"__all__ = {class_names!r}",
        "",
    ]
    for emil, eps in sorted(by_emil.items()):
        lines.append(f"class {safe_name(emil)}:")
        if doc := tags.get(emil):
            lines.append(f'    """{doc}"""')
        for suffix, params, summary, resp_fields in eps:
            pc = pascal(suffix)
            lines.append(f"    class {pc}Row(BaseModel):")
            typed_fields = {fn: RESPONSE_TYPE_MAP[ft] for fn, ft in resp_fields.items()}
            for line in compact_fields(typed_fields, per_line=4):
                lines.append(f"        {line}")
            lines.append(f"    class {pc}Response(ErcotResponse[{pc}Row]):")
            lines.append(f"        _schema: ClassVar[dict] = {resp_fields!r}")
            lines.append("    @staticmethod")
            sig = ", ".join(f"{fn}: {ft} | None = None" for fn, ft in params.items())
            lines.append(f"    def {safe_name(suffix)}(*, {sig}) -> {pc}Response:")
            if summary:
                lines.append(f'        """{summary}"""')
            call_args = ", ".join(f"{fn}={fn}" for fn in params)
            lines.append(
                f"        return {safe_name(emil)}.{pc}Response.model_validate("
                f'_get("{emil}/{suffix}", schema={resp_fields!r}, {call_args}))'
            )
            # Iterators own the page parameter. Preserve their signatures.
            call_args_no_page = ", ".join(f"{fn}={fn}" for fn in params if fn != "page")
            lines.append("    @staticmethod")
            sig_no_page = ", ".join(
                f"{fn}: {ft} | None = None" for fn, ft in params.items() if fn != "page"
            )
            lines.append(
                f"    def {safe_name(suffix)}_iter(*, {sig_no_page}) -> Iterator[{pc}Row]:"
            )
            lines.append('        """Yield all rows from all pages."""')
            lines.append("        page = 1")
            lines.append("        while True:")
            lines.append(
                f"            resp = {safe_name(emil)}.{safe_name(suffix)}({call_args_no_page}, page=page)"
            )
            lines.append("            yield from resp.data")
            lines.append('            if page >= resp.meta.get("totalPages", 1): break')
            lines.append("            page += 1")
            lines.append("    @staticmethod")
            lines.append(
                f"    def {safe_name(suffix)}_df(*, {sig_no_page}) -> pd.DataFrame:"
            )
            lines.append('        """Fetch all pages and return as DataFrame."""')
            lines.append(
                f"        resp = {safe_name(emil)}.{safe_name(suffix)}({call_args_no_page}, page=1)"
            )
            lines.append("        frames = [resp.to_df()]")
            lines.append(
                '        for p in range(2, resp.meta.get("totalPages", 1) + 1):'
            )
            lines.append(
                f"            frames.append({safe_name(emil)}.{safe_name(suffix)}({call_args_no_page}, page=p).to_df())"
            )
            lines.append("        return pd.concat(frames, ignore_index=True)")
            lines.append("    @staticmethod")
            lines.append(
                f"    async def {safe_name(suffix)}_iter_async(*, {sig_no_page}) -> AsyncIterator[{pc}Row]:"
            )
            lines.append(
                '        """Async yield all rows from all pages (rate-limited)."""'
            )
            lines.append("        page = 1")
            lines.append("        while True:")
            lines.append(
                f"            resp = {safe_name(emil)}.{pc}Response.model_validate("
                f'await _aget("{emil}/{suffix}", schema={resp_fields!r}, {call_args_no_page}, page=page))'
            )
            lines.append("            for row in resp.data: yield row")
            lines.append('            if page >= resp.meta.get("totalPages", 1): break')
            lines.append("            page += 1")
            lines.append("    @staticmethod")
            lines.append(
                f"    async def {safe_name(suffix)}_df_async(*, {sig_no_page}) -> pd.DataFrame:"
            )
            lines.append(
                '        """Async fetch all pages and return as DataFrame (rate-limited)."""'
            )
            lines.append(
                f"        resp = {safe_name(emil)}.{pc}Response.model_validate("
                f'await _aget("{emil}/{suffix}", schema={resp_fields!r}, {call_args_no_page}, page=1))'
            )
            lines.append("        frames = [resp.to_df()]")
            lines.append(
                '        for p in range(2, resp.meta.get("totalPages", 1) + 1):'
            )
            lines.append(
                f"            resp = {safe_name(emil)}.{pc}Response.model_validate("
                f'await _aget("{emil}/{suffix}", schema={resp_fields!r}, {call_args_no_page}, page=p))'
            )
            lines.append("            frames.append(resp.to_df())")
            lines.append("        return pd.concat(frames, ignore_index=True)")
    source = "\n".join(lines)
    expected = json.loads(PROVENANCE_FILE.read_text())["files"][
        "tinyercot/_generated.py"
    ]
    if hashlib.sha256(source.encode()).hexdigest() != expected:
        raise GenerationError("Generated output differs from the legacy baseline")
    return source


def main() -> None:
    """Check or write the frozen legacy source using local inputs only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare without writing")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    try:
        endpoints, tags = parse_openapi()
        source = generate(endpoints, tags, load_response_fields())
        if args.check:
            if args.output.read_bytes() != source.encode():
                raise GenerationError(f"Output differs: {args.output}")
            print("Legacy generation matches the pinned baseline")
        else:
            args.output.write_bytes(source.encode())
            print(f"Wrote the verified legacy client to {args.output}")
    except (GenerationError, OSError) as exc:
        parser.exit(1, f"Generation failed: {exc}\n")


if __name__ == "__main__":
    main()
