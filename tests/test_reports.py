"""Exercise generated field contracts and complete bounded query iteration."""

import datetime
import json
from pathlib import Path

import httpx
import pytest

from tinyercot.public import (
    DAM_PRICES,
    RT_PRICES,
    SYSTEM_LOAD,
    Credentials,
    LimitError,
    ReportsClient,
    SchemaMismatchError,
    StreamingLimits,
)
from tinyercot.public.api import TOKEN_URL

FIXTURES = Path(__file__).parent / "fixtures/public"
CREDS = Credentials("synthetic", "synthetic", "synthetic")


@pytest.mark.parametrize(
    "endpoint,fixture,date_field",
    [
        (RT_PRICES, "rt-prices", "deliveryDate"),
        (SYSTEM_LOAD, "system-load", "operatingDay"),
    ],
)
@pytest.mark.parametrize("period", ["current", "oldest"])
def test_observed_new_contracts(endpoint, fixture, date_field, period):
    raw = (FIXTURES / f"{fixture}-{period}.json").read_bytes()

    def handler(request):
        if str(request.url) == TOKEN_URL:
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        assert request.url.path.endswith(endpoint.path)
        return httpx.Response(200, content=raw)

    with ReportsClient(
        CREDS,
        limits=StreamingLimits(min_interval=0),
        transport=httpx.MockTransport(handler),
    ) as client:
        page = client.page(endpoint, size=2)
        assert page.rows and isinstance(page.rows[0], endpoint.row_model)
        assert isinstance(getattr(page.rows[0], date_field), datetime.date)
        assert page.raw == raw


def test_all_pages_can_stream_past_old_limits_and_filter_types_are_encoded():
    calls = []

    def handler(request):
        calls.append(request)
        if str(request.url) == TOKEN_URL:
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        params = request.url.params
        assert params["deliveryDateFrom"] == "2026-09-04"
        assert params["DSTFlag"] == "false"
        assert params["hourEnding"] == "24:00"
        body = json.loads((FIXTURES / "dam-oldest.json").read_text())
        number = int(params["page"])
        body["_meta"].update(
            currentPage=number, totalPages=125, totalRecords=125, pageSize=1
        )
        body["data"][0][3] = number
        return httpx.Response(200, json=body)

    with ReportsClient(
        CREDS,
        limits=StreamingLimits(max_requests=None, min_interval=0),
        transport=httpx.MockTransport(handler),
    ) as client:
        rows = client.iter_rows(
            DAM_PRICES,
            filters={
                "deliveryDateFrom": datetime.date(2026, 9, 4),
                "DSTFlag": False,
                "hourEnding": "24:00",
            },
            size=1,
            max_pages=None,
            max_rows=None,
        )
        assert sum(1 for _ in rows) == 125
        assert len(calls) == 126


@pytest.mark.parametrize(
    "filters",
    [
        {"unknown": 1},
        {"DSTFlag": "false"},
        {"deliveryDateFrom": "2026-09-04"},
        {"settlementPointPriceFrom": float("nan")},
        {"settlementPointPriceFrom": 5, "settlementPointPriceTo": 1},
    ],
)
def test_invalid_filters_fail_before_authentication(filters):
    def handler(request):
        pytest.fail("Invalid filters reached transport")

    with (
        ReportsClient(CREDS, transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ValueError),
    ):
        client.page(DAM_PRICES, filters=filters)


@pytest.mark.parametrize(
    "fault",
    [
        "page_budget",
        "row_budget",
        "totals",
        "repeat",
        "wrong_type",
        "short_total",
        "long_total",
    ],
)
def test_iteration_never_silently_returns_partial_or_changed_queries(fault):
    def handler(request):
        if str(request.url) == TOKEN_URL:
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        body = json.loads((FIXTURES / "dam-oldest.json").read_text())
        number = int(request.url.params["page"])
        body["_meta"].update(
            currentPage=number, totalPages=2, totalRecords=2, pageSize=1
        )
        if fault != "repeat":
            body["data"][0][3] = number
        if fault == "totals" and number == 2:
            body["_meta"]["totalRecords"] = 3
        if fault == "wrong_type":
            body["data"][0][4] = 0
        if fault == "short_total":
            body["_meta"]["totalRecords"] = 1
        if fault == "long_total":
            body["_meta"]["totalRecords"] = 3
        return httpx.Response(200, json=body)

    with ReportsClient(
        CREDS,
        limits=StreamingLimits(min_interval=0),
        transport=httpx.MockTransport(handler),
    ) as client:
        expected = LimitError if fault.endswith("budget") else SchemaMismatchError
        with pytest.raises(expected):
            list(
                client.iter_rows(
                    DAM_PRICES,
                    size=1,
                    max_pages=1 if fault == "page_budget" else None,
                    max_rows=1 if fault == "row_budget" else None,
                )
            )
