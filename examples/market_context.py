"""Export load, renewable and outage reports with original publication times."""

import argparse
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from examples.market_day import write_rows
from tinyercot import Client, Document, Publication

T = TypeVar("T", bound=BaseModel)


class PublishedRow(BaseModel, Generic[T]):
    document: Document
    row: T


def published_rows(reports: Iterable[Publication[T]]) -> Iterator[PublishedRow[T]]:
    for report in reports:
        for row in report.rows:
            yield PublishedRow(document=report.document, row=row)


def export_market_context(
    client: Client, posted_from: datetime, posted_to: datetime, directory: Path
) -> dict[str, int]:
    """Preserve each original issue and all its delivery periods, without joins."""
    for bound in (posted_from, posted_to):
        if bound.utcoffset() is not None:
            raise ValueError("Publication bounds must be ERCOT-local without an offset")
    if posted_from > posted_to:
        raise ValueError("posted_from must not exceed posted_to")
    directory.mkdir(parents=True, exist_ok=True)

    # Each concrete reader retains its own generated row type and source fields.
    def export(name: str, reports: Iterable[Publication[T]]) -> int:
        return write_rows(directory / f"{name}.jsonl", published_rows(reports))

    return {
        "load_forecasts": export(
            "load_forecasts",
            client.np3_561_cd._7d_load_fcast_by_wzn_history.publications(
                posted_from=posted_from, posted_to=posted_to
            ),
        ),
        "wind": export(
            "wind",
            client.np4_742_cd.wpp_hrly_actual_fcast_geo_history.publications(
                posted_from=posted_from, posted_to=posted_to
            ),
        ),
        "solar": export(
            "solar",
            client.np4_745_cd.spp_hrly_actual_fcast_geo_history.publications(
                posted_from=posted_from, posted_to=posted_to
            ),
        ),
        "outages": export(
            "outages",
            client.np3_233_cd.hourly_res_outage_cap_history.publications(
                posted_from=posted_from, posted_to=posted_to
            ),
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("posted_from", type=datetime.fromisoformat)
    parser.add_argument("posted_to", type=datetime.fromisoformat)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with Client() as ercot:
        counts = export_market_context(
            ercot, args.posted_from, args.posted_to, args.output
        )
    for name, count in counts.items():
        print(f"{name}: {count} rows")
