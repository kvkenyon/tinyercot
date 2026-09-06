"""Test raw ESR contracts with synthetic envelopes, never live row evidence."""

import copy
import json
from pathlib import Path

import httpx
import pytest

from tinyercot.public._http import AuthenticationError, Limits, SchemaMismatchError
from tinyercot.public.api import Credentials
from tinyercot.public.esr_api import BASE, PATH, ESRAPIClient, RawESRPage


def raw_envelope():
    return {
        "_meta": {"currentPage": 1, "pageSize": 1, "totalPages": 1, "totalRecords": 1},
        "report": {"reportProductId": "rptesr-m"},
        "fields": [{"name": "unverified", "dataType": "VARCHAR"}],
        "data": {},
    }


def client_for(body=None, status=200, media="application/json"):
    calls = []

    def handle(request):
        calls.append(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        return httpx.Response(
            status,
            content=json.dumps(body if body is not None else raw_envelope()).encode(),
            headers={"content-type": media},
        )

    return ESRAPIClient(
        Credentials("synthetic", "synthetic", "synthetic"),
        limits=Limits(min_interval=0, attempts=1),
        transport=httpx.MockTransport(handle),
    ), calls


def test_direct_module_raw_current_route_and_unknown_schema():
    client, calls = client_for()
    with client:
        page = client.current()
        assert isinstance(page, RawESRPage)
        assert page.row_schema == "unknown"
        assert page.envelope["data"] == {}
        assert str(calls[-1].url).startswith(BASE + PATH)
        assert dict(calls[-1].url.params) == {
            "page": "1",
            "size": "1",
            "sort": "AGCExecTime",
            "dir": "desc",
        }
        assert "unverified" not in repr(page)
        assert len(client.exchanges) == 1


def test_unrecognized_fields_remain_raw_not_typed():
    body = raw_envelope()
    body["fields"] = [{"name": "futureField", "dataType": "UNKNOWN_TYPE"}]
    body["data"] = [["raw"]]
    client, _ = client_for(body)
    with client:
        assert client.current().row_schema == "unknown"


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b.pop("fields"),
        lambda b: b.update(fields=[]),
        lambda b: b.update(fields=[{"name": "same"}, {"name": "same"}]),
        lambda b: b.update(data=[[1, 2]]),
        lambda b: b.update(data=[[1], [2]]),
        lambda b: b.update(data="not data"),
        lambda b: b.update(report=[]),
        lambda b: b["_meta"].update(currentPage=True),
        lambda b: b["_meta"].update(currentPage=2),
        lambda b: b["_meta"].update(pageSize=1001),
    ],
)
def test_envelope_mismatch_fails_closed_with_receipt(change):
    body = copy.deepcopy(raw_envelope())
    change(body)
    client, _ = client_for(body)
    with client:
        with pytest.raises(SchemaMismatchError):
            client.current()
        assert client.exchanges[-1].complete


def test_no_service_fallback_after_subscription_denial():
    client, calls = client_for(status=401)
    with client:
        with pytest.raises(AuthenticationError):
            client.current()
        assert len(calls) == 2
        assert client.exchanges[-1].receipt.status == 401


def test_esr_bad_content_type():
    client, _ = client_for(media="text/html")
    with client, pytest.raises(SchemaMismatchError, match="content type"):
        client.current()


@pytest.mark.parametrize("size", [0, -1, True, 1001, 1.5])
def test_size_checks_precede_authentication(size):
    client, calls = client_for()
    with client, pytest.raises(ValueError):
        client.current(size=size)
    assert not calls


def test_primary_esr_schema_has_no_concrete_rows():
    source = json.loads(
        (
            Path(__file__).parent / "fixtures/public/esr_api/source-contract.json"
        ).read_text()
    )
    assert source["operation"]["method"] == "GET"
    assert source["operation"]["urlTemplate"] == PATH
    assert source["schemas"]["Report"]["properties"]["data"] == {"type": "object"}
    assert "AGCExecTimeFrom" in {q["name"] for q in source["operation"]["query"]}
