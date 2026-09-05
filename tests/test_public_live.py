import datetime
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from tinyercot.public import SchemaMismatchError, WebClient
from tinyercot.public._http import Payload, Receipt
from tinyercot.public.live import EsrRow, decode_esr

RAW = (Path(__file__).parent / "fixtures/public/esr-live.json").read_bytes()
RECEIPT = Receipt(
    "https://www.ercot.com/api/1/services/read/dashboards/energy-storage-resources.json",
    datetime.datetime(2026, 9, 5, 20, 27, 20, tzinfo=datetime.UTC),
    hashlib.sha256(RAW).hexdigest(),
    len(RAW),
)


def test_real_feed_fixture_and_freshness():
    result = decode_esr(Payload(RAW, RECEIPT))
    assert len(result.current_day.data) == 4 and len(result.previous_day.data) == 4
    assert not result.is_stale()
    assert result.is_stale(max_age=datetime.timedelta(seconds=1))
    assert result.current_day.data[0].utc == datetime.datetime(
        2026, 9, 5, 5, tzinfo=datetime.UTC
    )
    assert result.current_day.data[0].dstFlag == "N"
    assert result.current_day.dayDate == "2026-09-05 03:00:00-0500"


@pytest.mark.parametrize(
    "timestamp, epoch",
    [
        ("2026-11-01 01:30:00-0500", 1793514600000),
        ("2026-11-01 01:30:00-0600", 1793518200000),
        ("2026-03-08 01:55:00-0600", 1772956500000),
        ("2026-03-08 03:00:00-0500", 1772956800000),
    ],
)
def test_offset_epoch_disambiguate_dst_without_guessing_flag(timestamp, epoch):
    row = EsrRow(
        tagCLastTime=timestamp[:19],
        timestamp=timestamp,
        epoch=epoch,
        dstFlag="unknown-meaning",
        totalCharging=-1,
        totalDischarging=2,
        netOutput=1,
    )
    assert int(row.utc.timestamp() * 1000) == epoch
    assert row.dstFlag == "unknown-meaning"


@pytest.mark.parametrize(
    "change",
    ["epoch", "offset", "flag_type", "missing", "extra", "duplicate", "null", "local"],
)
def test_feed_drift_and_conflicting_times_fail_closed(change):
    body = json.loads(RAW)
    row = body["currentDay"]["data"][0]
    if change == "epoch":
        row["epoch"] += 1
    elif change == "offset":
        row["timestamp"] = row["timestamp"].replace("-0500", "-0600")
    elif change == "flag_type":
        row["dstFlag"] = False
    elif change == "missing":
        row.pop("totalCharging")
    elif change == "extra":
        row["new"] = 1
    elif change == "duplicate":
        body["currentDay"]["data"].append(row)
    elif change == "null":
        row["netOutput"] = None
    elif change == "local":
        row["tagCLastTime"] = "2026-09-05 02:00:00"
    with pytest.raises(SchemaMismatchError):
        decode_esr(Payload(json.dumps(body).encode(), RECEIPT))


def test_web_fetch_is_anonymous_and_only_one_capture():
    calls = []

    def handler(request):
        calls.append(request)
        assert "Authorization" not in request.headers
        assert "Ocp-Apim-Subscription-Key" not in request.headers
        return httpx.Response(200, content=RAW)

    with WebClient(transport=httpx.MockTransport(handler)) as client:
        assert client.esr().current_day.data
        assert len(calls) == 1
