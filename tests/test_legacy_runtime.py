import asyncio
import datetime
import inspect
import json
from decimal import Decimal
from typing import ClassVar

import httpx
import pandas as pd
import pytest
from aiolimiter import AsyncLimiter
from pydantic import BaseModel, ValidationError

from tinyercot import _client as client
from tinyercot import _generated as generated
from tools.generate_client import load_response_fields, parse_openapi, pascal, safe_name

ENDPOINTS, _ = parse_openapi()
FIELDS = load_response_fields()
VALUES = {
    "VARCHAR": "example",
    "INTEGER": 1,
    "DOUBLE": "12.25",
    "BOOLEAN": False,
    "DATE": "2026-01-01",
    "DATETIME": "2026-01-01T01:00:00",
    "TIME": "01:00:00",
}


def sample(ep):
    return [VALUES[kind] for kind in FIELDS[ep].values()]


@pytest.fixture
def transport(monkeypatch):
    client.configure(
        username="synthetic", password="synthetic", subscription_key="synthetic"
    )
    monkeypatch.setattr(client, "_token", lambda: "synthetic-token")
    monkeypatch.setattr(client, "_rate_limiter", AsyncLimiter(1000, 1))

    def install(handler):
        sync = httpx.Client(transport=httpx.MockTransport(handler))
        monkeypatch.setattr(client, "_client", sync)
        return sync

    return install


@pytest.mark.parametrize("ep", ENDPOINTS)
def test_all_legacy_paths_forward_queries_and_paginate(ep, transport, monkeypatch):
    product, suffix = ep.split("/")
    facade = getattr(generated, safe_name(product))
    method = safe_name(suffix)
    calls = []

    def handler(request):
        assert request.url.path == "/api/public-reports/" + ep
        assert request.headers["Authorization"] == "Bearer synthetic-token"
        calls.append(dict(request.url.params))
        return httpx.Response(
            200, json={"_meta": {"totalPages": 2}, "data": [sample(ep)]}
        )

    response_type = getattr(facade, pascal(suffix) + "Response")
    # Distinct sentinels detect dropped or swapped filter arguments on every method.
    kwargs = {name: f"value-{i}" for i, name in enumerate(ENDPOINTS[ep][0])}
    kwargs.update(page=7, size=3)
    with transport(handler):
        response = getattr(facade, method)(**kwargs)
        assert type(response) is response_type
        assert calls == [{k: str(v) for k, v in kwargs.items()}]
        filters = {k: v for k, v in kwargs.items() if k != "page"}
        expected = [
            {**{k: str(v) for k, v in filters.items()}, "page": str(p)} for p in (1, 2)
        ]
        calls.clear()
        rows = list(getattr(facade, method + "_iter")(**filters))
        assert len(rows) == 2 and calls == expected
        assert all(type(row) is getattr(facade, pascal(suffix) + "Row") for row in rows)
        calls.clear()
        frame = getattr(facade, method + "_df")(**filters)
        assert len(frame) == 2 and frame.index.tolist() == [0, 1] and calls == expected

        async def run():
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as async_client:
                monkeypatch.setattr(client, "_async_client", async_client)
                calls.clear()
                async_rows = [
                    row
                    async for row in getattr(facade, method + "_iter_async")(**filters)
                ]
                assert async_rows == rows and calls == expected
                calls.clear()
                async_frame = await getattr(facade, method + "_df_async")(**filters)
                pd.testing.assert_frame_equal(async_frame, frame)
                assert calls == expected

        asyncio.run(run())


def test_none_omission_missing_page_count_and_positional_decoding(
    transport, monkeypatch
):
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "fields": [{"name": "b"}, {"name": "a"}],
                "data": [["B", "A", "ignored"]],
            },
        )

    with transport(handler):
        result = client._get(
            "synthetic", schema={"a": "VARCHAR", "b": "VARCHAR"}, size=None
        )
        assert result["data"] == [{"a": "B", "b": "A"}]
        assert calls == [{}]

        async def run():
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as async_client:
                monkeypatch.setattr(client, "_async_client", async_client)
                assert (
                    await client._aget(
                        "synthetic", schema={"a": "VARCHAR", "b": "VARCHAR"}
                    )
                    == result
                )

        asyncio.run(run())

    calls.clear()

    def one_page(request):
        calls.append(dict(request.url.params))
        return httpx.Response(
            200, json={"data": [sample("np4-190-cd/dam_stlmnt_pnt_prices")]}
        )

    with transport(one_page):
        assert len(list(generated.np4_190_cd.dam_stlmnt_pnt_prices_iter(size=1))) == 1
        assert calls == [{"size": "1", "page": "1"}]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 500])
def test_json_error_status_remains_empty_legacy_response(
    status, transport, monkeypatch
):
    def handler(request):
        return httpx.Response(status, json={"error": "synthetic"})

    with transport(handler):
        response = generated.np4_190_cd.dam_stlmnt_pnt_prices()
        assert response.data == [] and response.model_extra == {"error": "synthetic"}
        assert response.to_df().columns.tolist() == []

        async def run():
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as async_client:
                monkeypatch.setattr(client, "_async_client", async_client)
                rows = [
                    r
                    async for r in generated.np4_190_cd.dam_stlmnt_pnt_prices_iter_async()
                ]
                assert rows == []

        asyncio.run(run())


@pytest.mark.parametrize("failure", ["transport", "json", "validation"])
def test_legacy_errors_propagate(failure, transport, monkeypatch):
    expected = {
        "transport": httpx.ReadTimeout,
        "json": json.JSONDecodeError,
        "validation": ValidationError,
    }[failure]

    def handler(request):
        if failure == "transport":
            raise httpx.ReadTimeout("synthetic", request=request)
        if failure == "json":
            return httpx.Response(200, text="not json")
        return httpx.Response(200, json={"data": [[None]]})

    with transport(handler):
        with pytest.raises(expected):
            generated.np4_190_cd.dam_stlmnt_pnt_prices()

        async def run():
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as async_client:
                monkeypatch.setattr(client, "_async_client", async_client)
                with pytest.raises(expected):
                    await generated.np4_190_cd.dam_stlmnt_pnt_prices_df_async()

        asyncio.run(run())


def test_async_429_budget_and_terminal_sleep(transport, monkeypatch):
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            429, headers={"Retry-After": "120"}, json={"error": "synthetic"}
        )

    async def sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(client.asyncio, "sleep", sleep)

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as async_client:
            monkeypatch.setattr(client, "_async_client", async_client)
            with pytest.raises(httpx.HTTPStatusError, match="after 5 retries"):
                await client._aget("synthetic")

    asyncio.run(run())
    assert len(calls) == 5 and sleeps == [2, 4, 8, 16, 32]


def test_configure_replaces_fields_environment_fallback_and_token_cache(monkeypatch):
    for name, value in [
        ("USERNAME", "env-user"),
        ("PASSWORD", "env-pass"),
        ("SUBSCRIPTION_KEY", "env-key"),
    ]:
        monkeypatch.setenv("ERCOT_" + name, value)
    client.configure(
        username="configured", password="configured", subscription_key="configured"
    )
    client._tok_cache[()] = "old-token"
    client.configure(username="new-user")
    assert client._resolve_creds() == ("new-user", "env-pass", "env-key")
    assert len(client._tok_cache) == 0
    client.configure(username="", password="", subscription_key="")
    assert client._resolve_creds() == ("env-user", "env-pass", "env-key")
    monkeypatch.delenv("ERCOT_USERNAME")
    with pytest.raises(KeyError, match="ERCOT_USERNAME"):
        client._resolve_creds()
    assert client._tok_cache.ttl == 3600 and client._tok_cache.maxsize == 1


def test_auth_error_none_is_cached(monkeypatch):
    calls = []
    client.configure(
        username="synthetic", password="synthetic", subscription_key="synthetic"
    )

    def handler(request):
        calls.append(request)
        return httpx.Response(400, json={"error": "invalid_grant"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as sync:
        monkeypatch.setattr(client, "_client", sync)
        assert client._token() is None and client._token() is None
        assert len(calls) == 1
        client.configure(
            username="synthetic", password="synthetic", subscription_key="synthetic"
        )
        assert client._token() is None and len(calls) == 2


def test_envelope_aliases_defaults_extras_and_dataframe_types():
    class Row(BaseModel):
        day: datetime.date
        stamp: datetime.datetime
        amount: Decimal
        count: int
        flag: bool

    class Response(client.ErcotResponse[Row]):
        _schema: ClassVar[dict] = {
            "day": "DATE",
            "stamp": "DATETIME",
            "amount": "DOUBLE",
            "count": "INTEGER",
            "flag": "BOOLEAN",
        }

    first, second = Response(), Response()
    first.meta["x"] = 1
    first.report["x"] = 1
    first.fields.append({})
    first.links["x"] = 1
    assert second.model_dump() == {
        "meta": {},
        "report": {},
        "fields": [],
        "data": [],
        "links": {},
    }
    assert second.to_df().empty and list(second.to_df().columns) == []
    row = Row(
        day="2026-01-01",
        stamp="2026-01-01T00:00:00",
        amount="42.125",
        count=1,
        flag=False,
        extra="ignored",
    )
    response = Response.model_validate(
        {"_meta": {"totalPages": 1}, "_links": [], "extra": 1, "data": [row]}
    )
    assert response.meta == {"totalPages": 1} and response.links == []
    assert response.model_extra == {"extra": 1} and row.model_extra is None
    assert Response(meta={"named": True}, links={}).meta == {"named": True}
    frame = response.to_df()
    assert frame.iloc[0]["day"] == datetime.date(2026, 1, 1)
    assert str(frame.stamp.dtype) == "datetime64[ns]"
    assert str(frame.amount.dtype) == "float64" and frame.amount[0] == 42.125
    assert str(frame["count"].dtype) == "Int64"
    assert str(frame.flag.dtype) == "bool" and not frame.flag[0]
    assert all(
        p.default is None
        for p in inspect.signature(
            generated.np4_190_cd.dam_stlmnt_pnt_prices
        ).parameters.values()
    )
