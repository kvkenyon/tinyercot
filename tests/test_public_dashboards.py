import datetime
import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from tinyercot.public._http import (
    AccessDeniedError,
    Limits,
    Payload,
    Receipt,
    SchemaMismatchError,
)
from tinyercot.public.dashboards import (
    DAILY_PRC_URL,
    FUEL_MIX_URL,
    DashboardClient,
    decode_fuel_mix,
    decode_grid_conditions,
)

FIXTURES = Path(__file__).parent / "fixtures/public"
FUEL = (FIXTURES / "fuel-mix-live.json").read_bytes()
PRC = (FIXTURES / "daily-prc-live.json").read_bytes()


def payload(raw, url=FUEL_MIX_URL):
    return Payload(
        raw,
        Receipt(
            url,
            datetime.datetime(2026, 9, 6, 0, 27, tzinfo=datetime.UTC),
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        ),
    )


def test_fuel_mix_retains_exact_numbers_capacity_and_source_time():
    snapshot = decode_fuel_mix(payload(FUEL))
    assert len(snapshot.rows) == 8
    assert snapshot.rows[0].generation.natural_gas == Decimal("30015.6174087524466")
    assert snapshot.rows[0].generation.power_storage == Decimal("-1307.51257324219")
    assert snapshot.monthly_capacity.power_storage == 20654
    assert snapshot.rows[0].source_day == "2026-09-04"
    assert snapshot.rows[0].source_timestamp == "2026-09-04 00:00:00-0500"
    assert snapshot.rows[0].timestamp.utcoffset() == datetime.timedelta(hours=-5)
    assert snapshot.source_last_updated == "2026-09-05 19:21:00-0500"
    assert snapshot.raw == FUEL
    assert not snapshot.is_stale()
    assert snapshot.is_stale(max_age=datetime.timedelta(minutes=1))
    assert replace(
        snapshot,
        last_updated=snapshot.receipt.retrieved_at + datetime.timedelta(seconds=1),
    ).is_stale()
    with pytest.raises(ValueError):
        snapshot.is_stale(max_age=datetime.timedelta(seconds=-1))


def test_grid_conditions_retains_status_and_prc_time_evidence():
    snapshot = decode_grid_conditions(payload(PRC, DAILY_PRC_URL))
    assert len(snapshot.rows) == 4
    assert snapshot.current_condition.state == "normal"
    assert (
        snapshot.current_condition.condition_note
        == "There is enough power for current demand."
    )
    assert snapshot.current_condition.prc_value == "11,013"
    assert snapshot.current_condition.index == 7001
    assert snapshot.rows[-1].prc == 11013
    assert snapshot.rows[-1].epoch == snapshot.current_condition.datetime * 1000
    assert snapshot.rows[-1].dstFlag == "N"
    assert snapshot.raw == PRC
    assert not snapshot.is_stale()


@pytest.mark.parametrize(
    "bad", [None, True, "12.3", [], {}, float("nan"), float("inf")]
)
def test_fuel_mix_rejects_unobserved_numeric_types(bad):
    body = json.loads(FUEL)
    first = next(iter(next(iter(body["data"].values())).values()))
    first["Wind"]["gen"] = bad
    with pytest.raises(SchemaMismatchError):
        decode_fuel_mix(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "missing",
        "new_fuel",
        "nested",
        "capacity",
        "wrong_day",
        "bad_offset",
        "future",
        "reverse",
        "data_type",
    ],
)
def test_fuel_mix_rejects_schema_and_temporal_drift(change):
    body = json.loads(FUEL)
    day = next(iter(body["data"]))
    observations = body["data"][day]
    first_time = next(iter(observations))
    first = observations[first_time]
    if change == "extra":
        body["unknown"] = []
    elif change == "missing":
        first.pop("Solar")
    elif change == "new_fuel":
        first["New Fuel"] = {"gen": 1}
    elif change == "nested":
        first["Wind"]["forecast"] = 1
    elif change == "capacity":
        body["monthlyCapacity"]["Wind"] = "1"
    elif change == "wrong_day":
        body["data"]["2026-09-03"] = body["data"].pop(day)
    elif change == "bad_offset":
        observations[first_time.replace("-0500", "-0600")] = observations.pop(
            first_time
        )
    elif change == "future":
        body["lastUpdated"] = "2026-09-03 19:21:00-0500"
    elif change == "reverse":
        body["data"][day] = dict(reversed(list(observations.items())))
    elif change == "data_type":
        body["data"] = []
    with pytest.raises(SchemaMismatchError):
        decode_fuel_mix(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "interval",
        "offset",
        "boolean",
        "string",
        "null",
        "extra",
        "missing",
        "status",
        "condition_time",
        "duplicate",
        "reverse",
        "rows_type",
    ],
)
def test_prc_rejects_schema_and_temporal_drift(change):
    body = json.loads(PRC)
    row = body["data"][0]
    if change == "epoch":
        row["epoch"] += 1
    elif change == "interval":
        row["interval"] = "12:00:00"
    elif change == "offset":
        row["timestamp"] = row["timestamp"].replace("-0500", "-0600")
    elif change == "boolean":
        row["prc"] = True
    elif change == "string":
        row["prc"] = "11238"
    elif change == "null":
        row["prc"] = None
    elif change == "extra":
        row["unknown"] = 1
    elif change == "missing":
        row.pop("dstFlag")
    elif change == "status":
        body["current_condition"]["state"] = 0
    elif change == "condition_time":
        body["current_condition"]["datetime"] += 1
    elif change == "duplicate":
        body["data"].insert(0, row)
    elif change == "reverse":
        body["data"].reverse()
    elif change == "rows_type":
        body["data"] = {}
    with pytest.raises(SchemaMismatchError):
        decode_grid_conditions(payload(json.dumps(body).encode(), DAILY_PRC_URL))


def test_unknown_status_labels_are_preserved_without_inventing_enum_semantics():
    body = json.loads(PRC)
    body["current_condition"]["state"] = "new-source-state"
    body["current_condition"]["title"] = "New source title"
    body["data"][0]["dstFlag"] = "uninterpreted-source-flag"
    snapshot = decode_grid_conditions(payload(json.dumps(body).encode()))
    assert snapshot.current_condition.state == "new-source-state"
    assert snapshot.rows[0].dstFlag == "uninterpreted-source-flag"


@pytest.mark.parametrize(
    "timestamps",
    [
        ["2026-11-01 01:30:00-0500", "2026-11-01 01:30:00-0600"],
        ["2026-03-08 01:55:00-0600", "2026-03-08 03:00:00-0500"],
    ],
)
def test_prc_explicit_offsets_disambiguate_dst(timestamps):
    body = json.loads(PRC)
    body["data"] = []
    for text in timestamps:
        stamp = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S%z")
        body["data"].append(
            {
                "timestamp": text,
                "epoch": int(stamp.timestamp() * 1000),
                "interval": text[11:19],
                "dstFlag": "unchanged",
                "prc": 1,
            }
        )
    body["lastUpdated"] = timestamps[-1]
    body["current_condition"]["datetime"] = body["data"][-1]["epoch"] // 1000
    snapshot = decode_grid_conditions(payload(json.dumps(body).encode()))
    assert snapshot.rows[0].epoch < snapshot.rows[1].epoch


def test_public_client_captures_once_per_method_without_credentials():
    requests = []

    def handler(request):
        requests.append(request)
        assert "Authorization" not in request.headers
        assert "Ocp-Apim-Subscription-Key" not in request.headers
        assert not request.url.query
        return httpx.Response(
            200, content={FUEL_MIX_URL: FUEL, DAILY_PRC_URL: PRC}[str(request.url)]
        )

    with DashboardClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        assert requests == []
        assert client.fuel_mix().rows
        assert client.grid_conditions().rows
    assert len(requests) == 2


def test_denied_anonymous_source_does_not_retry_or_seek_credentials():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(403)

    with (
        DashboardClient(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(AccessDeniedError),
    ):
        client.grid_conditions()
    assert len(requests) == 1


def test_dashboard_fixture_hashes_match_provenance():
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads(
        (root / "docs/evidence/dashboard-fixture-provenance.json").read_text()
    )
    for record in evidence["fixtures"]:
        assert (
            hashlib.sha256((root / record["fixture"]).read_bytes()).hexdigest()
            == record["fixture_sha256"]
        )
        assert record["source_receipt"]["status"] == 200
