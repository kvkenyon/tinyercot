"""Negative static contracts; the installed checker must reject each line."""

from tinyercot import np4_190_cd
from tinyercot.public import DAM_PRICES, RT_PRICES, ReportsClient


def invalid_contracts(client: ReportsClient) -> None:
    """Ensure wrong filters and row fields do not degrade to Any."""
    DAM_PRICES.page(client, filters={"deliveryDateFrom": "2026-09-04"})
    RT_PRICES.page(client, filters={"deliveryHourFrom": "one"})
    _ = client.page(RT_PRICES).rows[0].not_a_source_field
    np4_190_cd.dam_stlmnt_pnt_prices(deliveryDateFrom="2026-09-04")
