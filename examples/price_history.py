"""Export retained DAM or RT settlement-price history as typed JSON Lines."""

import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from examples.market_day import write_rows
from tinyercot import Client, np4_190_cd, np6_905_cd


def export_price_history(
    client: Client,
    market: Literal["dam", "rt"],
    point: str,
    path: Path,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    posted_from: datetime | None = None,
    posted_to: datetime | None = None,
) -> int:
    """Combine bundles and archives, filtering delivery dates after decoding.

    Unbounded publication selection includes bundle-only reports and older
    individual archives. Distinct corrections remain separate. Output is not
    sorted. Delivery-date filters apply after download; optional inclusive
    ERCOT-local publication bounds limit downloads using archive metadata.
    """
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must not exceed date_to")
    for bound in (posted_from, posted_to):
        if bound is not None and bound.utcoffset() is not None:
            raise ValueError("Publication bounds must be ERCOT-local without an offset")
    if posted_from and posted_to and posted_from > posted_to:
        raise ValueError("posted_from must not exceed posted_to")

    def selected(
        row: np4_190_cd.DamStlmntPntPricesRow | np6_905_cd.SppNodeZoneHubRow,
    ) -> bool:
        return (
            row.settlementPoint == point
            and (
                date_from is None
                or (row.deliveryDate is not None and row.deliveryDate >= date_from)
            )
            and (
                date_to is None
                or (row.deliveryDate is not None and row.deliveryDate <= date_to)
            )
        )

    history = (
        client.np4_190_cd.dam_stlmnt_pnt_prices_history
        if market == "dam"
        else client.np6_905_cd.spp_node_zone_hub_history
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return write_rows(
        path,
        history.backfill(
            posted_from=posted_from,
            posted_to=posted_to,
            where=selected,
            batch_size=25,
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("market", choices=("dam", "rt"))
    parser.add_argument("--point", default="HB_HOUSTON", help="Settlement point name")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL file")
    parser.add_argument("--date-from", type=date.fromisoformat, help="Delivery date")
    parser.add_argument("--date-to", type=date.fromisoformat, help="Delivery date")
    for flag in ("--posted-from", "--posted-to"):
        parser.add_argument(
            flag,
            type=datetime.fromisoformat,
            help="Inclusive publication time, ERCOT-local ISO timestamp without offset",
        )
    args = parser.parse_args()
    with Client() as ercot:
        count = export_price_history(
            ercot,
            args.market,
            args.point,
            args.output,
            date_from=args.date_from,
            date_to=args.date_to,
            posted_from=args.posted_from,
            posted_to=args.posted_to,
        )
    print(f"{args.market}_prices: {count} rows")
