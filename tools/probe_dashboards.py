"""Capture each anonymous dashboard once through an isolated installed wheel.

Run /absolute/venv/bin/python -I tools/probe_dashboards.py --live --output PATH.
The explicit live flag is required. Output contains receipts and row counts,
never headers, credentials, raw response bodies, or continuous polling.
"""

import argparse
import datetime
import importlib.metadata
import json
import sys
from dataclasses import asdict
from pathlib import Path


def main() -> None:
    """Run exactly two bounded anonymous captures with installed-code checks.

    Raises:
        RuntimeError: The interpreter is not isolated or imports outside its venv.
        PublicDataError: A bounded capture or typed source decoding fails.
        OSError: The receipt output cannot be written.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error("--live is required for two anonymous ERCOT requests")
    if not sys.flags.isolated or sys.prefix == sys.base_prefix:
        raise RuntimeError("Use an isolated virtualenv interpreter with -I")

    from tinyercot.public import Limits, dashboards

    module_path = Path(dashboards.__file__).resolve()
    if Path(sys.prefix).resolve() not in module_path.parents:
        raise RuntimeError("Dashboard module was not imported from the installed venv")

    records = []
    with dashboards.DashboardClient(
        limits=Limits(max_requests=2, attempts=1)
    ) as client:
        for name, capture in (
            ("fuel_mix", client.fuel_mix),
            ("grid_conditions", client.grid_conditions),
        ):
            snapshot = capture()
            receipt = asdict(snapshot.receipt)
            receipt["retrieved_at"] = snapshot.receipt.retrieved_at.isoformat()
            records.append(
                {
                    "adapter": name,
                    "receipt": receipt,
                    "source_last_updated": snapshot.source_last_updated,
                    "typed_rows": len(snapshot.rows),
                    "stale_at_ten_minutes": snapshot.is_stale(),
                }
            )
    result = {
        "distribution_version": importlib.metadata.version("tinyercot"),
        "installed_module": str(module_path),
        "verified_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "authentication": "none",
        "scope": "Two rolling snapshots; no polling or historical extraction.",
        "captures": records,
    }
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("Installed wheel decoded two anonymous dashboard snapshots; receipts saved.")


if __name__ == "__main__":
    main()
