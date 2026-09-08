"""Export historical forecasts with the original archive publication metadata."""

import argparse
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from tinyercot import Client, Document, np3_561_cd


class ForecastVintage(BaseModel):
    document: Document
    forecast: np3_561_cd._7dLoadFcastByWznHistoryRow


def export_forecast_vintages(
    client: Client, posted_from: datetime, posted_to: datetime, path: Path
) -> int:
    """Keep separate issues even when their target dates or predicted values match.

    Bounds use ERCOT local publication time. For a backtest, retain only issues
    available at the decision time; never use the target date as an issue time.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as output:
        for publication in client.np3_561_cd._7d_load_fcast_by_wzn_history.publications(
            posted_from=posted_from, posted_to=posted_to
        ):
            for forecast in publication.rows:
                vintage = ForecastVintage(
                    document=publication.document, forecast=forecast
                )
                output.write(vintage.model_dump_json() + "\n")
                count += 1
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("posted_from", type=datetime.fromisoformat)
    parser.add_argument("posted_to", type=datetime.fromisoformat)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with Client() as ercot:
        count = export_forecast_vintages(
            ercot, args.posted_from, args.posted_to, args.output
        )
    print(f"forecast_vintages: {count} rows")
