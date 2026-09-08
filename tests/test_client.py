import json
from pathlib import Path

import httpx
import pytest

from tinyercot import Client, _generated
from tinyercot._client import History, Product

INPUTS = Path(__file__).resolve().parents[1] / "tools" / "inputs"


def test_live_product_and_history_shapes():
    for item in json.loads((INPUTS / "products.json").read_text())["_embedded"][
        "products"
    ]:
        Product.model_validate(item)
    for kind in ("archive", "bundle"):
        result = History.model_validate_json(
            (INPUTS / f"{kind}-sample.json").read_text()
        )
        assert result.meta.totalRecords >= len(result.archives or result.bundles)


@pytest.mark.parametrize(
    "sample", sorted((INPUTS / "samples").glob("*.json")), ids=lambda p: p.stem
)
def test_captured_rows_match_generated_models(sample):
    product, method = sample.stem.split("--")
    cls = getattr(_generated, product.replace("-", "_"))
    row_name = "".join(part.capitalize() for part in method.split("_")) + "Row"
    if row_name[0].isdigit():
        row_name = "_" + row_name
    row = getattr(cls, row_name)
    body = json.loads(sample.read_text())

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(
                200, json={"id_token": "test-token", "expires_in": 3600}
            )
        assert request.url.path == f"/api/public-reports/{product}/{method}"
        assert request.url.params["size"] == "1"
        return httpx.Response(200, json=body)

    method_name = "_" + method if method[0].isdigit() else method
    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("test", "test", "test", client=http) as client,
    ):
        namespace = getattr(client, product.replace("-", "_"))
        result = getattr(namespace, method_name)(size=1)
    assert len(result.data) == len(body["data"])
    assert all(isinstance(item, row) for item in result.data)
    assert (
        set(type(result.data[0]).model_fields)
        == set(
            getattr(row, "__source_fields__", None) or [f.name for f in result.fields]
        )
        if result.data
        else True
    )


def test_typed_pagination_auth_refresh_and_field_order():
    body = json.loads(
        (INPUTS / "samples/gen-55-cd--hrly_rt_load_fcast_actual.json").read_text()
    )
    calls = []
    auth_count = 0
    denied = False

    def handler(request):
        nonlocal auth_count, denied
        if "b2clogin" in request.url.host:
            auth_count += 1
            return httpx.Response(
                200, json={"id_token": f"token{auth_count}", "expires_in": 3600}
            )
        if not denied:
            denied = True
            return httpx.Response(401)
        page = int(request.url.params["page"])
        calls.append(page)
        payload = json.loads(json.dumps(body))
        payload["_meta"].update(currentPage=page, totalPages=2, totalRecords=2)
        payload["fields"].reverse()
        payload["data"] = [list(reversed(payload["data"][0]))]
        return httpx.Response(200, json=payload)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        rows = list(client.gen_55_cd.hrly_rt_load_fcast_actual_iter(size=1))
    assert len(rows) == 2
    assert calls == [1, 2]
    assert auth_count == 2
    assert rows[0] == rows[1]


def test_archive_download_post_shape():
    requests = []

    def handler(request):
        requests.append(request)
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "token", "expires_in": 3600})
        return httpx.Response(200, content=b"zip bytes")

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = Client("u", "p", "k", client=http)
        assert client.download("NP4-190-CD", [-123, 456], kind="bundle") == b"zip bytes"
    request = requests[-1]
    assert request.method == "POST"
    assert request.url.path.endswith("/bundle/np4-190-cd/download")
    assert json.loads(request.content) == {"docIds": [-123, 456]}


def test_async_iteration_uses_typed_rows():
    import asyncio

    body = json.loads(
        (INPUTS / "samples/gen-55-cd--hrly_rt_load_fcast_actual.json").read_text()
    )
    body["_meta"].update(totalPages=1, currentPage=1)

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "token", "expires_in": 3600})
        return httpx.Response(200, json=body)

    async def run():
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as ahttp:
                async with Client(
                    "u", "p", "k", client=http, async_client=ahttp
                ) as client:
                    rows = [
                        r
                        async for r in client.gen_55_cd.hrly_rt_load_fcast_actual_iter_async(
                            size=1
                        )
                    ]
                    assert isinstance(
                        rows[0], _generated.gen_55_cd.HrlyRtLoadFcastActualRow
                    )

    asyncio.run(run())


def test_invalid_arguments_are_rejected_by_type_checker(tmp_path):
    import subprocess
    import sys

    snippet = tmp_path / "invalid_usage.py"
    snippet.write_text(
        "from tinyercot import Client\nc = Client()\nc.np4_190_cd.dam_stlmnt_pnt_prices(deliveryDateFrom=123)\nc.np4_190_cd.dam_stlmnt_pnt_prices(unknown_filter=True)\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", str(snippet), "--follow-untyped-imports"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[arg-type]" in result.stdout
    assert "[call-arg]" in result.stdout


@pytest.mark.parametrize(
    "method,source",
    [
        ("fuel_mix", "fuel-mix"),
        ("grid_conditions", "daily-prc"),
        ("energy_storage", "energy-storage-resources"),
        ("generation_outages", "generation-outages"),
        ("dc_tie_flows", "dc-tie-flows"),
        ("system_prices", "system-wide-prices"),
        ("supply_demand", "supply-demand"),
        ("combined_wind_solar", "combine-wind-solar"),
        ("system_demand", "system-wide-demand"),
        ("ancillary_services", "ancillary-services"),
        ("sced_capacity", "capacity-available-sced"),
        ("ancillary_capacity", "ancillary-service-capacity-monitor"),
    ],
)
def test_dashboard_methods_need_no_credentials(method, source):
    body = json.loads((INPUTS / "dashboards" / f"{source}.json").read_text())

    def handler(request):
        assert request.url.host == "www.ercot.com"
        assert "authorization" not in request.headers
        assert request.url.path.endswith(f"/{source}.json")
        return httpx.Response(200, json=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result = getattr(Client(client=http).dashboards, method)()
    assert set(result.model_dump(by_alias=True)) == set(body)


def test_archive_listing_pagination():
    body = json.loads((INPUTS / "archive-page2-sample.json").read_text())
    pages = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "token", "expires_in": 3600})
        page = int(request.url.params["page"])
        pages.append(page)
        payload = json.loads(json.dumps(body))
        payload["_meta"].update(currentPage=page, totalPages=2, totalRecords=4)
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        docs = list(
            Client("u", "p", "k", client=http).iter_documents("np4-190-cd", size=2)
        )
    assert pages == [1, 2]
    assert len(docs) == 4


def test_weather_forecast():
    from tinyercot._dashboards import WeatherForecasts

    body = json.loads((INPUTS / "dashboards/weather-forecast.json").read_text())
    forecast = WeatherForecasts.model_validate(body).root
    assert len(forecast) == len(body)
    assert forecast[0].data["DFW"].high == int(body[0]["data"]["DFW"]["high"])


def test_capacity_feeds_preserve_values_and_source_sections():
    from datetime import datetime
    from decimal import Decimal

    from tinyercot._dashboards import AncillaryCapacitySnapshot, ScedCapacitySnapshot

    capacity = json.loads(
        (INPUTS / "dashboards/capacity-available-sced.json").read_text()
    )
    result = ScedCapacitySnapshot.model_validate(capacity)
    for period in ("current", "previous"):
        rows = getattr(result, period).data
        for row, source in zip(rows, capacity[period]["data"], strict=True):
            assert row.timestamp == datetime.fromisoformat(source["timestamp"])
            assert row.epoch == source["epoch"]
            assert row.dstFlag == source["dstFlag"]
            assert row.increaseGenResESRs == Decimal(source["increaseGenResESRs"])
            assert row.decreaseGenResESRs == Decimal(source["decreaseGenResESRs"])

    body = json.loads(
        (INPUTS / "dashboards/ancillary-service-capacity-monitor.json").read_text()
    )
    # Preserve fractional and negative telemetry instead of integer truncation.
    body["data"]["systemAvailableCapacityGroup"][1][1] = "-6.125"
    monitor = AncillaryCapacitySnapshot.model_validate(body)
    for group, table in body["data"].items():
        assert getattr(monitor.data, group).model_dump() == {
            key: Decimal(str(value)) for key, value in table[1:]
        }
    assert monitor.lastUpdated == datetime.fromisoformat(body["lastUpdated"])
    assert monitor.data.systemAvailableCapacityGroup.capClrDecreaseBp == Decimal(
        "-6.125"
    )
    assert monitor == AncillaryCapacitySnapshot.model_validate(monitor.model_dump())


@pytest.mark.parametrize(
    "table",
    [
        [["wrong", "header"], ["regUpAwd", 1], ["regDownAwd", 2]],
        [["key", "value"], ["regUpAwd", 1], ["regUpAwd", 2], ["regDownAwd", 3]],
        [["key", "value"], ["regUpAwd", 1]],
        [["key", "value"], ["regUpAwd", 1, 2], ["regDownAwd", 3]],
    ],
)
def test_capacity_tables_reject_lost_or_ambiguous_values(table):
    from pydantic import ValidationError

    from tinyercot._dashboards import RegulationAwards

    with pytest.raises(ValidationError):
        RegulationAwards.model_validate(table)


def test_single_bundle_400_uses_published_get_download():
    calls = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        calls.append(request)
        if request.method == "POST":
            assert json.loads(request.content) == {"docIds": [-593019152]}
            return httpx.Response(
                400, json={"message": "Your request could not be processed."}
            )
        assert request.url.path == "/api/public-reports/bundle/np4-190-cd"
        assert request.url.params["download"] == "-593019152"
        return httpx.Response(200, content=b"recovered zip bytes")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        assert (
            client.download("NP4-190-CD", [-593019152], kind="bundle")
            == b"recovered zip bytes"
        )
    assert [r.method for r in calls] == ["POST", "GET"]


@pytest.mark.parametrize(
    "kind,ids,status",
    [
        ("archive", [123], 400),
        ("bundle", [-123, -456], 400),
        ("bundle", [-123], 403),
    ],
)
def test_other_download_failures_are_not_reinterpreted(kind, ids, status):
    calls = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        calls.append(request)
        return httpx.Response(status, json={"message": "failed"})

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
        pytest.raises(httpx.HTTPStatusError) as error,
    ):
        client.download("NP4-190-CD", ids, kind=kind)
    assert error.value.response.status_code == status
    assert len(calls) == 1


def test_bundle_get_failure_propagates():
    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        return httpx.Response(400 if request.method == "POST" else 404)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
        pytest.raises(httpx.HTTPStatusError) as error,
    ):
        client.download("NP4-190-CD", [-123], kind="bundle")
    assert error.value.response.status_code == 404
