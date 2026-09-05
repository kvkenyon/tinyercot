import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from tinyercot.public import (
    AccessDeniedError,
    AuthenticationError,
    Credentials,
    Limits,
    PublicClient,
    SchemaMismatchError,
)
from tinyercot.public._http import Payload, Receipt
from tinyercot.public.api import PRICE_PATH, TOKEN_URL, decode_prices

FIXTURES = Path(__file__).parent / "fixtures/public"
CREDS = Credentials(
    "synthetic+user@example.test", "synthetic&password=+", "synthetic-key"
)


def payload(body):
    raw = json.dumps(body).encode()
    return Payload(
        raw,
        Receipt(
            "https://api.ercot.com/public-test",
            datetime.datetime.now(datetime.UTC),
            hashlib.sha256(raw).hexdigest(),
            len(raw),
        ),
    )


@pytest.mark.parametrize(
    "name", ["dam-current-page1", "dam-current-page2", "dam-oldest"]
)
def test_observed_current_and_oldest_rows_decode(name):
    body = json.loads((FIXTURES / f"{name}.json").read_text())
    response = decode_prices(payload(body), expected_page=body["_meta"]["currentPage"])
    assert response.rows and isinstance(response.rows[0].settlementPointPrice, Decimal)
    assert response.rows[0].settlementPoint == "HB_HOUSTON"
    if name == "dam-oldest":
        assert response.rows[0].deliveryDate == datetime.date(2023, 12, 13)
        assert response.rows[0].hourEnding == "24:00"


def test_reordered_fields_decode_by_declared_names():
    body = json.loads((FIXTURES / "dam-current-page1.json").read_text())
    expected = decode_prices(payload(body), expected_page=1).rows
    body["fields"].reverse()
    for row in body["data"]:
        row.reverse()
    assert decode_prices(payload(body), expected_page=1).rows == expected


@pytest.mark.parametrize(
    "change",
    [
        "missing_field",
        "extra_field",
        "duplicate_field",
        "field_type",
        "short_row",
        "long_row",
        "null",
        "extra_key",
        "bool_string",
        "numeric_string",
        "wrong_page",
        "missing_meta",
        "error",
        "not_json",
    ],
)
def test_unknown_current_shapes_fail_closed(change):
    body = json.loads((FIXTURES / "dam-current-page1.json").read_text())
    if change == "missing_field":
        body["fields"].pop()
    elif change == "extra_field":
        body["fields"].append({"name": "new", "dataType": "VARCHAR"})
    elif change == "duplicate_field":
        body["fields"].append(body["fields"][0])
    elif change == "field_type":
        body["fields"][0]["dataType"] = "VARCHAR"
    elif change == "short_row":
        body["data"][0].pop()
    elif change == "long_row":
        body["data"][0].append("extra")
    elif change == "null":
        body["data"][0][3] = None
    elif change == "bool_string":
        body["data"][0][4] = "false"
    elif change == "numeric_string":
        body["data"][0][3] = "28.76"
    elif change == "extra_key":
        body["data"][0] = {
            **dict(
                zip([f["name"] for f in body["fields"]], body["data"][0], strict=True)
            ),
            "new": 1,
        }
    elif change == "wrong_page":
        body["_meta"]["currentPage"] = 2
    elif change == "missing_meta":
        body.pop("_meta")
    elif change == "error":
        body = {"error": "unauthorized"}
    result = payload(body)
    if change == "not_json":
        result = Payload(b"<html>error</html>", result.receipt)
    with pytest.raises(SchemaMismatchError):
        decode_prices(result, expected_page=1)


def test_form_auth_pagination_refresh_and_receipts():
    calls = []
    token_count = 0

    def handler(request):
        nonlocal token_count
        assert CREDS.password not in str(request.url)
        calls.append(request)
        if str(request.url) == TOKEN_URL:
            token_count += 1
            fields = parse_qs(request.content.decode())
            assert fields["username"] == [CREDS.username] and fields["password"] == [
                CREDS.password
            ]
            return httpx.Response(
                200,
                json={"id_token": f"synthetic-token-{token_count}", "expires_in": 3600},
            )
        assert request.url.path.endswith(PRICE_PATH)
        page = request.url.params["page"]
        return httpx.Response(
            200, content=(FIXTURES / f"dam-current-page{page}.json").read_bytes()
        )

    with PublicClient(
        CREDS, limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        assert calls == []
        pages = list(
            client.price_pages(
                start=datetime.date(2026, 9, 4),
                end=datetime.date(2026, 9, 4),
                settlement_point="HB_HOUSTON",
                size=2,
                max_pages=2,
            )
        )
        assert len(pages) == 2 and sum(len(p.rows) for p in pages) == 4
        assert token_count == 1 and len(calls) == 3
        assert pages[0].receipt.sha256 != pages[1].receipt.sha256
        client.refresh_token()
        assert token_count == 2
        client.dam_prices(settlement_point="HB_HOUSTON", size=2)
        assert calls[-1].headers["Authorization"] == "Bearer synthetic-token-2"
        assert CREDS.password not in repr(CREDS)
        assert all(CREDS.password not in repr(p.receipt) for p in pages)
    assert client._token is None


@pytest.mark.parametrize(
    "status, expected, auth_count",
    [(401, AuthenticationError, 2), (403, AccessDeniedError, 1)],
)
def test_terminal_access_errors_do_not_loop_or_expose_secrets(
    status, expected, auth_count
):
    tokens = []

    def handler(request):
        if str(request.url) == TOKEN_URL:
            tokens.append(1)
            return httpx.Response(
                200, json={"id_token": "secret-token", "expires_in": 3600}
            )
        return httpx.Response(status, json={"secret": CREDS.password})

    with PublicClient(
        CREDS, limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(expected) as caught:
            client.dam_prices(settlement_point="HB_HOUSTON", size=1)
        assert len(tokens) == auth_count
        assert CREDS.password not in str(caught.value) and "secret-token" not in str(
            caught.value
        )


def test_one_401_reacquisition_and_expiry_skew():
    tokens, gets = [], []

    def handler(request):
        if str(request.url) == TOKEN_URL:
            tokens.append(1)
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        gets.append(1)
        if len(gets) == 1:
            return httpx.Response(401)
        return httpx.Response(
            200, content=(FIXTURES / "dam-current-page1.json").read_bytes()
        )

    with PublicClient(
        CREDS, limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        now = [100.0]
        client._http.clock = lambda: now[0]
        client.dam_prices(settlement_point="HB_HOUSTON", size=2)
        assert len(tokens) == 2 and len(gets) == 2
        now[0] = 3641
        client.dam_prices(settlement_point="HB_HOUSTON", size=2)
        assert len(tokens) == 3


def test_current_generator_is_independent_and_hash_pinned(monkeypatch, tmp_path):
    from tools import generate_public

    assert generate_public.render() == generate_public.OUTPUT.read_text()
    pin = tmp_path / "dam-prices.json"
    pin.write_text("{}")
    monkeypatch.setattr(generate_public, "INPUT", pin)
    with pytest.raises(ValueError, match="Unverified"):
        generate_public.render()


@pytest.mark.parametrize("fixture", ["capacity-current", "capacity-oldest"])
def test_capacity_endpoint_uses_its_own_pinned_schema(fixture):
    from tinyercot.public import DamCapacityPrice

    calls = []

    def handler(request):
        calls.append(request)
        if str(request.url) == TOKEN_URL:
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        assert request.url.path.endswith("/np4-188-cd/dam_clear_price_for_cap")
        assert request.url.params["ancillaryType"] == "REGUP"
        return httpx.Response(200, content=(FIXTURES / f"{fixture}.json").read_bytes())

    with PublicClient(
        CREDS, limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
    ) as client:
        page = client.dam_capacity_prices(
            ancillary_type="REGUP", size=2, oldest_first=fixture.endswith("oldest")
        )
        assert page.rows and isinstance(page.rows[0], DamCapacityPrice)
        assert isinstance(page.rows[0].MCPC, Decimal)
        assert page.rows[0].ancillaryType == "REGUP"
        if fixture.endswith("oldest"):
            assert page.rows[0].deliveryDate == datetime.date(2023, 12, 13)
        assert len(calls) == 2


def test_capacity_endpoint_rejects_settlement_price_schema():
    def handler(request):
        if str(request.url) == TOKEN_URL:
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        return httpx.Response(
            200, content=(FIXTURES / "dam-current-page1.json").read_bytes()
        )

    with (
        PublicClient(
            CREDS, limits=Limits(min_interval=0), transport=httpx.MockTransport(handler)
        ) as client,
        pytest.raises(SchemaMismatchError),
    ):
        client.dam_capacity_prices(ancillary_type="REGUP", size=2)
