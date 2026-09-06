"""Explicit installed-wheel archive metadata and cached typed CSV verification."""

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
from tinyercot.catalog import Access
from tinyercot.public import Credentials, Limits
from tinyercot.public._http import PublicDataError, Receipt, SchemaMismatchError
from tinyercot.public.api_archives import APIArchive, APIArchiveClient, APIArchiveFile
from tinyercot.public.archives import checked_zip
from tinyercot.public.resource_dme import iter_resource_dme


def cached_file(evidence: Path, document: APIArchive) -> APIArchiveFile:
    """Bind an existing selected source ZIP to its original receipt and metadata.

    Args:
        evidence: Directory containing the bounded discovery ZIPs and receipts.
        document: Unchanged public document from a newly fetched archive listing.

    Returns:
        A receipt-verified source file without another document request.

    Raises:
        PublicDataError: Selection, receipt, size, or ZIP structure differs.
        OSError: A required source evidence file is missing or unreadable.
    """
    path = evidence / f"download--np3-988-er--{document.document_id}.zip"
    receipt_path = path.with_suffix(".receipt.json")
    if (
        path.is_symlink()
        or receipt_path.is_symlink()
        or path.stat().st_size > 4_000_000
        or receipt_path.stat().st_size > 16_000
    ):
        raise SchemaMismatchError("Discovery file identity or size is unsupported")
    original = json.loads((evidence / "archive--np3-988-er.json").read_text())
    selected = next(
        item for item in original["archives"] if item["docId"] == document.document_id
    )
    if (
        document.emil_id != "np3-988-er"
        or selected["friendlyName"] != document.friendly_name
        or selected["postDatetime"] != document.post_datetime
    ):
        raise SchemaMismatchError("Selected source document metadata changed")
    raw = path.read_bytes()
    record = json.loads(receipt_path.read_text())
    record["retrieved_at"] = datetime.datetime.fromisoformat(record["retrieved_at"])
    receipt = Receipt(**record)
    if (
        receipt.retrieved_at.tzinfo is None
        or receipt.status != 200
        or receipt.source_url
        != "https://api.ercot.com/api/public-reports/archive/np3-988-er/download"
        or receipt.sha256 != hashlib.sha256(raw).hexdigest()
        or receipt.byte_count != len(raw)
    ):
        raise SchemaMismatchError("Discovery archive differs from its receipt")
    with checked_zip(raw, max_members=4, max_expanded_bytes=4_000_000) as archive:
        members = tuple(
            item.filename for item in archive.infolist() if not item.is_dir()
        )
    return APIArchiveFile(document, receipt, members, raw)


def main() -> None:
    """Verify installed metadata/CSV contracts and write credential-free evidence.

    Raises:
        SystemExit: Opt-in, installation, credential, or required verification fails.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retired-history", action="store_true")
    parser.add_argument("--download-oldest-bundle", action="store_true")
    args = parser.parse_args()
    installed = Path(tinyercot.__file__).resolve()
    if "site-packages" not in installed.parts:
        raise SystemExit("Run with an isolated installed-wheel interpreter using -I")
    credential_file = args.credentials_file
    if (
        credential_file.is_symlink()
        or not credential_file.is_file()
        or stat.S_IMODE(credential_file.stat().st_mode) != 0o600
        or credential_file.stat().st_size > 16_000
    ):
        raise SystemExit("Credentials require an existing regular mode-0600 file")
    logging.disable(logging.CRITICAL)
    args.output.mkdir(parents=True, exist_ok=True)
    records = {
        "installed_module": str(installed),
        "checks": [],
        "all_history_extraction": False,
    }

    def save(kind, **data):
        records["checks"].append({"kind": kind, **data})
        (args.output / "receipts.json").write_text(
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
        with APIArchiveClient(
            credentials,
            limits=Limits(max_requests=10, max_bytes=16_000_000, attempts=1),
        ) as client:
            products, root_receipt = client.products()
            save(
                "installed-public-root",
                product_count=len(products),
                receipt=asdict(root_receipt),
            )
            page = client.archives("NP3-988-ER")
            save(
                "installed-archive-listing",
                emil_id="NP3-988-ER",
                documents=len(page.documents),
                total_records=page.total_records,
                lifecycle=page.lifecycle,
                receipt=asdict(page.receipt),
            )
            for identity in (1270779234, 1166614741):
                document = next(
                    item for item in page.documents if item.document_id == identity
                )
                archive = cached_file(args.evidence, document)
                with closing(iter_resource_dme(archive)) as iterator:
                    rows = list(islice(iterator, 4))
                assert len(rows) == 4
                assert all(
                    isinstance(value, str)
                    for record in rows
                    for value in record.row.model_dump().values()
                )
                save(
                    "installed-cached-typed-dme",
                    document=asdict(document),
                    typed_rows=len(rows),
                    receipt=asdict(archive.receipt),
                    network_download=False,
                )
            bundles = client.bundles("NP4-190-CD")
            save(
                "installed-bundle-listing",
                emil_id="NP4-190-CD",
                documents=len(bundles.documents),
                total_records=bundles.total_records,
                receipt=asdict(bundles.receipt),
            )
            if args.retired_history:
                for identity in ("NP4-179-CD", "NP3-990-EX"):
                    source = next(
                        (
                            product
                            for product in products
                            if product.emil_id == identity
                        ),
                        None,
                    )
                    if source is None or source.access is not Access.PUBLIC:
                        save(
                            "retired-history-boundary",
                            emil_id=identity,
                            result="absent-or-nonpublic",
                            requested=False,
                        )
                        continue
                    try:
                        history = client.archives(identity)
                        save(
                            "installed-retired-history-listing",
                            emil_id=identity,
                            documents=len(history.documents),
                            total_records=history.total_records,
                            lifecycle=history.lifecycle,
                            receipt=asdict(history.receipt),
                        )
                    except PublicDataError as error:
                        save(
                            "retired-history-boundary",
                            emil_id=identity,
                            result=type(error).__name__,
                            requested=True,
                        )
            if args.download_oldest_bundle:
                oldest = min(
                    bundles.documents, key=lambda document: document.post_datetime
                )
                try:
                    path = args.output / f"bundle-np4-190-cd-{oldest.document_id}.zip"
                    if path.exists() or path.is_symlink():
                        raise SchemaMismatchError(
                            "Existing bundle output requires explicit receipt review"
                        )
                    bundle = client.download_bundle(oldest)
                    with path.open("xb") as stream:
                        stream.write(bundle.body)
                    save(
                        "installed-single-bundle-transfer",
                        document=asdict(oldest),
                        receipt=asdict(bundle.receipt),
                        members=list(bundle.members),
                        row_schema=bundle.row_schema,
                        typed_rows=0,
                    )
                except PublicDataError as error:
                    save(
                        "selected-bundle-boundary",
                        document=asdict(oldest),
                        result=type(error).__name__,
                        detail=str(error),
                        response_byte_limit=16_000_000,
                        typed_rows=0,
                    )
    except (
        PublicDataError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AssertionError,
        StopIteration,
    ) as error:
        save("required-probe-failure", error_type=type(error).__name__)
        raise SystemExit(
            f"Installed archive probe failed ({type(error).__name__}); see receipt evidence"
        ) from None
    print(
        "Installed archive metadata and cached DME typing probe completed; see receipt evidence."
    )


if __name__ == "__main__":
    main()
