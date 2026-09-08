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


@pytest.mark.parametrize(
    "service,method,parameter",
    [
        ("Client", "np4_190_cd.dam_stlmnt_pnt_prices", "deliveryDateFrom"),
        ("ESRClient", "rptesr_m._4_sec_esr_charging_mw", "AGCExecTimeUTCFrom"),
    ],
)
def test_invalid_arguments_are_rejected_by_type_checker(
    tmp_path, service, method, parameter
):
    import subprocess
    import sys

    snippet = tmp_path / "invalid_usage.py"
    snippet.write_text(
        f"from tinyercot import {service}\nc = {service}()\nc.{method}({parameter}=123)\nc.{method}(unknown_filter=True)\n"
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


def test_public_real_time_conditions():
    from datetime import datetime
    from decimal import Decimal

    source = (INPUTS / "dashboards/real-time-system-conditions.html").read_text()

    def handler(request):
        assert (
            request.url
            == "https://www.ercot.com/content/cdr/html/real_time_system_conditions.html"
        )
        assert "authorization" not in request.headers
        return httpx.Response(200, text=source)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result = Client(client=http).dashboards.real_time_conditions()
    assert result.lastUpdated == datetime.fromisoformat("2026-09-08T00:42:50")
    assert result.lastUpdated.tzinfo is None
    assert result.model_dump(exclude={"lastUpdated"}) == {
        "currentFrequency": Decimal("59.984"),
        "instantaneousTimeError": Decimal("-2.123"),
        "consecutiveBaalExceedances": 0,
        "actualSystemDemand": Decimal(65912),
        "averageNetLoad": Decimal(48039),
        "totalSystemCapacity": Decimal(86005),
        "totalWindOutput": Decimal(17978),
        "totalPvgrOutput": Decimal(0),
        "currentSystemInertia": Decimal(328564),
        "dcE": Decimal(-443),
        "dcL": Decimal(70),
        "dcN": Decimal(-218),
        "dcR": Decimal(83),
        "dcS": Decimal(0),
    }


@pytest.mark.parametrize("change", ["markup", "missing", "duplicate"])
def test_real_time_conditions_use_labels_and_reject_incomplete_readings(change):
    import re
    from decimal import Decimal

    source = (INPUTS / "dashboards/real-time-system-conditions.html").read_text()
    row = re.search(
        r"<tr>\s*<td[^>]*>Instantaneous Time Error</td>.*?</tr>", source, re.DOTALL
    )[0]
    if change == "missing":
        source = source.replace(row, "")
    elif change == "duplicate":
        source = source.replace(row, row + row)
    else:
        # Moving the row and splitting its label across markup must preserve its meaning.
        source = source.replace(row, "").replace("</tbody>", row + "</tbody>")
        source = source.replace(
            "Instantaneous Time Error", "<span>Instantaneous</span>&nbsp;Time Error"
        )

    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=source))
    ) as http:
        if change == "markup":
            assert Client(
                client=http
            ).dashboards.real_time_conditions().instantaneousTimeError == Decimal(
                "-2.123"
            )
        else:
            with pytest.raises(ValueError):
                Client(client=http).dashboards.real_time_conditions()


@pytest.mark.parametrize(
    "hubs_and_zones,source,count,first_point",
    [(False, "current_np6788", 2, "7RNCHSLR_ALL"), (True, "hb_lz", 15, "HB_BUSAVG")],
)
def test_public_lmps_keep_price_components_and_changes(
    hubs_and_zones, source, count, first_point
):
    from datetime import datetime
    from decimal import Decimal

    body = (INPUTS / "dashboards" / f"{source}.html").read_text()

    def handler(request):
        assert request.url.path == f"/content/cdr/html/{source}.html"
        assert "authorization" not in request.headers
        return httpx.Response(200, text=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result = Client(client=http).dashboards.real_time_lmps(
            hubs_and_zones=hubs_and_zones
        )
    assert result.lastUpdated == datetime.fromisoformat("2026-09-08T00:50:15")
    assert result.lastUpdated.tzinfo is None
    assert result.RTRDPA == Decimal("0.71")
    assert len(result.data) == count
    row = result.data[0]
    assert row.settlementPoint == first_point
    assert row.LMP == Decimal("32.17")
    assert row.lmpChange == Decimal("0.48")
    assert row.lmpWithAdder == Decimal("32.88")
    assert row.lmpWithAdderChange == Decimal("-0.01")


@pytest.mark.parametrize(
    "old,new",
    [
        ("5&nbsp;Min<br>Change to&nbsp;LMP", "Unknown Price"),
        ("RTRDPA: $0.71", "Unknown: $0.71"),
    ],
)
def test_public_lmps_reject_unknown_price_components(old, new):
    body = (INPUTS / "dashboards/current_np6788.html").read_text()
    assert old in body
    body = body.replace(old, new)
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        ) as http,
        pytest.raises(ValueError),
    ):
        Client(client=http).dashboards.real_time_lmps()


@pytest.mark.parametrize("point", ["HB_BUSAVG", "HB_HOUSTON"])
def test_indicative_prices_preserve_runs_horizons_and_adder_semantics(point):
    from datetime import datetime
    from decimal import Decimal

    name = "rtd_ind_lmp_lz_hb" + ("" if point == "HB_BUSAVG" else "_" + point)
    body = (INPUTS / "dashboards" / f"{name}.html").read_text()

    def handler(request):
        assert request.url.path == f"/content/cdr/html/{name}.html"
        assert "authorization" not in request.headers
        return httpx.Response(200, text=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result = Client(client=http).dashboards.indicative_prices(point)
    assert result.settlementPoint == point
    assert result.includesReliabilityAdder is True
    assert result.lastSCEDTimestamp == datetime.fromisoformat("2026-09-08T01:05:16")
    assert result.lastSCEDTimestamp.tzinfo is None
    assert len(result.data) == 2
    run = result.data[0]
    assert run.RTDTimestamp == datetime.fromisoformat("2026-09-08T01:05:03")
    assert run.actualLMP == Decimal("36.14")
    assert [interval.intervalId for interval in run.intervals] == list(range(1, 12))
    assert [interval.minutesAhead for interval in run.intervals] == list(
        range(5, 60, 5)
    )
    assert [interval.LMP for interval in run.intervals] == list(
        map(
            Decimal,
            [
                "36.14",
                "34.57",
                "32.33",
                "31.92",
                "31.41",
                "31.07",
                "30.69",
                "30.12",
                "29.69",
                "29.47",
                "29.40",
            ],
        )
    )
    assert type(result).model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("point", ["INVALID", "HB_HOUSTON"])
def test_indicative_prices_reject_unknown_or_mismatched_points(point):
    body = (INPUTS / "dashboards/rtd_ind_lmp_lz_hb.html").read_text()
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        ) as http,
        pytest.raises(ValueError),
    ):
        Client(client=http).dashboards.indicative_prices(point)


@pytest.mark.parametrize("change", ["horizon", "missing_price"])
def test_indicative_prices_reject_ambiguous_or_truncated_horizons(change):
    body = (INPUTS / "dashboards/rtd_ind_lmp_lz_hb.html").read_text()
    if change == "horizon":
        body = body.replace("(Time+55)", "(Unknown)")
    else:
        assert '<td class="labelClassCenter">29.40</td>' in body
        body = body.replace('<td class="labelClassCenter">29.40</td>', "", 1)
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        ) as http,
        pytest.raises(ValueError),
    ):
        Client(client=http).dashboards.indicative_prices()


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


@pytest.mark.parametrize(
    "filename", ["system-wide-demand.json", "system-wide-demand-before-day-ahead.json"]
)
def test_system_demand_preserves_available_data_before_day_ahead_publication(filename):
    from datetime import datetime
    from decimal import Decimal

    raw = (INPUTS / "dashboards" / filename).read_bytes()
    body = json.loads(raw, parse_float=Decimal)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=raw))
    ) as http:
        snapshot = Client(client=http).dashboards.system_demand()
    missing_forecasts = 0
    for name in ("previousDay", "currentDay", "nextDay"):
        for row, source in zip(
            getattr(snapshot, name).data, body[name]["data"], strict=True
        ):
            assert row.timestamp == datetime.fromisoformat(source["timestamp"])
            assert row.hourEnding == source["hourEnding"]
            assert row.epoch == source["epoch"]
            assert row.dstFlag == source["dstFlag"]
            for key in (
                "currentLoadForecast",
                "dayAheadForecast",
                "currentDayHsl",
                "dayAheadHsl",
                "systemLoad",
            ):
                value = source.get(key)
                assert getattr(row, key) == (
                    Decimal(value) if value is not None else None
                )
            missing_forecasts += row.dayAheadForecast is None
    if filename.endswith("before-day-ahead.json"):
        assert missing_forecasts == 24
        assert snapshot.currentDay.data[0].systemLoad == Decimal("66748.26")
        assert all(row.dayAheadHsl is None for row in snapshot.nextDay.data)
        assert all(row.currentLoadForecast is not None for row in snapshot.nextDay.data)


@pytest.mark.parametrize(
    "filename", ["combine-wind-solar.json", "combine-wind-solar-before-day-ahead.json"]
)
def test_wind_solar_preserves_null_day_ahead_forecasts_and_actual_zeroes(filename):
    from datetime import datetime
    from decimal import Decimal

    raw = (INPUTS / "dashboards" / filename).read_bytes()
    body = json.loads(raw, parse_float=Decimal)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=raw))
    ) as http:
        snapshot = Client(client=http).dashboards.combined_wind_solar()
    for name in ("currentDay", "nextDay"):
        actual = getattr(snapshot, name).data
        assert actual.keys() == body[name]["data"].keys()
        for key, source in body[name]["data"].items():
            for field, value in actual[key].model_dump().items():
                original = source.get(field)
                if field == "timestamp":
                    assert value == datetime.fromisoformat(original)
                else:
                    assert value == original
    if filename.endswith("before-day-ahead.json"):
        for row in snapshot.nextDay.data.values():
            assert row.copHslWindDayAhead is None
            assert row.stwpfDayAhead is None
            assert row.wgrppDayAhead is None
            assert row.copHslSolarDayAhead is None
            assert row.stppfDayAhead is None
            assert row.pvgrppDayAhead is None
            assert row.stwpf is not None
        first = next(iter(snapshot.currentDay.data.values()))
        assert first.copHslSolarDayAhead == Decimal(0)
        assert first.stppfDayAhead == Decimal(0)


def test_real_time_lmps_preserve_prices_when_a_change_is_unavailable():
    import re
    from decimal import Decimal
    from html import unescape
    from zipfile import ZipFile

    with ZipFile(INPUTS / "dashboards/current_np6788-missing-change.zip") as archive:
        body = archive.read("current_np6788.html").decode()
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
    ) as http:
        snapshot = Client(client=http).dashboards.real_time_lmps()
    rows = [
        [
            " ".join(unescape(re.sub(r"<[^>]+>", " ", c)).split())
            for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        ]
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.DOTALL)
    ][2:]
    assert len(snapshot.data) == len(rows) == 1123
    missing = []
    for typed, raw in zip(snapshot.data, rows, strict=True):
        assert typed.settlementPoint == raw[0]
        assert typed.LMP == Decimal(raw[1])
        assert typed.lmpChange == (None if raw[2] == "-" else Decimal(raw[2]))
        assert typed.lmpWithAdder == Decimal(raw[3])
        assert typed.lmpWithAdderChange == Decimal(raw[4])
        if typed.lmpChange is None:
            missing.append(typed.settlementPoint)
    assert missing == ["APPALOSA_ALL", "HB_NORTH", "MIDP_SLR_RN"]


@pytest.mark.parametrize("change", ["-1.25", "0.00", "unrecognized"])
def test_price_change_marker_does_not_hide_real_numbers_or_invalid_data(change):
    from decimal import Decimal

    from tinyercot._dashboards import RealTimeLmp

    values = {
        "Settlement Point": "HB_NORTH",
        "LMP": "-12.50",
        "5 Min Change to LMP": change,
        "RTRDPA + LMP": "-12.40",
        "5 Min Change to RTRDPA + LMP": "0.00",
    }
    if change == "unrecognized":
        with pytest.raises(ValueError):
            RealTimeLmp.model_validate(values)
    else:
        row = RealTimeLmp.model_validate(values)
        assert row.lmpChange == Decimal(change)
        assert row.LMP == Decimal("-12.50")
