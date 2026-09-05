import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest
from legacy_contract import method_contract, model_contract

import tinyercot
from tinyercot import _client, _generated

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads((ROOT / "tests/fixtures/legacy-contract.json").read_text())


def resolve(name):
    module, member = name.split(".")
    return getattr(
        _client if module == "_client" else getattr(_generated, module), member
    )


def test_legacy_exports_and_import_paths():
    assert _generated.__all__ == GOLDEN["generated_all"]
    assert len(_generated.__all__) == 35
    assert _client.ErcotResponse is _generated.ErcotResponse
    assert tinyercot.configure is _client.configure
    assert method_contract(tinyercot.configure) == GOLDEN["configure"]
    assert method_contract(_client.ErcotResponse.to_df) == GOLDEN["to_df"]
    for name in _generated.__all__:
        assert getattr(tinyercot, name) is getattr(_generated, name)
    script = (
        "import socket; "
        "socket.socket.connect = lambda *a: (_ for _ in ()).throw(AssertionError()); "
        "import tinyercot, json; "
        "print(json.dumps(sorted(n for n in vars(tinyercot) if not n.startswith('_'))))"
    )
    names = json.loads(
        subprocess.check_output([sys.executable, "-c", script], cwd=ROOT)
    )
    assert names == sorted(["configure", *GOLDEN["generated_all"]])


@pytest.mark.parametrize("name", GOLDEN["methods"])
def test_legacy_signatures(name):
    assert method_contract(resolve(name)) == GOLDEN["methods"][name]
    assert all(
        p.kind == inspect.Parameter.KEYWORD_ONLY and p.default is None
        for p in inspect.signature(resolve(name)).parameters.values()
    )


@pytest.mark.parametrize("name", GOLDEN["models"])
def test_legacy_model_contracts(name):
    model = resolve(name)
    actual = json.loads(json.dumps(model_contract(model)))
    assert actual == GOLDEN["models"][name]
    obj = importlib.import_module(model.__module__)
    for part in model.__qualname__.split("."):
        obj = getattr(obj, part)
    assert obj is model


def test_complete_legacy_inventory():
    methods, models = set(), set()
    row_fields = 0
    for name in _generated.__all__:
        for member, value in vars(getattr(_generated, name)).items():
            if isinstance(value, staticmethod):
                methods.add(f"{name}.{member}")
            elif isinstance(value, type) and issubclass(value, _client.BaseModel):
                models.add(f"{name}.{member}")
                if member.endswith("Row"):
                    row_fields += len(value.model_fields)
    assert methods == set(GOLDEN["methods"])
    assert models == set(GOLDEN["models"]) - {"_client.ErcotResponse"}
    assert len(methods) == 510 and len(models) == 204 and row_fields == 1334
