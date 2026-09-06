"""Explicit scope states for every audited family and observed API operation."""

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from tinyercot.catalog import operations

from ._schemas import ENDPOINTS


@dataclass(frozen=True)
class Coverage:
    """An exact retrieval scope, separate from broad family completeness.

    Attributes:
        key: Stable source or operation identity, including service and verb.
        title: Human-readable family or implemented capability.
        status: Covered bounded scope, deferred work, restricted, or unavailable.
        scope: What the status covers and what it does not establish.
        source_urls: Primary ERCOT references for this entry.
        product_ids: Relevant source product identifiers, where established.
    """

    key: str
    title: str
    status: Literal["covered", "deferred", "restricted", "unavailable"]
    scope: str
    source_urls: tuple[str, ...]
    product_ids: tuple[str, ...] = ()


def coverage() -> tuple[Coverage, ...]:
    """List all audited families, API operations, and supported web subsets.

    Returns:
        Immutable scope records. A covered endpoint or web subset does not mark
        its entire family covered. Deferred or unknown schemas grant no access.
        The Stage-0 metadata catalog remains an unchanged observation snapshot.
    """
    snapshot = json.loads(
        files("tinyercot.public").joinpath("_coverage.json").read_text()
    )
    entries = [
        Coverage(
            **{k: v for k, v in row.items() if k not in {"source_urls", "product_ids"}},
            source_urls=tuple(row["source_urls"]),
            product_ids=tuple(row["product_ids"]),
        )
        for row in snapshot["families"]
    ]
    for operation in operations():
        supported = (operation.service, operation.method, operation.path) in {
            ("public-reports", "GET", endpoint.path) for endpoint in ENDPOINTS
        }
        entries.append(
            Coverage(
                f"api:{operation.service}:{operation.method}:{operation.path}",
                operation.path,
                "covered" if supported else "deferred",
                "Observed non-null row schema and generated query filters; opt-in complete page/row iteration with explicit budgets. Current and oldest-first samples verified; no full-history, as-of, or schema-epoch guarantee."
                if supported
                else "No opt-in retrieval implementation or verified current row contract.",
                (operation.source_url,),
            )
        )
    entries.extend(
        (
            Coverage(
                "web:dam-annual",
                "Public DAM annual ZIP/XLSX retrieval and iteration",
                "covered",
                "Report 13060 public listing, one selected file per call, receipt cache, worksheet sampling, and opt-in all-worksheet row iteration. Real 2010 and 2026 samples; complete multi-worksheet iteration verified with synthetic files only. No complete-year data guarantee.",
                (
                    "https://www.ercot.com/mp/data-products/data-product-details?id=np4-180-er",
                ),
                ("NP4-180-ER",),
            ),
            Coverage(
                "web:esr",
                "Public rolling ESR aggregates",
                "covered",
                "One snapshot with source offset/epoch validation and explicit freshness. No historical API or automatic polling.",
                (
                    "https://www.ercot.com/api/1/services/read/dashboards/energy-storage-resources.json",
                ),
                ("GEN-545-UI",),
            ),
        )
    )
    return tuple(entries)
