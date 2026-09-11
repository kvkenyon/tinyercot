"""Export July–August 2026 settlement loss factors without API credentials."""

import argparse
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from examples.market_day import write_rows
from tinyercot import Client, LossFactorDay


def july_august_2026(client: Client) -> Iterator[LossFactorDay]:
    """Keep actual/forecast and transmission/distribution series distinct."""
    archives = [a for a in client.loss_factors.archives() if a.year == 2026]
    if not archives:
        raise ValueError("ERCOT's index has no 2026 loss-factor workbook")
    for archive in archives:
        yield from client.loss_factors.read(
            client.loss_factors.download(archive),
            filename=archive.url.rsplit("/", 1)[-1],
            source_file=archive,
            date_from=date(2026, 7, 1),
            date_to=date(2026, 8, 31),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("loss-factors-jul-aug-2026.jsonl")
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Client() as ercot:
        count = write_rows(args.output, july_august_2026(ercot))
    print(f"loss_factors: {count} series/day rows -> {args.output}")
