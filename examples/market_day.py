"""Export typed market inputs as JSON Lines, keeping source intervals separate."""

import argparse
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from tinyercot import Client


def write_rows(path: Path, rows: Iterable[BaseModel]) -> int:
    """Preserve Decimal strings, nulls, field names and DST flags in each row."""
    count = 0
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(row.model_dump_json() + "\n")
            count += 1
    return count


def export_market_day(
    client: Client, day: date, point: str, directory: Path
) -> dict[str, int]:
    """Retrieve prices for a hub/load zone and system-wide load and AS inputs.

    The four files retain their native frequency and locations. This example
    does not join weather zones to settlement load zones or resolve corrections.
    """
    directory.mkdir(parents=True, exist_ok=True)
    return {
        "dam_prices": write_rows(
            directory / "dam_prices.jsonl",
            client.np4_190_cd.dam_stlmnt_pnt_prices_iter(
                deliveryDateFrom=day, deliveryDateTo=day, settlementPoint=point
            ),
        ),
        "rt_prices": write_rows(
            directory / "rt_prices.jsonl",
            client.np6_905_cd.spp_node_zone_hub_iter(
                deliveryDateFrom=day, deliveryDateTo=day, settlementPoint=point
            ),
        ),
        "dam_ancillary_prices": write_rows(
            directory / "dam_ancillary_prices.jsonl",
            client.np4_188_cd.dam_clear_price_for_cap_iter(
                deliveryDateFrom=day, deliveryDateTo=day
            ),
        ),
        "actual_load": write_rows(
            directory / "actual_load.jsonl",
            client.np6_345_cd.act_sys_load_by_wzn_iter(
                operatingDayFrom=day, operatingDayTo=day
            ),
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "day", type=date.fromisoformat, help="Operating day: YYYY-MM-DD"
    )
    parser.add_argument("--point", default="HB_HOUSTON", help="Settlement point name")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    with Client() as ercot:
        for name, count in export_market_day(
            ercot, args.day, args.point, args.output
        ).items():
            print(f"{name}: {count} rows")
