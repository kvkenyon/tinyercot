"""Collect bounded public metadata and one-row observations with explicit consent.

This developer command never generates models. Exact public bytes and receipts
are saved for offline review; credentials and auth payloads are never retained.
"""

import argparse
import datetime
import hashlib
import json
import logging
import stat
from dataclasses import asdict
from pathlib import Path

from tinyercot.catalog import operations
from tinyercot.public import Credentials, PublicClient, StreamingLimits
from tinyercot.public.metadata import RETIRED_PRODUCTS


def verified_capture(path: Path, receipt_path: Path, expected_url: str) -> dict:
    """Read exact public metadata only after checking its source receipt.

    Args:
        path: Captured public JSON payload.
        receipt_path: Corresponding public-only receipt.
        expected_url: Exact adapter-selected source URL.

    Returns:
        Parsed metadata whose URL, status, byte count and hash agree.

    Raises:
        ValueError: The receipt is unverified or contains unexpected metadata.
    """
    raw = path.read_bytes()
    receipt = json.loads(receipt_path.read_text())
    if (
        set(receipt) - {"source_url", "retrieved_at", "sha256", "byte_count", "status"}
        or receipt["source_url"] != expected_url
        or receipt["status"] != 200
        or receipt["byte_count"] != len(raw)
        or receipt["sha256"] != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError("Cached metadata lacks matching public provenance")
    return json.loads(raw)


def main() -> None:
    """Collect a selected public metadata batch without expanding its scope.

    Raises:
        SystemExit: Consent, credentials, source identity, or request checks fail.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", action="store_true")
    parser.add_argument("--products", nargs="*", default=[])
    parser.add_argument("--metadata-paths", nargs="*", default=[])
    parser.add_argument("--download", nargs=2, metavar=("PRODUCT", "DOC_ID"))
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--samples", action="store_true")
    parser.add_argument("--max-requests", type=int, default=60)
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()
    if args.samples:
        catalog = json.loads(
            (
                Path(__file__).resolve().parents[1] / "tinyercot/_catalog.json"
            ).read_text()
        )
        if (
            args.spec is None
            or hashlib.sha256(args.spec.read_bytes()).hexdigest()
            != catalog["sources"]["public-reports"]["sha256"]
        ):
            raise SystemExit("Sampling requires the pinned current OpenAPI export")
    if not args.live or not 1 <= args.max_requests <= 100:
        raise SystemExit("Explicit --live and a 1–100 request budget are required")
    if not 1 <= args.attempts <= 3:
        raise SystemExit("Choose one to three transport attempts per request")
    known = {
        op.path for op in operations(service="public-reports") if op.kind == "data"
    }
    products = {path.split("/")[1] for path in known}
    if len(args.products) > 20 or set(args.products) - products:
        raise SystemExit("Select at most 20 observed public products")
    credential_file = args.credentials_file
    if (
        credential_file.is_symlink()
        or not credential_file.is_file()
        or stat.S_IMODE(credential_file.stat().st_mode) != 0o600
    ):
        raise SystemExit("Credentials require a regular mode-0600 file")
    logging.disable(logging.CRITICAL)
    args.output.mkdir(parents=True, exist_ok=True)
    root_path = args.output / "root.json"
    cached_root = (
        verified_capture(
            root_path,
            args.output / "root-receipt.json",
            "https://api.ercot.com/api/public-reports/",
        )
        if root_path.exists()
        else None
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
        with PublicClient(
            credentials,
            limits=StreamingLimits(
                max_requests=args.max_requests, attempts=args.attempts
            ),
        ) as client:
            if args.root:
                payload = client._authenticated_payload("/", {})
                (args.output / "root.json").write_bytes(payload.body)
                (args.output / "root-receipt.json").write_text(
                    json.dumps(asdict(payload.receipt), indent=2, default=str) + "\n"
                )
                print(
                    "Root public metadata saved", len(payload.body), "bytes", flush=True
                )
            if args.metadata_paths or args.download:
                root = verified_capture(
                    root_path,
                    args.output / "root-receipt.json",
                    "https://api.ercot.com/api/public-reports/",
                )
                public = {
                    p["emilId"].lower()
                    for p in root["_embedded"]["products"]
                    if p["securityClassification"] == p["audience"] == "Public"
                }
                for path in args.metadata_paths:
                    if path not in {
                        f"/{kind}/{product}"
                        for product in public
                        for kind in ("archive", "bundle")
                    }:
                        raise ValueError("Unsupported metadata path")
                    payload = client._authenticated_payload(path, {})
                    target = args.output / (
                        path.strip("/").replace("/", "--") + ".json"
                    )
                    target.write_bytes(payload.body)
                    target.with_name(target.stem + "-receipt.json").write_text(
                        json.dumps(asdict(payload.receipt), indent=2, default=str)
                        + "\n"
                    )
                    print(path, "metadata bytes", len(payload.body), flush=True)
                if args.download:
                    product, document = args.download
                    listing = verified_capture(
                        args.output / ("archive--" + product + ".json"),
                        args.output / ("archive--" + product + "-receipt.json"),
                        "https://api.ercot.com/api/public-reports/archive/" + product,
                    )
                    if (
                        product not in public
                        or not document.isdigit()
                        or int(document)
                        not in {row["docId"] for row in listing["archives"]}
                        or listing["product"]["emilId"].lower() != product
                    ):
                        raise ValueError("Download lacks public listing evidence")
                    payload = client._authenticated_payload(
                        "/archive/" + product + "/download",
                        {},
                        method="POST",
                        json_body={"docIds": [int(document)]},
                    )
                    target = args.output / (
                        "download--" + product + "--" + document + ".zip"
                    )
                    target.write_bytes(payload.body)
                    target.with_suffix(".receipt.json").write_text(
                        json.dumps(asdict(payload.receipt), indent=2, default=str)
                        + "\n"
                    )
                    print(
                        "Selected public download",
                        len(payload.body),
                        "bytes",
                        flush=True,
                    )
            for product in args.products:
                file = args.output / (product + ".json")
                if file.exists():
                    body = verified_capture(
                        file,
                        file.with_name(product + "-receipt.json"),
                        "https://api.ercot.com/api/public-reports/" + product,
                    )
                elif (args.output / "root.json").exists():
                    root = cached_root or verified_capture(
                        root_path,
                        args.output / "root-receipt.json",
                        "https://api.ercot.com/api/public-reports/",
                    )
                    matches = [
                        item
                        for item in root["_embedded"]["products"]
                        if item["emilId"].lower() == product
                    ]
                    if len(matches) != 1:
                        print(product, "missing-or-ambiguous-product", flush=True)
                        continue
                    body = matches[0]
                else:
                    payload = client._authenticated_payload("/" + product, {})
                    body = payload.json()
                    file.write_bytes(payload.body)
                    file.with_name(product + "-receipt.json").write_text(
                        json.dumps(asdict(payload.receipt), indent=2, default=str)
                        + "\n"
                    )
                public = (
                    body.get("securityClassification")
                    == body.get("audience")
                    == "Public"
                )
                print(
                    product,
                    "metadata",
                    body.get("status"),
                    "public" if public else "restricted-or-unknown",
                    flush=True,
                )
                if (
                    not args.samples
                    or not public
                    or body.get("status") != "Active"
                    or body.get("emilId", "").upper() in RETIRED_PRODUCTS
                    or body.get("contentType") != "DATA"
                ):
                    continue
                spec = json.loads(args.spec.read_bytes())
                for artifact in body.get("artifacts", []):
                    url = artifact.get("_links", {}).get("endpoint", {}).get("href", "")
                    prefix = "https://api.ercot.com/api/public-reports"
                    path = url.removeprefix(prefix)
                    if (
                        not url.startswith(prefix)
                        or path not in known
                        or path.split("/")[1] != product
                    ):
                        print(product, "artifact-unavailable-or-unknown", flush=True)
                        continue
                    parameters = spec["paths"][path]["get"].get("parameters", [])
                    dates = [
                        p["name"][:-4]
                        for p in parameters
                        if p["name"].endswith("From")
                        and p.get("schema", {}).get("format")
                        in {"yyyy-MM-dd", "yyyy-MM-ddTH24:mm:ss"}
                    ]
                    sort = dates[0] if dates else None
                    for period, direction in (
                        ("current", "desc"),
                        ("historical", "asc"),
                    ):
                        target = args.output / (
                            path.strip("/").replace("/", "--") + "--" + period + ".json"
                        )
                        if target.exists():
                            continue
                        query = {"size": 1, "page": 1}
                        if sort:
                            query.update(sort=sort, dir=direction)
                        try:
                            payload = client._authenticated_payload(path, query)
                            target.write_bytes(payload.body)
                            target.with_name(target.stem + "-receipt.json").write_text(
                                json.dumps(
                                    asdict(payload.receipt), indent=2, default=str
                                )
                                + "\n"
                            )
                            response = payload.json()
                            print(
                                path,
                                period,
                                "rows",
                                len(response.get("data", [])),
                                "fields",
                                len(response.get("fields", [])),
                                flush=True,
                            )
                        except Exception as error:  # noqa: BLE001 - Never expose retained auth/request objects.
                            target.with_name(target.stem + "-failure.json").write_text(
                                json.dumps(
                                    {
                                        "path": path,
                                        "period": period,
                                        "error_type": type(error).__name__,
                                        "observed_at": str(
                                            datetime.datetime.now(datetime.UTC)
                                        ),
                                    },
                                    indent=2,
                                )
                                + "\n"
                            )
                            print(path, period, type(error).__name__, flush=True)
    except Exception as error:  # noqa: BLE001 - Sanitize all credential-consumer failures.
        raise SystemExit(f"Public observation failed: {type(error).__name__}") from None


if __name__ == "__main__":
    main()
