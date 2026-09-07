from collections.abc import AsyncIterator, Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import assert_type

from tinyercot import Archive, Client, Page, np3_966_er, np3_988_er, np4_190_cd

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

    assert_type(
        client.np3_988_er.resources_history,
        Archive[np3_988_er.ResourcesHistoryRow],
    )

    for row in client.eia_930_er.daily_operations_history.read(b""):
        assert_type(row.HR1, Decimal | datetime | None)

    for outage in client.np1_346_er.outages_history.rows():
        assert_type(outage.plannedEndDate, datetime | None)
        assert_type(outage.availableMWMaximum, Decimal | None)
    for response in client.np3_108.demand_response_history.rows():
        assert_type(response.month, date | None)
        assert_type(response.sourceSheet, str | None)

    for solar in client.np4_737_cd.spp_hrly_avrg_actl_fcast_history.rows():
        assert_type(solar.hourEndingTimestamp, datetime | None)
        assert_type(solar.genSystemWide, Decimal | None)
    for wind in client.np4_733_cd.wpp_actual_5min_avg_values_history.rows():
        assert_type(wind.LZWestNorth, Decimal | None)
