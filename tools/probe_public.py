"""Run a small real-source check with an installed wheel, only with --live.

The credential file is the JSON-quoted, mode-0600 local vault export used for
this task. Receipts contain public source metadata and hashes, never headers.
"""

import argparse
import datetime
import json
import logging
import stat
from dataclasses import asdict
from pathlib import Path

import tinyercot
from tinyercot.public import (
    RT_PRICES,
    SYSTEM_LOAD,
    Credentials,
    PublicClient,
    ReportsClient,
    WebClient,
    sample_dam_archive,
)


def main() -> None:
    """Check installed current/history retrieval and write public-only receipts.

    Raises:
        SystemExit: Explicit consent, installed-package, or credential checks fail.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Check new RT/load contracts with six bounded data requests",
    )
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("Real requests require --live")
    root = Path(__file__).resolve().parents[1]
    installed = Path(tinyercot.__file__).resolve()
    if installed.parent == root / "tinyercot":
        raise SystemExit("Run with an isolated interpreter and the installed wheel")
    credential_file = args.credentials_file
    if (
        credential_file.is_symlink()
        or stat.S_IMODE(credential_file.stat().st_mode) != 0o600
    ):
        raise SystemExit("Credentials require a regular mode-0600 file")
    if not credential_file.is_file():
        raise SystemExit("Credentials require a regular file")
    logging.disable(logging.CRITICAL)
    records = {"installed_module": str(installed), "receipts": []}
    args.output.mkdir(parents=True, exist_ok=True)

    def record(kind, receipt, **metadata):
        """Add public source evidence without request headers or row values.

        Args:
            kind: Evidence class for this installed-client operation.
            receipt: Public URL, retrieval time, byte count, and response hash.
            **metadata: Public counts and source publication or selection fields.
        """
        records["receipts"].append({"kind": kind, **asdict(receipt), **metadata})
        (args.output / "installed-receipts.json").write_text(
            json.dumps(records, indent=2, default=str) + "\n"
        )

    try:
        values = {
            key: json.loads(value)
            for line in credential_file.read_text().splitlines()
            for key, value in [line.split("=", 1)]
        }
        credentials = Credentials(
            *(
                values[name]
                for name in (
                    "ERCOT_USERNAME",
                    "ERCOT_PASSWORD",
                    "ERCOT_SUBSCRIPTION_KEY",
                )
            )
        )
        del values
        day = datetime.date(2026, 9, 4)
        if args.reports_only:
            with ReportsClient(credentials) as client:
                for endpoint, date_field, selection in (
                    (RT_PRICES, "deliveryDate", {"settlementPoint": "HB_HOUSTON"}),
                    (SYSTEM_LOAD, "operatingDay", {}),
                ):
                    for period in ("current", "historical"):
                        filters = dict(selection)
                        if period == "current":
                            filters.update(
                                {date_field + "From": day, date_field + "To": day}
                            )
                        page = client.page(
                            endpoint,
                            filters=filters,
                            size=2 if period == "current" else 1,
                            sort=date_field,
                            direction="desc" if period == "current" else "asc",
                        )
                        assert len(page.rows) == (2 if period == "current" else 1)
                        if period == "current":
                            assert all(
                                getattr(row, date_field) == day for row in page.rows
                            )
                        record(
                            "typed-reports-" + period,
                            page.receipt,
                            endpoint=endpoint.path,
                            rows=len(page.rows),
                            first_observed_date=str(getattr(page.rows[0], date_field)),
                        )
                pages = list(
                    client.pages(
                        RT_PRICES,
                        filters={
                            "settlementPoint": "HB_HOUSTON",
                            "deliveryDateFrom": day,
                            "deliveryDateTo": day,
                            "deliveryHourFrom": 1,
                            "deliveryHourTo": 1,
                            "deliveryIntervalFrom": 1,
                            "deliveryIntervalTo": 2,
                        },
                        size=1,
                        sort="deliveryInterval",
                        max_pages=2,
                    )
                )
                assert len(pages) == 2 and sum(len(page.rows) for page in pages) == 2
                for page in pages:
                    record(
                        "typed-reports-complete-selection",
                        page.receipt,
                        endpoint=RT_PRICES.path,
                        rows=len(page.rows),
                        page=page.meta["currentPage"],
                        total_records=page.meta["totalRecords"],
                    )
            print(
                "Installed RT/load current, historical, and complete two-page selection passed"
            )
            return
        with PublicClient(credentials) as client:
            for page in client.price_pages(
                start=day, end=day, settlement_point="HB_HOUSTON", size=2, max_pages=2
            ):
                assert page.rows and all(row.deliveryDate == day for row in page.rows)
                record(
                    "typed-api-current",
                    page.receipt,
                    rows=len(page.rows),
                    page=page.meta["currentPage"],
                    total_pages=page.meta["totalPages"],
                )
            page = client.dam_prices(
                settlement_point="HB_HOUSTON", size=1, oldest_first=True
            )
            assert len(page.rows) == 1
            record(
                "typed-api-historical",
                page.receipt,
                rows=1,
                earliest_observed_date=str(page.rows[0].deliveryDate),
            )
            client.refresh_token()
            page = client.dam_prices(
                start=day, end=day, settlement_point="HB_HOUSTON", size=1
            )
            assert page.rows
            record(
                "typed-api-after-token-reacquisition", page.receipt, rows=len(page.rows)
            )
            page = client.dam_capacity_prices(
                start=day, end=day, ancillary_type="REGUP", size=2
            )
            assert len(page.rows) == 2 and all(
                row.deliveryDate == day for row in page.rows
            )
            record("typed-capacity-current", page.receipt, rows=len(page.rows))
            page = client.dam_capacity_prices(
                ancillary_type="REGUP", size=1, oldest_first=True
            )
            assert len(page.rows) == 1
            record(
                "typed-capacity-historical",
                page.receipt,
                rows=1,
                earliest_observed_date=str(page.rows[0].deliveryDate),
            )
        with WebClient() as client:
            snapshot = client.esr()
            record(
                "typed-esr",
                snapshot.receipt,
                rows=len(snapshot.previous_day.data) + len(snapshot.current_day.data),
                source_updated_at=str(snapshot.last_updated),
                stale=snapshot.is_stale(),
            )
            documents, receipt = client.dam_archives()
            record("typed-public-mis-listing", receipt, documents=len(documents))
            for year, sheet in ((2010, "Dec_1"), (2026, "Aug")):
                document = next(
                    item
                    for item in documents
                    if item.friendly_name == f"DAMLZHBSPP_{year}"
                )
                download = client.download_dam_archive(
                    document, cache=args.output / "cache"
                )
                sample = sample_dam_archive(download, sheet=sheet, max_rows=4)
                assert len(sample.rows) == 4 and sample.truncated
                reused = client.download_dam_archive(
                    document, cache=args.output / "cache"
                )
                assert reused.cache_hit and reused.receipt == download.receipt
                record(
                    "typed-annual-sample",
                    download.receipt,
                    year=year,
                    source_published_at=str(document.published_at),
                    document_id=document.document_id,
                    rows=len(sample.rows),
                    member=sample.member,
                    sheet=sample.sheet,
                    truncated=sample.truncated,
                    initial_cache_hit=download.cache_hit,
                    verified_cache_reuse=True,
                )
    except Exception as error:  # noqa: BLE001 - Do not expose third-party request objects.
        # Some third-party exceptions retain requests. Never print their values.
        raise SystemExit(
            f"Installed probe failed: {type(error).__name__}; public receipts retained"
        ) from None
    print("Installed public-source probe passed; public-only receipts written")


if __name__ == "__main__":
    main()
