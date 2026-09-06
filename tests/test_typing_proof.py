"""Check generated assertion structure; real PEP 561 proof uses an installed wheel."""

import ast

import pytest

from tinyercot import public
from tinyercot.public import _schemas
from tools.check_typing import registry_assertions


@pytest.fixture
def registry():
    source = (
        "SAMPLE: Endpoint[SampleRow, SampleRowFilters] = "
        "Endpoint('/np1-2-cd/7d_sample', SampleRow, 'sample.json')\n"
    )
    bundle = {
        "sample.json": {
            "path": "/np1-2-cd/7d_sample",
            "fields": [
                {"name": "price", "dataType": "DOUBLE"},
                {"name": "deliveryDate", "dataType": "DATE"},
            ],
            "observed_nullable_fields": ["price"],
            "query_parameters": [
                {
                    "name": "deliveryDateFrom",
                    "schema": {"type": "string", "format": "yyyy-MM-dd"},
                },
                {
                    "name": "postedDatetimeFrom",
                    "schema": {"type": "string", "format": "yyyy-MM-ddTH24:mm:ss"},
                },
                {"name": "priceFrom", "schema": {"type": "number"}},
                {"name": "size", "schema": {"type": "integer"}},
            ],
        }
    }
    return source, bundle


def test_assertions_cover_precise_facade_filters_rows_and_iteration(registry):
    positive, negative, counts = registry_assertions(*registry)
    ast.parse(positive)
    ast.parse(negative)
    assert counts == {
        "endpoints": 1,
        "row_fields": 2,
        "filter_fields": 3,
        "invalid_uses": 1,
    }
    assert (
        "assert_type(schemas.SAMPLE, Endpoint[rows.SampleRow, schemas.SampleRowFilters])"
        in positive
    )
    assert "products.np1_2_cd._7d_sample" in positive
    assert "assert_type(row.price, Decimal | None)" in positive
    assert "assert_type(filters['postedDatetimeFrom'], datetime)" in positive
    assert "Iterator[DataPage[rows.SampleRow]]" in positive
    assert "Iterator[rows.SampleRow]" in positive
    assert "'not_a_source_filter': 1" in negative
    assert registry_assertions(*registry) == (positive, negative, counts)


def test_assertions_reject_registry_contract_identity_mismatch(registry):
    source, bundle = registry
    bundle["sample.json"]["path"] = "/np1-2-cd/different"
    with pytest.raises(ValueError, match="identity"):
        registry_assertions(source, bundle)


def test_assertions_reject_an_unrepresented_bundled_contract(registry):
    source, bundle = registry
    bundle["missing.json"] = {**bundle["sample.json"], "path": "/np1-2-cd/missing"}
    with pytest.raises(ValueError, match="every bundled"):
        registry_assertions(source, bundle)


def test_product_facades_cover_every_endpoint_and_stable_exports_remain():
    assert len(public.__all__) == len(set(public.__all__))
    for endpoint in _schemas.ENDPOINTS:
        constants = [
            name for name in vars(_schemas) if getattr(_schemas, name) is endpoint
        ]
        assert len(constants) == 1
        name = constants[0]
        product, method = endpoint.path.strip("/").split("/")
        if not method.isidentifier():
            method = "_" + method
        assert (
            getattr(getattr(public.products, product.replace("-", "_")), method)
            is endpoint
        )
        if name in {"DAM_PRICES", "DAM_CAPACITY_PRICES", "RT_PRICES", "SYSTEM_LOAD"}:
            assert name in public.__all__
            assert getattr(public, name) is endpoint
            assert getattr(public, endpoint.row_model.__name__) is endpoint.row_model
            filter_name = endpoint.row_model.__name__ + "Filters"
            assert getattr(public, filter_name) is getattr(_schemas, filter_name)
    for name in [
        "MetadataClient",
        "Product",
        "Artifact",
        "DashboardClient",
        "AggregateDashboardClient",
        "RTArchiveClient",
        "APIArchiveClient",
        "APIBundle",
        "APIBundlePage",
        "ResourceDmeRow",
        "iter_resource_dme",
        "products",
    ]:
        assert name in public.__all__ and getattr(public, name) is not None
