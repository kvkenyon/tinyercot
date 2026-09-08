"""Read one day of Houston hub prices with typed filters and rows."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tinyercot import Client

if __name__ == "__main__":
    yesterday = datetime.now(ZoneInfo("America/Chicago")).date() - timedelta(days=1)
    with Client() as ercot:
        for row in ercot.np4_190_cd.dam_stlmnt_pnt_prices_iter(
            deliveryDateFrom=yesterday,
            deliveryDateTo=yesterday,
            settlementPoint="HB_HOUSTON",
        ):
            print(row.deliveryDate, row.hourEnding, row.settlementPointPrice)
