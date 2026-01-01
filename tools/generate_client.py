import argparse
import json
import re
import time
from pathlib import Path

import httpx

OPENAPI_SPEC_URL = "https://raw.githubusercontent.com/ercot/api-specs/main/pubapi/pubapi-apim-api.json"
CACHE_FILE = Path(__file__).parent.parent / "api_response_fields.json"

# OpenAPI schema types -> Python types (for query params)
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

# ERCOT dataType -> Python types (for response fields)
RESPONSE_TYPE_MAP = {
    "BOOLEAN": "bool",
    "DATE": "datetime.date",
    "DATETIME": "datetime.datetime",
    "DOUBLE": "Decimal",
    "INTEGER": "int",
    "TIME": "datetime.time",
    "VARCHAR": "str",
}


def fetch_response_fields(debug: bool = False) -> dict:
    """Fetch all endpoint response field definitions from ERCOT products API."""
    from tqdm import tqdm

    from tinyercot._client import _get

    products = _get("/")["_embedded"]["products"]
    endpoints = [
        (p["emilId"].lower(), a["_links"]["endpoint"]["href"].split("/")[-1])
        for p in products
        for a in p.get("artifacts", [])
    ]
    response_fields = {}
    for emil_id, suffix in tqdm(endpoints, desc="Fetching fields"):
        ep = f"{emil_id}/{suffix}"
        try:
            ep_data = _get(ep)
            response_fields[ep] = {
                f["name"]: f["dataType"] for f in ep_data.get("fields", [])
            }
        except Exception as e:
            if debug:
                print(f"ERROR {ep}: {e}")
            response_fields[ep] = {}
        time.sleep(1)  # Rate limiting
    return response_fields


def load_response_fields(refresh: bool = False, debug: bool = False) -> dict:
    """Load response fields from cache, or fetch if refresh=True."""
    if CACHE_FILE.exists() and not refresh:
        return json.loads(CACHE_FILE.read_text())
    if refresh:
        fields = fetch_response_fields(debug=debug)
        CACHE_FILE.write_text(json.dumps(fields, indent=2))
        print(f"Saved response fields to {CACHE_FILE}")
        return fields
    raise FileNotFoundError(
        f"Cache file {CACHE_FILE} not found. Run with --refresh."
    )


def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s).replace("  ", " ").strip()


def get_type(param: dict) -> str:
    schema = param.get("schema", {})
    fmt = schema.get("format", "")
    return FORMAT_MAP.get(fmt) or TYPE_MAP.get(schema.get("type"), "str")


def parse_openapi() -> tuple[dict, dict]:
    spec = httpx.get(OPENAPI_SPEC_URL).json()
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
    n = s.replace("-", "_")
    return f"_{n}" if n[0].isdigit() else n


def pascal(s: str) -> str:
    result = "".join(w.capitalize() for w in s.replace("-", "_").split("_"))
    return f"_{result}" if result[0].isdigit() else result


def compact_fields(fields: dict[str, str], per_line: int = 4) -> list[str]:
    """Format model fields compactly with semicolons."""
    items = list(fields.items())
    lines = []
    for i in range(0, len(items), per_line):
        group = items[i : i + per_line]
        lines.append("; ".join(f"{fn}: {ft}" for fn, ft in group))
    return lines


def generate(endpoints: dict, tags: dict, response_fields: dict):
    by_emil: dict[str, list] = {}
    for ep, (params, summary) in endpoints.items():
        emil, suffix = ep.split("/", 1)
        resp_fields = response_fields.get(ep, {})
        by_emil.setdefault(emil, []).append(
            (suffix, params, summary, resp_fields)
        )

    class_names = [safe_name(e) for e in sorted(by_emil)]
    lines = [
        "# AUTO-GENERATED — do not edit",
        "from __future__ import annotations",
        "import datetime",
        "from decimal import Decimal",
        "from typing import ClassVar",
        "from pydantic import BaseModel",
        "from tinyercot._client import _get, ErcotResponse",
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
            # Row model - Pydantic BaseModel
            lines.append(f"    class {pc}Row(BaseModel):")
            if resp_fields:
                typed_fields = {
                    fn: RESPONSE_TYPE_MAP.get(ft, "str")
                    for fn, ft in resp_fields.items()
                }
                for line in compact_fields(typed_fields, per_line=4):
                    lines.append(f"        {line}")
            else:
                lines.append("        pass")
            # Response model - ErcotResponse with schema
            lines.append(f"    class {pc}Response(ErcotResponse[{pc}Row]):")
            lines.append(f"        _schema: ClassVar[dict] = {resp_fields!r}")
            # Method
            lines.append("    @staticmethod")
            sig = ", ".join(
                f"{fn}: {ft} | None = None" for fn, ft in params.items()
            )
            lines.append(
                f"    def {safe_name(suffix)}(*, {sig}) -> {pc}Response:"
            )
            if summary:
                lines.append(f'        """{summary}"""')
            call_args = ", ".join(f"{fn}={fn}" for fn in params)
            lines.append(
                f"        return {safe_name(emil)}.{pc}Response.model_validate("
                f'_get("{emil}/{suffix}", schema={resp_fields!r}, {call_args}))'
            )
    Path("tinyercot/_generated.py").write_text("\n".join(lines))
    print(f"Generated {len(by_emil)} classes in tinyercot/_generated.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tinyercot client")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch response fields from ERCOT API (requires credentials)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print exceptions when fetching fields",
    )

    args = parser.parse_args()

    endpoints, tags = parse_openapi()
    response_fields = load_response_fields(
        refresh=args.refresh, debug=args.debug
    )
    generate(endpoints, tags, response_fields)
