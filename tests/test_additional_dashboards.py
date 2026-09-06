import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from tinyercot.public._http import Limits, Payload, Receipt, SchemaMismatchError
from tinyercot.public.additional_dashboards import (
    SUPPLY_DEMAND_URL,
    SYSTEM_PRICES_URL,
    AdditionalDashboardClient,
    SupplyActualRow,
    SupplyForecastRow,
    decode_supply_demand,
    decode_system_prices,
)

ROOT = Path(__file__).resolve().parents[1]
PRICES = (ROOT / "tests/fixtures/public/system-wide-prices-live.json").read_bytes()
SUPPLY = (ROOT / "tests/fixtures/public/supply-demand-live.json").read_bytes()


def payload(raw):
    return Payload(
        raw,
        Receipt(
            SYSTEM_PRICES_URL,
            datetime.datetime(2026, 9, 6, 1, 5, tzinfo=datetime.UTC),
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        ),
    )


def test_price_sections_and_exact_source_values_remain_separate():
    result = decode_system_prices(payload(PRICES))
    assert len(result.real_time) == len(result.day_ahead) == 4
    assert result.real_time[0].hbHouston == Decimal("37.1")
    assert result.real_time[-1].hbNorth == Decimal("52.16")
    assert result.day_ahead[-1].hourEnding == 24
    assert result.day_ahead[-1].timestamp == "2026-09-06 00:00:00-0500"
    assert result.day_ahead[-1].interval > int(result.last_updated.timestamp() * 1000)
    assert result.raw == PRICES and not result.is_stale()


def test_supply_variants_retain_absent_actual_available_and_future_data():
    result = decode_supply_demand(payload(SUPPLY))
    assert len(result.data) == 8 and len(result.forecast) == 4
    actual = result.data[0]
    forecast = result.data[-1]
    assert isinstance(actual, SupplyActualRow) and actual.forecast == 0
    assert "available" not in actual.model_dump()
    assert isinstance(forecast, SupplyForecastRow) and forecast.available == 98151
    assert forecast.epoch > int(result.last_updated.timestamp() * 1000)
    assert result.forecast[-1].forecastedDemand == 70621
    assert result.forecast[-1].deliveryDateHrEnd == "2026-09-12 00:00:00"
    assert result.forecast[-1].dstFlag == "N"
    assert actual.dstFlag == 0
    assert result.raw == SUPPLY and not result.is_stale()


@pytest.mark.parametrize(
    "bad", [None, True, "37.1", [], {}, float("nan"), float("inf")]
)
def test_price_unknown_numeric_types_fail_closed(bad):
    body = json.loads(PRICES)
    body["rtSppData"][0]["hbHouston"] = bad
    with pytest.raises(SchemaMismatchError):
        decode_system_prices(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "offset",
        "extra",
        "missing",
        "rt_label",
        "dam_label",
        "duplicate",
        "future_actual",
    ],
)
def test_price_time_and_schema_drift_fail_closed(change):
    body = json.loads(PRICES)
    row = body["rtSppData"][0]
    if change == "epoch":
        row["interval"] += 1
    elif change == "offset":
        row["timestamp"] = row["timestamp"].replace("-0500", "-0600")
    elif change == "extra":
        row["newZone"] = 1
    elif change == "missing":
        row.pop("hbPan")
    elif change == "rt_label":
        row["intervalEnding"] = "07:00"
    elif change == "dam_label":
        body["damSppData"][-1]["hourEnding"] = 0
    elif change == "duplicate":
        body["rtSppData"].insert(0, row)
    elif change == "future_actual":
        body["lastUpdated"] = "2026-09-04 20:02:00-0500"
    with pytest.raises(SchemaMismatchError):
        decode_system_prices(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "boolean_forecast",
        "unknown_forecast",
        "missing_available",
        "actual_available",
        "null_available",
        "null_demand",
        "string_capacity",
        "flag_type",
        "epoch",
        "interval",
        "hour",
        "duplicate",
        "future_actual",
        "outlook_end",
        "outlook_begin",
        "outlook_day",
        "outlook_hour",
        "outlook_flag",
        "extra",
    ],
)
def test_supply_types_sections_and_temporal_drift_fail_closed(change):
    body = json.loads(SUPPLY)
    row = body["data"][0]
    if change == "boolean_forecast":
        row["forecast"] = False
    elif change == "unknown_forecast":
        row["forecast"] = 2
    elif change == "missing_available":
        body["data"][-1].pop("available")
    elif change == "actual_available":
        row["available"] = 0
    elif change == "null_available":
        body["data"][-1]["available"] = None
    elif change == "null_demand":
        row["demand"] = None
    elif change == "string_capacity":
        row["capacity"] = "1"
    elif change == "flag_type":
        row["dstFlag"] = "N"
    elif change == "epoch":
        row["epoch"] += 1
    elif change == "interval":
        row["interval"] = 5
    elif change == "hour":
        row["hourEnding"] = 1
    elif change == "duplicate":
        body["data"].insert(0, row)
    elif change == "future_actual":
        body["lastUpdated"] = "2026-09-04 20:00:00-0500"
    elif change == "outlook_end":
        body["forecast"][0]["deliveryDateHrEnd"] = "2026-09-04 00:00:00"
    elif change == "outlook_begin":
        body["forecast"][0]["deliveryDateHrBegin"] = "2026-09-14 00:00:00"
    elif change == "outlook_day":
        body["forecast"][0]["deliveryDate"] = "2026-09-04"
    elif change == "outlook_hour":
        body["forecast"][-1]["hourEnding"] = 0
    elif change == "outlook_flag":
        body["forecast"][0]["dstFlag"] = 0
    elif change == "extra":
        body["forecast"][0]["computed"] = 1
    with pytest.raises(SchemaMismatchError):
        decode_supply_demand(payload(json.dumps(body).encode()))


def test_price_fall_hour_offsets_remain_distinct():
    body = json.loads(PRICES)
    body["rtSppData"] = body["rtSppData"][:2]
    body["damSppData"] = []
    body["lastUpdated"] = "2026-11-01 02:00:00-0600"
    for row, text in zip(
        body["rtSppData"],
        ["2026-11-01 01:15:00-0500", "2026-11-01 01:15:00-0600"],
        strict=True,
    ):
        row.update(
            timestamp=text,
            intervalEnding="01:15",
            interval=int(
                datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S%z").timestamp()
                * 1000
            ),
            dstFlag="uninterpreted",
        )
    result = decode_system_prices(payload(json.dumps(body).encode()))
    assert result.real_time[1].interval - result.real_time[0].interval == 3600000
    assert result.real_time[0].dstFlag == "uninterpreted"


def test_each_method_captures_once_without_authentication():
    requests = []

    def handler(request):
        requests.append(request)
        assert "Authorization" not in request.headers
        assert "Ocp-Apim-Subscription-Key" not in request.headers
        assert not request.url.query
        return httpx.Response(
            200,
            content={SYSTEM_PRICES_URL: PRICES, SUPPLY_DEMAND_URL: SUPPLY}[
                str(request.url)
            ],
        )

    with AdditionalDashboardClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        assert not requests
        assert client.system_prices().real_time
        assert client.supply_demand().data
    assert len(requests) == 2


def test_fixture_provenance_hashes():
    evidence = json.loads(
        (
            ROOT / "docs/evidence/additional-dashboard-fixture-provenance.json"
        ).read_text()
    )
    for record in evidence["fixtures"]:
        assert (
            hashlib.sha256((ROOT / record["fixture"]).read_bytes()).hexdigest()
            == record["fixture_sha256"]
        )
