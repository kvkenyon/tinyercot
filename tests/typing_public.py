"""Positive static contracts; copy outside the checkout for installed checks."""

from collections.abc import AsyncIterator, Generator, Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, assert_type

import pandas as pd

from tinyercot import configure, np4_190_cd
from tinyercot.catalog import Access, operations
from tinyercot.public import (
    DAM_CAPACITY_PRICES,
    DAM_PRICES,
    RT_PRICES,
    SYSTEM_LOAD,
    AdditionalDashboardClient,
    AggregateDashboardClient,
    APIArchive,
    APIArchiveClient,
    APIArchiveFile,
    APIArchivePage,
    APIBundle,
    APIBundlePage,
    ArchiveDocument,
    ArchivePrice,
    Artifact,
    DamCapacityPrice,
    DamPrice,
    DashboardClient,
    DayAheadDashboardPrice,
    DcTieRow,
    DcTieSnapshot,
    Download,
    FuelMixSnapshot,
    GenerationOutagesSnapshot,
    GridConditionsSnapshot,
    MetadataClient,
    Product,
    PublicClient,
    RealTimeDashboardPrice,
    RealTimePrice,
    Receipt,
    ReportsClient,
    ResourceDmeRecord,
    ResourceDmeRow,
    RTArchiveClient,
    RTArchivePrice,
    RTArchiveRecord,
    SupplyActualRow,
    SupplyDemandSnapshot,
    SupplyForecastRow,
    SupplyOutlookRow,
    SystemLoad,
    SystemPricesSnapshot,
    WebClient,
    iter_dam_archive,
    iter_resource_dme,
    iter_rt_archive,
)


def public_contracts(
    reports: ReportsClient, prices: PublicClient, web: WebClient, download: Download
) -> None:
    """Check public row, query, metadata, file, and legacy method types."""
    configure(username="synthetic")
    with reports as scoped:
        assert_type(scoped, ReportsClient)
        assert_type(
            RT_PRICES.iter_rows(
                scoped, filters={"settlementPointPriceFrom": Decimal("1.25")}
            ),
            Iterator[RealTimePrice],
        )
    assert_type(operations()[0].access, Access)
    assert_type(
        DAM_PRICES.page(reports, filters={"deliveryDateFrom": date(2026, 9, 4)}).rows[
            0
        ],
        DamPrice,
    )
    assert_type(reports.page(DAM_CAPACITY_PRICES).rows[0], DamCapacityPrice)
    assert_type(
        RT_PRICES.page(reports, filters={"deliveryHourFrom": 1}).rows[0], RealTimePrice
    )
    assert_type(reports.page(SYSTEM_LOAD).rows[0], SystemLoad)
    assert_type(reports.page(RT_PRICES).rows[0].deliveryHour, int)
    assert_type(reports.page(SYSTEM_LOAD).rows[0].total, Decimal)
    assert_type(reports.iter_rows(SYSTEM_LOAD), Iterator[SystemLoad])
    assert_type(prices.dam_prices(settlement_point="HB_HOUSTON").rows[0], DamPrice)
    assert_type(web.esr().current_day.data[0].netOutput, Decimal)
    assert_type(next(iter_dam_archive(download)).row, ArchivePrice)
    legacy = np4_190_cd.dam_stlmnt_pnt_prices()
    assert_type(legacy.data[0], np4_190_cd.DamStlmntPntPricesRow)
    assert_type(legacy.data[0].settlementPointPrice, Decimal)
    assert_type(legacy.to_df(), pd.DataFrame)
    assert_type(np4_190_cd.dam_stlmnt_pnt_prices_df(), pd.DataFrame)
    assert_type(
        np4_190_cd.dam_stlmnt_pnt_prices_iter(),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )
    assert_type(
        np4_190_cd.dam_stlmnt_pnt_prices_iter_async(),
        AsyncIterator[np4_190_cd.DamStlmntPntPricesRow],
    )


async def legacy_async_contract() -> None:
    """Check the legacy async DataFrame return contract without running it."""
    assert_type(await np4_190_cd.dam_stlmnt_pnt_prices_df_async(), pd.DataFrame)


def live_and_metadata_contracts(
    dashboard: DashboardClient,
    aggregates: AggregateDashboardClient,
    metadata: MetadataClient,
) -> None:
    """Verify precise anonymous snapshots and independent public metadata types."""
    with aggregates as scoped:
        assert_type(scoped, AggregateDashboardClient)
    assert_type(dashboard.fuel_mix(), FuelMixSnapshot)
    assert_type(dashboard.fuel_mix().rows[0].generation.natural_gas, Decimal)
    assert_type(dashboard.fuel_mix().rows[0].source_timestamp, str)
    assert_type(dashboard.fuel_mix().rows[0].timestamp, datetime)
    assert_type(dashboard.grid_conditions(), GridConditionsSnapshot)
    assert_type(dashboard.grid_conditions().current_condition.state, str)
    assert_type(dashboard.grid_conditions().rows[0].prc, int)
    assert_type(aggregates.generation_outages(), GenerationOutagesSnapshot)
    assert_type(aggregates.generation_outages().current[0].row.combined.total, int)
    assert_type(aggregates.generation_outages().current[0].source_epoch, str)
    assert_type(aggregates.dc_tie_flows(), DcTieSnapshot)
    assert_type(aggregates.dc_tie_flows().rows, tuple[DcTieRow, ...])
    assert_type(aggregates.dc_tie_flows().rows[0].currentFrequency, Decimal)
    assert_type(aggregates.dc_tie_flows().rows[0].dcN, int)
    assert_type(metadata.products(), tuple[tuple[Product, ...], Receipt])
    assert_type(metadata.product("np4-190-cd"), tuple[Product, Receipt])
    assert_type(metadata.product("np4-190-cd")[0].access, Access)
    assert_type(metadata.product("np4-190-cd")[0].artifacts, tuple[Artifact, ...])
    assert_type(metadata.product("np4-190-cd")[0].artifacts[0].path, str | None)


def additional_dashboard_contracts(client: AdditionalDashboardClient) -> None:
    """Check source price rows and observed versus published supply values."""
    with client as scoped:
        assert_type(scoped, AdditionalDashboardClient)
    prices = client.system_prices()
    assert_type(prices, SystemPricesSnapshot)
    assert_type(prices.real_time, tuple[RealTimeDashboardPrice, ...])
    assert_type(prices.day_ahead, tuple[DayAheadDashboardPrice, ...])
    assert_type(prices.real_time[0].hbHouston, Decimal)
    assert_type(prices.real_time[0].intervalEnding, str)
    assert_type(prices.real_time[0].interval, int)
    assert_type(prices.real_time[0].timestamp, str)
    assert_type(prices.day_ahead[0].hourEnding, int)
    supply = client.supply_demand()
    assert_type(supply, SupplyDemandSnapshot)
    assert_type(supply.data, tuple[SupplyActualRow | SupplyForecastRow, ...])
    assert_type(supply.forecast, tuple[SupplyOutlookRow, ...])
    for row in supply.data:
        assert_type(row.demand, int)
        if isinstance(row, SupplyForecastRow):
            assert_type(row.available, int)
            assert_type(row.forecast, Literal[1])
        else:
            assert_type(row, SupplyActualRow)
            assert_type(row.forecast, Literal[0])
    assert_type(supply.forecast[0].forecastedDemand, int)
    assert_type(supply.forecast[0].deliveryDateHrBegin, str)


def archive_contracts(
    annual: RTArchiveClient,
    archives: APIArchiveClient,
    document: ArchiveDocument,
    download: Download,
    api_file: APIArchiveFile,
) -> None:
    """Verify selected file rows while keeping generic archive schemas unknown."""
    assert_type(annual.archives(), tuple[tuple[ArchiveDocument, ...], Receipt])
    assert_type(annual.download(document, cache=Path("cache")), Download)
    assert_type(
        iter_rt_archive(download, max_rows=None), Generator[RTArchiveRecord, None, None]
    )
    assert_type(next(iter_rt_archive(download)).row, RTArchivePrice)
    assert_type(next(iter_rt_archive(download)).row.settlement_point_price, Decimal)
    assert_type(archives.archives("np4-190-cd"), APIArchivePage)
    assert_type(archives.archives("np4-190-cd").documents, tuple[APIArchive, ...])
    assert_type(archives.bundles("np4-190-cd"), APIBundlePage)
    assert_type(archives.bundles("np4-190-cd").documents, tuple[APIBundle, ...])
    assert_type(
        archives.archives("np4-190-cd").lifecycle,
        Literal["active", "retired-or-inactive", "unknown"],
    )
    assert_type(
        archives.download(archives.archives("np4-190-cd").documents[0]), APIArchiveFile
    )
    assert_type(
        archives.download_bundle(archives.bundles("np4-190-cd").documents[0]),
        APIArchiveFile,
    )
    assert_type(api_file.row_schema, Literal["unknown"])
    assert_type(iter_resource_dme(api_file), Generator[ResourceDmeRecord, None, None])
    assert_type(next(iter_resource_dme(api_file)).row, ResourceDmeRow)
    assert_type(next(iter_resource_dme(api_file)).row.dme_duns, str)
