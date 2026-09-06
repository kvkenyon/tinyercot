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
        status: Covered scope, pending work, retirement, or access boundary.
        scope: What the status covers and what it does not establish.
        source_urls: Primary ERCOT references for this entry.
        product_ids: Relevant source product identifiers, where established.
    """

    key: str
    title: str
    status: Literal[
        "covered", "pending", "deferred", "retired", "restricted", "unavailable"
    ]
    scope: str
    source_urls: tuple[str, ...]
    product_ids: tuple[str, ...] = ()


def coverage() -> tuple[Coverage, ...]:
    """List all audited families, API operations, and supported web subsets.

    Returns:
        Immutable scope records. A covered endpoint or web subset does not mark
        its entire family covered. Pending or unknown schemas grant no access.
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
        metadata_scope = (
            {
                "/": "Installed product-root retrieval: 116 metadata identities with independent public-access and lifecycle checks; no row schema inferred.",
                "/archive/{emilId}": "Installed public archive listings for DME and two retired products. First-page listings preserve source totals; no claim of all documents fetched.",
                "/bundle/{emilId}": "Installed DAM monthly bundle listing: 103 file identities. Bundle transfer remains unverified after one unsuccessful bounded attempt.",
            }.get(operation.path)
            if operation.service == "public-reports" and operation.method == "GET"
            else None
        )
        supported = (operation.service, operation.method, operation.path) in {
            ("public-reports", "GET", endpoint.path) for endpoint in ENDPOINTS
        }
        entries.append(
            Coverage(
                f"api:{operation.service}:{operation.method}:{operation.path}",
                operation.path,
                "covered" if supported or metadata_scope else "pending",
                metadata_scope
                or (
                    "Observed required fields, explicitly observed nullability, and generated query filters; opt-in complete page/row iteration with explicit budgets. Two bounded source selections verified through the installed wheel; oldest chronology requires a temporal sort. No full-history, as-of, or schema-epoch guarantee."
                    if supported
                    else "Active public coverage work. No verified typed row contract for this operation; missing schemas remain unsupported. Retirement and document/history access are tracked separately."
                ),
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
    for key, title, scope, url, product in (
        (
            "resource-dme",
            "Public Resource DME CSV documents",
            "Exact seven-column string schema decoded from two verified current/oldest listed source ZIPs through the installed wheel. Document transfers observed during discovery; installed decoding reused captures. Generic archive files remain row-schema unknown.",
            "https://www.ercot.com/mp/data-products/data-product-details?id=np3-988-er",
            "NP3-988-ER",
        ),
        (
            "rt-annual",
            "Public RT annual ZIP/XLSX retrieval",
            "Report 13061 listing and bounded streaming worksheet iteration. Installed-client listing and cached 2010/2026 source decoding verified. Complete requested file iteration is opt-in; no full-year extraction occurred.",
            "https://www.ercot.com/mp/data-products/data-product-details?id=np6-785-er",
            "NP6-785-ER",
        ),
        (
            "fuel-mix",
            "Public rolling fuel mix",
            "Typed source fuel values and timestamps from one bounded installed-client snapshot; no historical API or automatic polling.",
            "https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json",
            "GEN-544-UI",
        ),
        (
            "grid-conditions",
            "Public rolling grid conditions and PRC",
            "Typed condition and PRC rows with source freshness from one bounded installed-client snapshot; no historical API or automatic polling.",
            "https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json",
            "GEN-543-UI",
        ),
        (
            "generation-outages",
            "Public generation outage aggregates",
            "Typed current/previous day outage aggregates, source timestamps and freshness from one bounded installed-client snapshot; no unit-private telemetry.",
            "https://www.ercot.com/api/1/services/read/dashboards/generation-outages.json",
            "GEN-546-UI",
        ),
        (
            "dc-tie-flows",
            "Public rolling DC tie aggregates",
            "Typed signed public flow series with source epoch/offset validation from one bounded installed-client snapshot; no private telemetry or historical API.",
            "https://www.ercot.com/api/1/services/read/dashboards/dc-tie-flows.json",
            "GEN-538-UI",
        ),
    ):
        entries.append(
            Coverage(f"web:{key}", title, "covered", scope, (url,), (product,))
        )
    return tuple(entries)
