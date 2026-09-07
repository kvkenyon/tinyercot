from collections.abc import AsyncIterator, Iterator
from datetime import date
from decimal import Decimal
from typing import assert_type

from tinyercot import Archive, Client, Page, np3_966_er, np4_190_cd

with Client() as client:
    result = client.np4_190_cd.dam_stlmnt_pnt_prices(deliveryDateFrom=date(2026, 1, 1))
    assert_type(result, Page[np4_190_cd.DamStlmntPntPricesRow])
    assert_type(result.data[0].settlementPointPrice, Decimal | None)
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_iter(),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_iter_async(),
        AsyncIterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history,
        Archive[np4_190_cd.DamStlmntPntPricesRow],
    )
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history.rows(
            where=lambda row: row.settlementPoint == "HB_HOUSTON"
        ),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    assert_type(
        client.np3_966_er._60_dam_load_res_data_history,
        Archive[np3_966_er._60DamLoadResDataHistoryRow],
    )
