"""Run with an isolated Python interpreter after installing the built wheel."""

import importlib
import socket
from importlib.resources import files
from pathlib import Path


def deny_network(*args, **kwargs):
    """Stop any accidental network call during the installed-wheel smoke check.

    Args:
        *args: Ignored socket arguments.
        **kwargs: Ignored socket options.

    Raises:
        AssertionError: Any socket operation reaches this guard.
    """
    raise AssertionError("Wheel metadata must work offline")


socket.socket.connect = deny_network
socket.getaddrinfo = deny_network

tinyercot = importlib.import_module("tinyercot")
catalog = importlib.import_module("tinyercot.catalog")

assert (
    Path(tinyercot.__file__).resolve().parent
    != Path(__file__).resolve().parents[1] / "tinyercot"
)
assert files("tinyercot").joinpath("_catalog.json").is_file()
assert len(catalog.operations()) == 257 and len(catalog.sources()) == 8
assert len(tinyercot._generated.__all__) == 35
assert tinyercot.np3_910_er._2d_agg_dsr_loads
assert tinyercot.np4_190_cd.DamStlmntPntPricesResponse().to_df().columns.empty
print("Installed-wheel legacy imports and offline catalog passed")
