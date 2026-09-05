"""Capture baseline contracts; golden updates require explicit compatibility review."""

import hashlib
import inspect
import json

from tinyercot import _client, _generated


def schema_hash(model):
    """Hash a model schema without depending on JSON dictionary ordering.

    Args:
        model: Pydantic model whose JSON schema is part of the contract.

    Returns:
        A SHA-256 over canonical JSON schema text.
    """
    data = json.dumps(model.model_json_schema(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def model_contract(model):
    """Capture model identity, ordered fields, defaults, and schema essentials.

    Args:
        model: Legacy row or response model.

    Returns:
        JSON-compatible contract with a complete JSON schema digest.
    """
    return {
        "module": model.__module__,
        "qualname": model.__qualname__,
        "bases": [str(base) for base in model.__bases__],
        "config": dict(model.model_config),
        "schema_sha256": schema_hash(model),
        "wire_schema": list(getattr(model, "_schema", {}).items()),
        "fields": [
            [
                name,
                str(field.annotation),
                field.is_required(),
                field.alias,
                str(field.default),
                getattr(field.default_factory, "__name__", None),
            ]
            for name, field in model.model_fields.items()
        ],
    }


def method_contract(fn):
    """Capture signature defaults and the function execution category.

    Args:
        fn: Legacy public function or static method.

    Returns:
        Signature digest and independent generator/coroutine category flags.
    """
    return {
        "signature_sha256": hashlib.sha256(
            str(inspect.signature(fn)).encode()
        ).hexdigest(),
        "generator": inspect.isgeneratorfunction(fn),
        "async_generator": inspect.isasyncgenfunction(fn),
        "coroutine": inspect.iscoroutinefunction(fn),
    }


def snapshot():
    """Capture all generated methods, nested models, and the base envelope.

    Returns:
        JSON-compatible baseline with 510 methods and 205 models.
    """
    methods, models = {}, {}
    for name in _generated.__all__:
        for member, value in vars(getattr(_generated, name)).items():
            key = f"{name}.{member}"
            if isinstance(value, staticmethod):
                methods[key] = method_contract(value.__func__)
            elif isinstance(value, type) and issubclass(value, _client.BaseModel):
                models[key] = model_contract(value)
    models["_client.ErcotResponse"] = model_contract(_client.ErcotResponse)
    return {
        "base_sha": "d1daad25df42d3fff41f88b907d99ef325b970e0",
        "generated_all": _generated.__all__,
        "configure": method_contract(_client.configure),
        "to_df": method_contract(_client.ErcotResponse.to_df),
        "methods": methods,
        "models": models,
    }
