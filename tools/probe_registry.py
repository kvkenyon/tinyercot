"""Verify bounded current and historical selections through an installed registry."""

import argparse
import json
import logging
import stat
import sys
from dataclasses import asdict
from importlib.metadata import distribution
from pathlib import Path

import tinyercot
from tinyercot.public import Credentials, ReportsClient, StreamingLimits
from tinyercot.public._schemas import ENDPOINTS


def main() -> None:
    """Run one explicit installed-client batch and save public receipts only.

    Raises:
        SystemExit: Consent, installation, credentials, or retrieval checks fail.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if not args.live or not 1 <= args.count <= 20 or args.start < 0:
        raise SystemExit("Explicit --live and a 1–20 operation batch are required")
    if (
        Path(tinyercot.__file__).resolve().parent
        == Path(__file__).resolve().parents[1] / "tinyercot"
    ):
        raise SystemExit("Run with an isolated installed wheel")
    module = Path(tinyercot.__file__).resolve()
    dist = distribution("tinyercot")
    origin = json.loads(dist.read_text("direct_url.json") or "{}")
    if (
        not sys.flags.isolated
        or not module.is_relative_to(Path(sys.prefix).resolve())
        or "site-packages" not in module.parts
        or "archive_info" not in origin
    ):
        raise SystemExit(
            "Proof requires -I and an installed wheel in this interpreter's environment"
        )
    path = args.credentials_file
    if (
        path.is_symlink()
        or not path.is_file()
        or stat.S_IMODE(path.stat().st_mode) != 0o600
    ):
        raise SystemExit("Credentials require a regular mode-0600 file")
    logging.disable(logging.CRITICAL)
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        values = {
            key: json.loads(value)
            for line in path.read_text().splitlines()
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
        endpoints = [ep for ep in ENDPOINTS if "product_evidence" in ep.contract]
        with ReportsClient(
            credentials, limits=StreamingLimits(max_requests=90)
        ) as client:
            for endpoint in endpoints[args.start : args.start + args.count]:
                output = args.output / (
                    endpoint.path.strip("/").replace("/", "--") + ".json"
                )
                if output.exists():
                    continue
                temporal = [
                    field["name"]
                    for field in endpoint.contract["fields"]
                    if field["dataType"] in {"DATE", "DATETIME"}
                    and field.get("sortable")
                ]
                sort = temporal[0] if temporal else None
                records = []
                for period, direction in (("latest", "desc"), ("oldest", "asc")):
                    try:
                        page = client.page(
                            endpoint, size=1, sort=sort, direction=direction
                        )
                        records.append(
                            {
                                "period": period,
                                "status": "typed" if page.rows else "empty",
                                "rows": len(page.rows),
                                "sort": sort,
                                "source_time": str(getattr(page.rows[0], sort))
                                if page.rows and sort
                                else None,
                                "receipt": asdict(page.receipt),
                            }
                        )
                        print(
                            endpoint.path,
                            period,
                            "typed rows",
                            len(page.rows),
                            flush=True,
                        )
                    except Exception as error:  # noqa: BLE001 - Never expose credential-bearing request objects.
                        records.append(
                            {
                                "period": period,
                                "status": "failed",
                                "error_type": type(error).__name__,
                            }
                        )
                        print(endpoint.path, period, type(error).__name__, flush=True)
                output.write_text(
                    json.dumps(
                        {
                            "path": endpoint.path,
                            "installed_module": str(tinyercot.__file__),
                            "records": records,
                        },
                        indent=2,
                        default=str,
                    )
                    + "\n"
                )
    except Exception as error:  # noqa: BLE001 - Credential consumer must redact third-party failures.
        raise SystemExit(
            f"Installed registry probe failed: {type(error).__name__}"
        ) from None


if __name__ == "__main__":
    main()
