"""Run with an isolated Python interpreter after installing the built wheel."""

import importlib
import json
import socket
from datetime import date
from importlib.resources import files
from pathlib import Path

import httpx


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
response = tinyercot.np4_190_cd.DamStlmntPntPricesResponse.model_validate(
    {
        "data": [
            {
                "deliveryDate": "2026-09-04",
                "hourEnding": "24:00",
                "settlementPoint": "HB_HOUSTON",
                "settlementPointPrice": "12.25",
                "DSTFlag": False,
            }
        ]
    }
)
frame = response.to_df()
assert frame.deliveryDate[0] == date(2026, 9, 4)
assert str(frame.settlementPointPrice.dtype) == "float64"
assert frame.settlementPointPrice[0] == 12.25
assert str(frame.DSTFlag.dtype) == "bool"
public = importlib.import_module("tinyercot.public")
assert len(public.coverage()) == 298
assert files("tinyercot").joinpath("py.typed").is_file()
assert files("tinyercot.public").joinpath("_contracts.json").is_file()
assert public.RT_PRICES.row_model is public.RealTimePrice
assert len([entry for entry in public.coverage() if entry.status == "covered"]) == 6
assert public.Credentials("test", "test", "test")
with public.WebClient():
    pass
raw = (Path(__file__).parent / "fixtures/public/rt-prices-current.json").read_bytes()


def report_transport(request):
    """Serve synthetic authentication and retained public data without sockets.

    Args:
        request: Installed client's HTTP request.

    Returns:
        A synthetic ID token or a small saved public response.
    """
    if request.method == "POST":
        return httpx.Response(200, json={"id_token": "synthetic", "expires_in": 3600})
    return httpx.Response(200, content=raw)


with public.ReportsClient(
    public.Credentials("synthetic", "synthetic", "synthetic"),
    limits=public.StreamingLimits(min_interval=0),
    transport=httpx.MockTransport(report_transport),
) as client:
    page = client.page(public.RT_PRICES, size=2)
    assert len(page.rows) == len(json.loads(raw)["data"]) == 2
    assert type(page.rows[0]) is public.RealTimePrice
print("Installed-wheel legacy imports and opt-in public metadata passed")
