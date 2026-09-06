"""Negative static contracts; the installed checker must reject each line."""

from tinyercot import np4_190_cd
from tinyercot.public import (
    DAM_PRICES,
    RT_PRICES,
    APIArchiveClient,
    APIArchiveFile,
    DashboardClient,
    Download,
    ReportsClient,
    iter_resource_dme,
    iter_rt_archive,
)


def invalid_contracts(client: ReportsClient) -> None:
    """Ensure wrong filters and row fields do not degrade to Any."""
    DAM_PRICES.page(client, filters={"deliveryDateFrom": "2026-09-04"})
    RT_PRICES.page(client, filters={"deliveryHourFrom": "one"})
    _ = client.page(RT_PRICES).rows[0].not_a_source_field
    np4_190_cd.dam_stlmnt_pnt_prices(deliveryDateFrom="2026-09-04")


def invalid_additive_contracts(
    dashboard: DashboardClient,
    archives: APIArchiveClient,
    api_file: APIArchiveFile,
    annual: Download,
) -> None:
    """Reject unknown live fields, unlisted identities, and identifier coercion."""
    _ = dashboard.fuel_mix().rows[0].generation.not_a_source_fuel
    archives.download_bundle("unlisted-document")
    _identifier: int = next(iter_resource_dme(api_file)).row.dme_duns
    iter_rt_archive(annual, max_rows="all")
