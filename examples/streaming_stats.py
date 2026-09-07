"""Compute an average without collecting report pages in memory."""

from datetime import date
from decimal import Decimal

from tinyercot import Client


def mean_price(start: date, end: date, point: str = "HB_HOUSTON") -> Decimal | None:
    total, count = Decimal(0), 0
    with Client() as ercot:
        for row in ercot.np4_190_cd.dam_stlmnt_pnt_prices_iter(
            deliveryDateFrom=start, deliveryDateTo=end, settlementPoint=point
        ):
            if row.settlementPointPrice is not None:
                total += row.settlementPointPrice
                count += 1
    return total / count if count else None
