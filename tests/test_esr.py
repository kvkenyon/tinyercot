# ruff: noqa: SIM117, DTZ001, DTZ007
# ESR source timestamps deliberately have no encoded timezone offset.
"""Separate ESR credentials and routes, with captured API and archive contracts."""

import asyncio
import csv
import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, ESRClient, rptesr_m

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/esr"


def payload(name):
    return json.loads((INPUTS / f"{name}.json").read_text())


def test_service_credentials_are_isolated_and_esr_refreshes(monkeypatch):
    monkeypatch.setenv("ERCOT_USERNAME", "u")
    monkeypatch.setenv("ERCOT_PASSWORD", "p")
    monkeypatch.setenv("ERCOT_SUBSCRIPTION_KEY", "reports-key")
    monkeypatch.setenv("ERCOT_ESR_SUBSCRIPTION_KEY", "esr-key")
    tokens = 0
    denied = False
    seen = []

    def handler(request):
        nonlocal tokens, denied
        if "b2clogin" in request.url.host:
            tokens += 1
            return httpx.Response(200, json={"id_token": f"token{tokens}"})
        service = request.url.path.split("/")[2]
        assert request.headers["Ocp-Apim-Subscription-Key"] == (
            "esr-key" if service == "public-data" else "reports-key"
        )
        seen.append(service)
        if service == "public-data" and not denied:
            denied = True
            return httpx.Response(401)
        return httpx.Response(200, json=payload("version"))

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with Client(client=http) as reports, ESRClient(client=http) as esr:
            assert reports.version().info.version == esr.version().info.version
    assert seen == ["public-reports", "public-data", "public-data"]
    assert tokens == 3
    monkeypatch.delenv("ERCOT_ESR_SUBSCRIPTION_KEY")
    with ESRClient() as esr:
        with pytest.raises(ValueError, match="ERCOT_ESR_SUBSCRIPTION_KEY"):
            esr.version()


def test_esr_pagination_filters_and_async_share_contract():
    calls = []
    stamp = datetime(2025, 12, 4, 23, 50)

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "token"})
        assert request.url.path == "/api/public-data/rptesr-m/4_sec_esr_charging_mw"
        assert request.headers["Ocp-Apim-Subscription-Key"] == "esr"
        assert request.url.params["AGCExecTimeFrom"] == stamp.isoformat()
        assert request.url.params["DSTFlag"] == "false"
        assert request.url.params["ESRChargingMWFrom"] == "0.01"
        page = int(request.url.params.get("page", 1))
        calls.append(page)
        body = payload("sample")
        body["_meta"].update(totalPages=2, totalRecords=2, currentPage=page, pageSize=1)
        body["data"] = [body["data"][page - 1]]
        return httpx.Response(200, json=body)

    args = {
        "AGCExecTimeFrom": stamp,
        "DSTFlag": False,
        "ESRChargingMWFrom": Decimal("0.01"),
        "size": 1,
    }
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with ESRClient("u", "p", "esr", client=http) as esr:
            rows = list(esr.rptesr_m._4_sec_esr_charging_mw_iter(**args))
            assert rows[0].ESRChargingMW == Decimal("1684.38782")
            assert rows[0].AGCExecTimeUTC == datetime(2025, 12, 5, 5, 54, 58)
            assert rows[0].AGCExecTime == datetime(2025, 12, 4, 23, 54, 58)
            assert rows[0].DSTFlag is False

    async def run():
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as ahttp:
                async with ESRClient(
                    "u", "p", "esr", client=http, async_client=ahttp
                ) as esr:
                    page = await esr.rptesr_m._4_sec_esr_charging_mw_async(**args)
                    assert page.data == rows[:1]
                    assert [
                        r
                        async for r in esr.rptesr_m._4_sec_esr_charging_mw_iter_async(
                            **args
                        )
                    ] == rows

    asyncio.run(run())
    assert calls == [1, 2, 1, 1, 2]


def test_esr_metadata_download_and_empty_bundles():
    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "token"})
        assert request.url.path.startswith("/api/public-data/")
        path = request.url.path.removeprefix("/api/public-data/")
        if request.method == "POST":
            assert path == "archive/rptesr-m/download"
            assert json.loads(request.content) == {"docIds": [156101]}
            return httpx.Response(200, content=(INPUTS / "recent.zip").read_bytes())
        fixture = {
            "": "products",
            "rptesr-m": "product",
            "archive/rptesr-m": "archive",
            "bundle/rptesr-m": "bundle",
        }[path]
        return httpx.Response(200, json=payload(fixture))

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with ESRClient("u", "p", "esr", client=http) as esr:
            assert (
                esr.products()[0].emilId == esr.product("RPTESR-M").emilId == "RPTESR-M"
            )
            assert esr.archives("RPTESR-M", size=1).product.emilId == "RPTESR-M"
            assert list(esr.iter_documents("RPTESR-M", kind="bundle")) == []
            assert (
                len(
                    list(esr.rptesr_m._4_sec_esr_charging_mw_history.download([156101]))
                )
                == 75
            )


@pytest.mark.parametrize("name", ["oldest", "middle", "recent"])
def test_original_esr_archive_cells(name):
    data = (INPUTS / f"{name}.zip").read_bytes()
    with ZipFile(BytesIO(data)) as outer:
        with ZipFile(BytesIO(outer.read(outer.namelist()[0]))) as inner:
            originals = list(
                csv.DictReader(StringIO(inner.read(inner.namelist()[0]).decode()))
            )
    with ESRClient() as esr:
        rows = list(esr.rptesr_m._4_sec_esr_charging_mw_history.read(data))
    assert len(rows) == len(originals) == 75
    for row, raw in zip(rows, originals, strict=True):
        assert isinstance(row, rptesr_m._4SecEsrChargingMwRow)
        assert row.AGCExecTime == datetime.strptime(
            raw["AGC_EXEC_TIME"], "%m/%d/%Y %H:%M:%S"
        )
        assert row.AGCExecTimeUTC == datetime.strptime(
            raw["AGC_EXEC_TIME_UTC"], "%m/%d/%Y %H:%M:%S"
        )
        assert row.DSTFlag == (raw["AGC_EXEC_TIME_DST"] == "Y")
        assert row.systemDemand == Decimal(raw["SYSTEM_DEMAND"])
        assert row.ESRChargingMW == Decimal(raw["ESR_CHARGING_MW"])
