"""Probe bounded ESR and archive contracts with an isolated installed wheel."""

import argparse
import datetime
import hashlib
import json
import logging
import stat
from contextlib import closing
from dataclasses import asdict
from itertools import islice
from pathlib import Path

import tinyercot
from tinyercot.public._http import Limits, PublicDataError, Receipt
from tinyercot.public.api import Credentials
from tinyercot.public.api_archives import APIArchive, APIArchiveFile, APIBundle
from tinyercot.public.archive_api import ArchiveAPIClient
from tinyercot.public.archive_rows import sample_capacity_bundle, sample_retired_offers
from tinyercot.public.esr_api import ESRAPIClient
from tinyercot.public.resource_dme import iter_resource_dme


def sample_cache(cache: Path, output: Path) -> None:
    """Verify installed decoders against exact prior public file receipts.

    Args:
        cache: Prior live probe output directory.
        output: New directory for typed sample evidence.

    Raises:
        SystemExit: The cache or receipt file is unsafe or too large.
        PublicDataError: Source bytes or CSV schemas differ.
    """
    path = cache / "receipts.json"
    if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > 1_000_000:
        raise SystemExit("Invalid cached receipt file")
    checks = json.loads(path.read_text())["checks"]
    records = []
    for check in checks:
        if "download_receipt" not in check:
            continue
        raw_receipt = dict(check["download_receipt"])
        raw_receipt["retrieved_at"] = datetime.datetime.fromisoformat(
            raw_receipt["retrieved_at"]
        )
        receipt = Receipt(**raw_receipt)
        kind = "bundle" if "/bundle/" in receipt.source_url else "archive"
        document = (APIBundle if kind == "bundle" else APIArchive)(**check["document"])
        path = cache / f"{kind}-{document.emil_id.upper()}.zip"
        if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > 4_000_000:
            raise SystemExit("Invalid cached public file")
        file = APIArchiveFile(
            document, receipt, tuple(check["members"]), path.read_bytes()
        )
        record = {
            "document": asdict(document),
            "receipt": asdict(receipt),
            "network_download": False,
            "installed_module": tinyercot.__file__,
        }
        if document.emil_id == "np3-988-er":
            with closing(iter_resource_dme(file)) as iterator:
                rows = list(islice(iterator, 4))
            record.update(
                typed_rows=len(rows),
                decoder="iter_resource_dme",
                rows=[r.row.model_dump() for r in rows],
            )
        else:
            decoder = (
                sample_capacity_bundle if kind == "bundle" else sample_retired_offers
            )
            sample = decoder(file, member=file.members[0], max_rows=4)
            record.update(
                typed_rows=len(sample.rows),
                decoder=decoder.__name__,
                sample=asdict(sample),
            )
        records.append(record)
    output.mkdir(parents=True)
    result = {
        "checks": records,
        "network_requests": 0,
        "runtime_sha256": {
            name: hashlib.sha256(
                (Path(tinyercot.__file__).parent / "public" / name).read_bytes()
            ).hexdigest()
            for name in ("archive_rows.py", "resource_dme.py")
        },
    }
    (output / "samples.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n"
    )
    print("Verified installed typed samples against cached public file receipts.")


def main() -> None:
    """Write safe public receipts for explicitly enabled bounded live requests.

    Raises:
        SystemExit: The wheel, credential file, or output path is invalid.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--sample-cache", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bundle-transfer", action="store_true")
    parser.add_argument(
        "--followup",
        action="store_true",
        help="Probe one capacity bundle and one retired public file",
    )
    args = parser.parse_args()
    installed = Path(tinyercot.__file__).resolve()
    if "site-packages" not in installed.parts:
        raise SystemExit("Use an isolated installed wheel with python -I")
    if args.output.exists():
        raise SystemExit("Select a new output directory")
    if args.sample_cache:
        sample_cache(args.sample_cache, args.output)
        return
    if not args.live or args.credentials_file is None:
        raise SystemExit("Live requests require --live and --credentials-file")
    path = args.credentials_file
    if (
        not stat.S_ISREG(path.lstat().st_mode)
        or stat.S_IMODE(path.stat().st_mode) != 0o600
        or path.stat().st_size > 16000
    ):
        raise SystemExit("Use a regular mode-0600 authorized local credential file")
    logging.disable(logging.CRITICAL)
    values = {
        k: json.loads(v)
        for line in path.read_text().splitlines()
        for k, v in [line.split("=", 1)]
    }
    credentials = Credentials(
        *(
            values[k]
            for k in (
                "ERCOT_USERNAME",
                "ERCOT_PASSWORD",
                "ERCOT_SUBSCRIPTION_KEY",
            )
        )
    )
    del values
    args.output.mkdir(parents=True)
    result = {
        "installed_module": str(installed),
        "checks": [],
        "bulk_history": False,
        "runtime_sha256": {
            name: hashlib.sha256(
                (installed.parent / "public" / name).read_bytes()
            ).hexdigest()
            for name in ("esr_api.py", "archive_api.py", "archive_http.py")
        },
    }

    def save():
        (args.output / "receipts.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n"
        )

    def check(client, name, action):
        start = len(client.exchanges)
        record = {"operation": name}
        try:
            record.update(action())
            record["outcome"] = "supported"
        except PublicDataError as error:
            record.update(outcome=type(error).__name__, reason=str(error))
        record["exchanges"] = [asdict(x) for x in client.exchanges[start:]]
        result["checks"].append(record)
        save()

    with ESRAPIClient(credentials, limits=Limits(max_requests=3, attempts=1)) as esr:

        def current():
            page = esr.current(size=1)
            (args.output / "esr-current.json").write_bytes(page.raw)
            return {
                "row_schema": page.row_schema,
                "meta": page.envelope["_meta"],
                "fields": page.envelope["fields"],
                "raw_list_entries": len(page.envelope["data"])
                if isinstance(page.envelope["data"], list)
                else None,
            }

        if not args.followup:
            check(esr, "GET ESR current size=1", current)

    with ArchiveAPIClient(
        credentials,
        limits=Limits(max_requests=12, max_bytes=4_000_000, attempts=1),
    ) as client:

        def root():
            products, receipt = client.products()
            return {
                "receipt": asdict(receipt),
                "products": [
                    {
                        "id": p.emil_id,
                        "access": p.access.value,
                        "status": p.status,
                        "content_type": p.content_type,
                        "row_schema": "not_assessed",
                        "file_access": "outstanding"
                        if p.access.value == "public"
                        else "blocked",
                    }
                    for p in products
                ],
            }

        check(client, "GET public product root", root)

        def history(identity, kind, transfer=False):
            page = (
                client.bundles(identity)
                if kind == "bundle"
                else client.archives(identity)
            )
            data = {
                "product_id": identity,
                "lifecycle": page.lifecycle,
                "documents": len(page.documents),
                "total_records": page.total_records,
                "page_size": page.page_size,
                "total_pages": page.total_pages,
                "current_page": page.current_page,
                "receipt": asdict(page.receipt),
                "row_schema": "unknown",
                "file_access": "supported_listing",
                "first_document": asdict(page.documents[0]) if page.documents else None,
                "last_document": asdict(page.documents[-1]) if page.documents else None,
            }
            result["checks"].append({"operation": f"GET {kind}/{identity}", **data})
            save()
            if transfer and page.documents:
                document = (
                    (max if args.followup else min)(
                        page.documents, key=lambda d: d.post_datetime
                    )
                    if kind == "bundle"
                    else page.documents[0]
                )
                result["checks"].append(
                    {"operation": "selected_document", **asdict(document)}
                )
                save()
                downloaded = (
                    client.download_bundle(document)
                    if kind == "bundle"
                    else client.download(document)
                )
                data.update(
                    document=asdict(document),
                    members=downloaded.members,
                    download_receipt=asdict(downloaded.receipt),
                    file_access="supported_zip",
                )
                (args.output / f"{kind}-{identity}.zip").write_bytes(downloaded.body)
            return data

        if args.followup:
            check(
                client,
                "public capacity bundle transfer",
                lambda: history("NP4-188-CD", "bundle", True),
            )
            check(
                client,
                "retired public file transfer",
                lambda: history("NP4-179-CD", "archive", True),
            )
            print("Wrote bounded follow-up installed-wheel receipts.")
            return

        check(
            client,
            "public archive representative transfer",
            lambda: history("NP3-988-ER", "archive", True),
        )
        check(
            client,
            "public bundle boundary",
            lambda: history("NP4-190-CD", "bundle", args.bundle_transfer),
        )
        for identity in ("NP4-179-CD", "NP3-990-EX", "NP4-765-ER"):
            check(
                client,
                f"public file metadata {identity}",
                lambda identity=identity: history(identity, "archive"),
            )
    print("Wrote bounded installed-wheel receipts; inspect each operation outcome.")


if __name__ == "__main__":
    main()
