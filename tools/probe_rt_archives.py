"""Explicit, anonymous installed-wheel probe for two selected RT annual files."""

import argparse
import datetime
import hashlib
import json
from contextlib import closing
from dataclasses import asdict
from itertools import islice
from pathlib import Path

import tinyercot
from tinyercot.public.archive_reports import RTArchiveClient, iter_rt_archive


def main() -> None:
    """Fetch a listing, reuse two source files, and record four typed rows each."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-evidence", type=Path, required=True)
    args = parser.parse_args()
    package = Path(tinyercot.__file__).resolve()
    if "site-packages" not in package.parts:
        parser.error("Run with an isolated installed-wheel interpreter using -I")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    with RTArchiveClient() as client:
        documents, listing = client.archives()
        for year, sheet in ((2010, "Dec_1"), (2026, "Jan")):
            document = next(
                d for d in documents if d.friendly_name == f"RTMLZHBSPP_{year}"
            )
            cache = output / "cache"
            cache.mkdir(exist_ok=True)
            path = cache / f"13061-{document.document_id}.zip"
            if not path.exists():
                source = args.source_evidence / f"{document.friendly_name}.zip"
                source_receipt = (
                    args.source_evidence / f"{document.friendly_name}-receipt.json"
                )
                source_listing = json.loads(
                    (args.source_evidence / "rt-annual-list.json").read_text()
                )
                original = next(
                    entry["Document"]
                    for entry in source_listing["ListDocsByRptTypeRes"]["DocumentList"]
                    if entry["Document"]["DocID"] == document.document_id
                )
                assert (
                    datetime.datetime.fromisoformat(original["PublishDate"])
                    == document.published_at
                )
                assert original["FriendlyName"] == document.friendly_name
                assert original["SecurityStatus"] == "P"
                raw = source.read_bytes()
                receipt = json.loads(source_receipt.read_text())
                assert len(raw) == document.byte_count == receipt["byte_count"]
                assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
                identity = asdict(document)
                identity["published_at"] = document.published_at.isoformat()
                with path.open("xb") as stream:
                    stream.write(raw)
                with path.with_suffix(".json").open("x") as stream:
                    json.dump({"document": identity, "receipt": receipt}, stream)
            download = client.download(document, cache=cache)
            assert download.cache_hit
            with closing(iter_rt_archive(download, sheets=[sheet], max_rows=5)) as rows:
                sample = list(islice(rows, 4))
            assert len(sample) == 4
            assert all(record.row.delivery_date.year == year for record in sample)
            reused = client.download(document, cache=output / "cache")
            assert reused.cache_hit and reused.receipt == download.receipt
            records.append(
                {
                    "document": asdict(document),
                    "download": asdict(download.receipt),
                    "initial_cache_hit": download.cache_hit,
                    "cache_reuse_verified": True,
                    "sheet": sheet,
                    "typed_rows": len(sample),
                    "complete_file_iteration": False,
                }
            )
    (output / "receipts.json").write_text(
        json.dumps(
            {
                "installed_package": str(package),
                "listing": asdict(listing),
                "samples": records,
                "authenticated_requests": 0,
                "all_history_extraction": False,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    print(
        "Installed RT archive probe passed: two four-row samples; cache reuse verified."
    )


if __name__ == "__main__":
    main()
