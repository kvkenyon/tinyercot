import re
from pathlib import Path

import httpx

OPENAPI_SPEC_URL = "https://raw.githubusercontent.com/ercot/api-specs/main/pubapi/pubapi-apim-api.json"
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


def generate(endpoints: dict, tags: dict):
    by_emil: dict[str, list] = {}
    for ep, (fields, summary) in endpoints.items():
        emil, suffix = ep.split("/", 1)
        by_emil.setdefault(emil, []).append((suffix, fields, summary))

    class_names = [safe_name(e) for e in sorted(by_emil)]
    lines = [
        "# AUTO-GENERATED — do not edit",
        "from __future__ import annotations",
        "import datetime",
        "from decimal import Decimal",
        "from typing import TypedDict",
        "from tinyercot._client import _get",
        "",
        f"__all__ = {class_names!r}",
        "",
    ]
    for emil, eps in sorted(by_emil.items()):
        lines.append(f"class {safe_name(emil)}:")
        if doc := tags.get(emil):
            lines.append(f'    """{doc}"""')
            lines.append("")
        for suffix, fields, summary in eps:
            lines.append(
                f"    class {pascal(suffix)}Params(TypedDict, total=False):"
            )
            for fn, ft in fields.items():
                lines.append(f"        {fn}: {ft}")
            lines.append("")
            lines.append("    @staticmethod")
            sig = ", ".join(
                f"{fn}: {ft} | None = None" for fn, ft in fields.items()
            )
            lines.append(f"    def {safe_name(suffix)}(*, {sig}) -> dict:")
            if summary:
                lines.append(f'        """{summary}"""')
            lines.append(
                f'        return _get("{emil}/{suffix}", '
                + ", ".join(f"{fn}={fn}" for fn in fields)
                + ")"
            )
            lines.append("")
    Path("tinyercot/_generated.py").write_text("\n".join(lines))
    print(f"Generated {len(by_emil)} classes in tinyercot/_generated.py")


if __name__ == "__main__":
    generate(*parse_openapi())
