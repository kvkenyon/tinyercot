import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from tinyercot.public._http import Limits, Payload, Receipt, SchemaMismatchError
from tinyercot.public.aggregate_dashboards import (
    DC_TIE_FLOWS_URL,
    GENERATION_OUTAGES_URL,
    AggregateDashboardClient,
    decode_dc_tie_flows,
    decode_generation_outages,
)

FIXTURES = Path(__file__).parent / "fixtures/public"
OUTAGES = (FIXTURES / "generation-outages-live.json").read_bytes()
TIES = (FIXTURES / "dc-tie-flows-live.json").read_bytes()


def payload(raw):
    return Payload(
        raw,
        Receipt(
            GENERATION_OUTAGES_URL,
            datetime.datetime(2026, 9, 6, 0, 35, tzinfo=datetime.UTC),
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        ),
    )


def test_outages_retain_current_previous_metadata_and_epoch_keys():
    result = decode_generation_outages(payload(OUTAGES))
    assert len(result.current) == 4
    assert len(result.previous) == 4
    assert result.current_outages == 15206
    assert result.current[-1].source_epoch == "1788654660000"
    assert result.current[-1].row.combined.unplanned == 14725
    assert result.current[-1].row.combined.planned == 481
    assert result.current[-1].row.dispatchable.total == 9812
    assert result.current[-1].row.renewable.total == 5394
    assert result.current[-1].row.deliveryTime == "2026-09-05 19:31:00-0500"
    assert result.current[-1].row.dstFlag == "N"
    assert result.days.current == ("2026-09-05",)
    assert len(result.days.previous) == 6
    assert result.resource_types == ("Dispatchable", "Renewable")
    assert result.raw == OUTAGES
    assert not result.is_stale()


def test_dc_ties_retain_signed_flows_and_frequency_precision():
    result = decode_dc_tie_flows(payload(TIES))
    assert len(result.rows) == 4
    row = result.rows[0]
    assert row.currentFrequency == Decimal("59.993")
    assert row.currentSystemInertia == 323984
    assert row.dcE == 0 and row.dcN == -218 and row.dcL == 70 and row.dcR == 0
    assert row.timestamp == "2026-09-05 00:00:00-0500"
    assert row.epoch == 1788584400000
    assert row.interval == "00:00:00" and row.dstFlag == "N"
    assert result.raw == TIES
    assert not result.is_stale()


@pytest.mark.parametrize("bad", [None, True, "1", 1.5, {}, []])
def test_unknown_outage_numeric_types_fail_closed(bad):
    body = json.loads(OUTAGES)
    next(iter(body["current"].values()))["Combined"]["planned"] = bad
    with pytest.raises(SchemaMismatchError):
        decode_generation_outages(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "offset",
        "extra",
        "missing",
        "new_type",
        "day",
        "duplicate_day",
        "section",
        "future",
        "reverse",
        "total_type",
    ],
)
def test_outage_schema_and_time_drift_fail_closed(change):
    body = json.loads(OUTAGES)
    key = next(iter(body["current"]))
    row = body["current"][key]
    if change == "epoch":
        body["current"][str(int(key) + 1)] = body["current"].pop(key)
    elif change == "offset":
        row["deliveryTime"] = row["deliveryTime"].replace("-0500", "-0600")
    elif change == "extra":
        row["Combined"]["unknown"] = 1
    elif change == "missing":
        row.pop("Renewable")
    elif change == "new_type":
        body["types"].append("Unknown Resource")
    elif change == "day":
        body["days"]["current"] = ["2026-09-03"]
    elif change == "duplicate_day":
        body["days"]["previous"].append(body["days"]["current"][0])
    elif change == "section":
        body["current"] = []
    elif change == "future":
        body["lastUpdated"] = "2026-09-04 19:31:00-0500"
    elif change == "reverse":
        body["current"] = dict(reversed(list(body["current"].items())))
    elif change == "total_type":
        body["currentOutages"] = True
    with pytest.raises(SchemaMismatchError):
        decode_generation_outages(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "field,bad",
    [
        ("currentFrequency", None),
        ("currentFrequency", "60"),
        ("currentFrequency", True),
        ("currentFrequency", float("nan")),
        ("currentFrequency", float("inf")),
        ("currentSystemInertia", None),
        ("dcE", "1"),
        ("dcN", 1.5),
        ("dcL", True),
        ("dcR", None),
        ("epoch", "1788584400000"),
        ("dstFlag", False),
    ],
)
def test_dc_tie_numeric_and_label_types_fail_closed(field, bad):
    body = json.loads(TIES)
    body["data"][0][field] = bad
    with pytest.raises(SchemaMismatchError):
        decode_dc_tie_flows(payload(json.dumps(body).encode()))


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "interval",
        "offset",
        "extra",
        "missing",
        "duplicate",
        "reverse",
        "future",
        "data_type",
    ],
)
def test_dc_tie_schema_and_temporal_drift_fail_closed(change):
    body = json.loads(TIES)
    row = body["data"][0]
    if change == "epoch":
        row["epoch"] += 1
    elif change == "interval":
        row["interval"] = "01:00:00"
    elif change == "offset":
        row["timestamp"] = row["timestamp"].replace("-0500", "-0600")
    elif change == "extra":
        row["unknown"] = 1
    elif change == "missing":
        row.pop("dcR")
    elif change == "duplicate":
        body["data"].insert(0, row)
    elif change == "reverse":
        body["data"].reverse()
    elif change == "future":
        body["lastUpdated"] = "2026-09-04 19:32:10-0500"
    elif change == "data_type":
        body["data"] = {}
    with pytest.raises(SchemaMismatchError):
        decode_dc_tie_flows(payload(json.dumps(body).encode()))


def test_outage_dst_repeated_local_hour_remains_two_distinct_instants():
    body = json.loads(OUTAGES)
    original = next(iter(body["current"].values()))
    body["current"] = {}
    body["previous"] = {}
    body["days"] = {"current": ["2026-11-01"], "previous": []}
    body["lastUpdated"] = "2026-11-01 01:30:00-0600"
    for text in ["2026-11-01 01:30:00-0500", "2026-11-01 01:30:00-0600"]:
        stamp = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S%z")
        body["current"][str(int(stamp.timestamp() * 1000))] = {
            **original,
            "deliveryTime": text,
            "dstFlag": "unknown-meaning",
        }
    result = decode_generation_outages(payload(json.dumps(body).encode()))
    assert result.current[0].timestamp < result.current[1].timestamp
    assert result.current[0].row.dstFlag == "unknown-meaning"


def test_outage_totals_remain_source_values_without_recalculation():
    body = json.loads(OUTAGES)
    next(iter(body["current"].values()))["Combined"]["total"] = 123
    result = decode_generation_outages(payload(json.dumps(body).encode()))
    assert result.current[0].row.combined.total == 123


def test_public_aggregate_methods_each_make_one_anonymous_capture():
    requests = []

    def handler(request):
        requests.append(request)
        assert "Authorization" not in request.headers
        assert "Ocp-Apim-Subscription-Key" not in request.headers
        assert not request.url.query
        return httpx.Response(
            200,
            content={GENERATION_OUTAGES_URL: OUTAGES, DC_TIE_FLOWS_URL: TIES}[
                str(request.url)
            ],
        )

    with AggregateDashboardClient(
        limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        assert requests == []
        assert client.generation_outages().current
        assert client.dc_tie_flows().rows
    assert len(requests) == 2


def test_aggregate_fixture_provenance_hashes():
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads(
        (root / "docs/evidence/aggregate-dashboard-fixture-provenance.json").read_text()
    )
    for record in evidence["fixtures"]:
        assert (
            hashlib.sha256((root / record["fixture"]).read_bytes()).hexdigest()
            == record["fixture_sha256"]
        )
