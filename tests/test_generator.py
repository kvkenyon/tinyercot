import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import generate_client as gen

ROOT = Path(__file__).resolve().parents[1]


def test_generator_reproducible_offline():
    endpoints, tags = gen.parse_openapi()
    fields = gen.load_response_fields()
    first = gen.generate(endpoints, tags, fields).encode()
    second = gen.generate(endpoints, tags, fields).encode()
    assert first == second == gen.OUTPUT_FILE.read_bytes()
    assert hashlib.sha256(first).hexdigest() == (
        "aaf91cb373b7557113e5343e4366e0d331566d82327ffabe4b9562937f3c2b5c"
    )


def test_cli_paths_are_independent_of_working_directory(tmp_path):
    cmd = [sys.executable, str(ROOT / "tools/generate_client.py")]
    subprocess.run([*cmd, "--check"], cwd=tmp_path, check=True)
    output = tmp_path / "generated.py"
    subprocess.run([*cmd, "--output", str(output)], cwd=tmp_path, check=True)
    assert output.read_bytes() == gen.OUTPUT_FILE.read_bytes()
    output.write_text("sentinel")
    result = subprocess.run(
        [*cmd, "--check", "--output", str(output)], cwd=tmp_path, check=False
    )
    assert result.returncode == 1
    assert output.read_text() == "sentinel"


@pytest.mark.parametrize("flag", ["--refresh", "--cache-products"])
def test_authenticated_refresh_is_not_a_generation_option(flag):
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/generate_client.py"), flag],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2


def test_pinned_files_and_runtime_are_unchanged():
    manifest = json.loads(gen.PROVENANCE_FILE.read_text())
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("content", [None, b"{}", b"invalid json"])
def test_missing_or_changed_pin_fails_closed(tmp_path, monkeypatch, content):
    path = tmp_path / "cache.json"
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    if content is not None:
        path.write_bytes(content)
    with pytest.raises(gen.GenerationError):
        gen.read_pinned(path)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "empty",
        "row_type",
        "field_name",
        "parameter_name",
        "query_type",
        "order",
        "new_endpoint",
        "method_collision",
        "product_collision",
        "summary",
        "quote",
        "private_field",
    ],
)
def test_unverified_row_or_query_contract_fails_closed(mutation):
    endpoints, tags = copy.deepcopy(gen.parse_openapi())
    fields = gen.load_response_fields()
    ep = next(iter(endpoints))
    if mutation == "missing":
        fields.pop(ep)
    elif mutation == "empty":
        fields[ep] = {}
    elif mutation == "row_type":
        fields[ep][next(iter(fields[ep]))] = "LONG"
    elif mutation == "field_name":
        fields[ep]["invalid-name"] = "VARCHAR"
    elif mutation == "private_field":
        fields[ep]["_hidden"] = "VARCHAR"
    elif mutation == "parameter_name":
        endpoints[ep][0]["class"] = "str"
    elif mutation == "query_type":
        endpoints[ep][0][next(iter(endpoints[ep][0]))] = "int"
    elif mutation == "order":
        fields[ep] = dict(reversed(list(fields[ep].items())))
    elif mutation in {"new_endpoint", "method_collision", "product_collision"}:
        product, suffix = ep.split("/")
        new_ep = {
            "new_endpoint": "np-new/new_data",
            "method_collision": ep + "_iter",
            "product_collision": product.replace("-", "_") + "/" + suffix,
        }[mutation]
        endpoints[new_ep] = endpoints[ep]
        fields[new_ep] = fields[ep]
    else:
        endpoints[ep] = (
            endpoints[ep][0],
            '"""unsafe' if mutation == "quote" else "changed",
        )
    with pytest.raises(gen.GenerationError):
        gen.generate(endpoints, tags, fields)


@pytest.mark.parametrize(
    "param",
    [
        {"$ref": "#/components/parameters/Unknown"},
        {"schema": {"$ref": "#/components/schemas/Unknown"}},
        {"schema": {"type": "array"}},
        {"schema": {"type": "string", "format": "date-time"}},
    ],
)
def test_unresolved_refs_and_formats_require_a_policy(param):
    with pytest.raises(gen.GenerationError):
        gen.get_type(param)


def test_failed_generation_does_not_overwrite_output(tmp_path, monkeypatch):
    output = tmp_path / "generated.py"
    output.write_bytes(b"keep existing output")
    monkeypatch.setattr(sys, "argv", ["generate_client.py", "--output", str(output)])
    monkeypatch.setattr(gen, "CACHE_FILE", ROOT / "missing-fields.json")
    with pytest.raises(SystemExit) as exc:
        gen.main()
    assert exc.value.code == 1
    assert output.read_bytes() == b"keep existing output"
