"""Check every generated current contract against its two bounded source samples."""

import datetime
import hashlib
from pathlib import Path

import httpx
import pytest

from tinyercot.catalog import Access
from tinyercot.public import Credentials, StreamingLimits
from tinyercot.public._http import Payload, Receipt
from tinyercot.public._schemas import ENDPOINTS
from tinyercot.public.metadata import MetadataClient
from tinyercot.public.reports import decode_page

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "tests/fixtures/public/batch"
NEW = [endpoint for endpoint in ENDPOINTS if "product_evidence" in endpoint.contract]


@pytest.mark.parametrize("endpoint", NEW, ids=lambda endpoint: endpoint.path)
@pytest.mark.parametrize("period", ["current", "historical"])
def test_generated_rows_decode_primary_source_observations(endpoint, period):
    name = endpoint.path.strip("/").replace("/", "--") + "--" + period + ".json"
    path = BATCH / name
    if not path.exists():
        pytest.skip("No source row observation for this period")
    # apply_patch stores a final newline; source observations have none.
    raw = path.read_bytes().removesuffix(b"\n")
    digest = hashlib.sha256(raw).hexdigest()
    assert digest in {
        receipt["sha256"] for receipt in endpoint.contract["observations"]
    }
    receipt = Receipt(
        "https://api.ercot.com/api/public-reports" + endpoint.path,
        datetime.datetime.now(datetime.UTC),
        digest,
        len(raw),
    )
    decoded = decode_page(Payload(raw, receipt), endpoint, page=1, size=1)
    assert len(decoded.rows) == 1
    assert type(decoded.rows[0]) is endpoint.row_model
    assert set(type(decoded.rows[0]).model_fields) == {
        field["name"] for field in endpoint.contract["fields"]
    }


def test_public_metadata_retains_access_and_artifacts_without_row_claims():
    raw = (BATCH / "root.json").read_bytes()

    def transport(request):
        if request.method == "POST":
            return httpx.Response(
                200, json={"id_token": "synthetic", "expires_in": 3600}
            )
        return httpx.Response(200, content=raw)

    with MetadataClient(
        Credentials("test", "test", "test"),
        limits=StreamingLimits(min_interval=0),
        transport=httpx.MockTransport(transport),
    ) as client:
        products, receipt = client.products()
    assert len(products) == 116
    assert all(product.access is Access.PUBLIC for product in products)
    assert sum(len(product.artifacts) for product in products) == 242
    assert receipt.sha256 == hashlib.sha256(raw).hexdigest()


def test_generated_datetime_filters_preserve_source_naive_time_and_reject_offsets():
    endpoint = next(
        ep
        for ep in NEW
        if any(
            p["schema"].get("format") == "yyyy-MM-ddTH24:mm:ss"
            for p in ep.contract["query_parameters"]
        )
    )
    name = next(
        p["name"]
        for p in endpoint.contract["query_parameters"]
        if p["schema"].get("format") == "yyyy-MM-ddTH24:mm:ss"
    )
    from tinyercot.public.reports import query_parameters

    assert (
        query_parameters(
            endpoint, {name: datetime.datetime.fromisoformat("2026-09-04T01:02:03")}
        )[name]
        == "2026-09-04T01:02:03"
    )
    with pytest.raises(ValueError):
        query_parameters(
            endpoint, {name: datetime.datetime(2026, 9, 4, tzinfo=datetime.UTC)}
        )
