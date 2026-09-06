"""Positive static contracts; copy outside the checkout for installed checks."""

from collections.abc import AsyncIterator, Iterator
from datetime import date
from decimal import Decimal
from typing import assert_type

import pandas as pd

from tinyercot import configure, np4_190_cd
from tinyercot.catalog import Access, operations
from tinyercot.public import (
    DAM_CAPACITY_PRICES,
    DAM_PRICES,
    RT_PRICES,
    SYSTEM_LOAD,
    ArchivePrice,
    DamCapacityPrice,
    DamPrice,
    Download,
    PublicClient,
    RealTimePrice,
    ReportsClient,
    SystemLoad,
    WebClient,
    iter_dam_archive,
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
