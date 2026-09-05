"""Opt-in offline metadata for observed public ERCOT sources.

This module does not fetch data or verify current response schemas. Public API
data requests still require ERCOT account authentication. Source classification
does not grant entitlement. See docs/public-foundation.md for snapshot limits.
"""

import json
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from typing import Literal

__all__ = [
    "Access",
    "Operation",
    "SourceCapability",
    "classify_access",
    "operations",
    "sources",
]


class Access(str, Enum):
    """Access evidence for a source, independent of adapter implementation."""

    PUBLIC = "public"
    RESTRICTED = "restricted"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


def classify_access(security_classification: str | None) -> Access:
    """Classify an EMIL security label without inferring public access.

    Args:
        security_classification: The source label, or None for absent evidence.

    Returns:
        Public for Public, restricted for Secure or Certified, otherwise unknown.
        This function does not determine source availability or user entitlement.
    """
    label = (security_classification or "").strip().casefold()
    if label == "public":
        return Access.PUBLIC
    if label in {"secure", "certified"}:
        return Access.RESTRICTED
    return Access.UNKNOWN


@dataclass(frozen=True)
class Operation:
    """An observed API operation in the immutable Stage-0 metadata snapshot.

    Attributes:
        service: ERCOT route namespace: public-reports or public-data (ESR).
        path: Exact source path, including any path parameter placeholders.
        method: HTTP verb from the source specification.
        kind: Data endpoint or generic service operation.
        legacy_path: Whether the frozen legacy client exposes this path.
        row_schema: Cache evidence only; no value certifies current row types.
        query_drift: Audited legacy query change, including order-only changes.
            None means that no legacy comparison applies.
        request_media: Documented request body media types.
        response_media: Documented success response media types.
        source_url: Public OpenAPI export used for this observation.
        observed_at: Audit date; not a data publication or availability date.
        access: Public source classification; API authentication is still needed.
        support: Metadata only. See tinyercot.public.coverage for opt-in
            retrieval support.
    """

    service: str
    path: str
    method: str
    kind: Literal["data", "service"]
    legacy_path: bool
    row_schema: Literal["cached_unverified", "missing", "not_applicable"]
    query_drift: Literal["contract", "order_only", "unchanged"] | None
    request_media: tuple[str, ...]
    response_media: tuple[str, ...]
    source_url: str
    observed_at: str
    access: Access = Access.PUBLIC
    support: Literal["metadata_only"] = "metadata_only"


def operations(*, service: str | None = None) -> tuple[Operation, ...]:
    """Read the bundled operation inventory without credentials or requests.

    Args:
        service: Exact route namespace to filter, or None for both public APIs.
            An unknown namespace returns an empty tuple.

    Returns:
        Immutable Stage-0 observations from 2026-09-05. These records do not
        establish retrieval support. See tinyercot.public.coverage for that.
    """
    snapshot = json.loads(files("tinyercot").joinpath("_catalog.json").read_text())
    return tuple(
        Operation(
            **{
                k: v
                for k, v in row.items()
                if k not in {"request_media", "response_media"}
            },
            request_media=tuple(row["request_media"]),
            response_media=tuple(row["response_media"]),
            source_url=snapshot["sources"][row["service"]]["url"],
            observed_at=snapshot["observed_at"],
        )
        for row in snapshot["operations"]
        if service is None or row["service"] == service
    )


@dataclass(frozen=True)
class SourceCapability:
    """A selected delivery source or explicit public-access boundary.

    Attributes:
        source_id: TinyERCOT metadata key, not an official ERCOT product ID.
        access: Public, restricted, unavailable, or unknown source evidence.
        delivery: Separate route for future API, MIS, live, or website adapters.
        authentication: Source access requirement, not a credential request.
        source_url: Primary ERCOT reference for the boundary.
        note: Scope and limitations; does not claim successful data retrieval.
        support: Metadata only; no adapter exists on this opt-in surface.
        observed_at: Audit date, not an availability or publication timestamp.
    """

    source_id: str
    access: Access
    delivery: str
    authentication: str
    source_url: str
    note: str
    support: Literal["metadata_only"] = "metadata_only"
    observed_at: str = "2026-09-05"


def sources() -> tuple[SourceCapability, ...]:
    """Describe selected public delivery paths and excluded access boundaries.

    Returns:
        Immutable metadata, not a complete EMIL catalog or retrieval support.
        Restricted records describe exclusions only. Unknown records grant no
        access. Public aggregates do not expose original private records.
    """
    return (
        SourceCapability(
            "public-api",
            Access.PUBLIC,
            "api",
            "ercot_account",
            "https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication/",
            "Public content requires an ID token and subscription key for data requests.",
        ),
        SourceCapability(
            "mis-files",
            Access.PUBLIC,
            "mis",
            "none",
            "https://www.ercot.com/mp/data-products/data-product-details?id=np4-180-er",
            "Selected public file listings exist. No file adapter or history guarantee.",
        ),
        SourceCapability(
            "live-feeds",
            Access.PUBLIC,
            "live",
            "none",
            "https://www.ercot.com/gridmktinfo/dashboards",
            "Public aggregate dashboard feeds are rolling views, not historical archives.",
        ),
        SourceCapability(
            "load-2001",
            Access.UNAVAILABLE,
            "website",
            "none",
            "https://www.ercot.com/gridinfo/load/load_hist",
            "ERCOT states that hourly load data for 2001 is unavailable.",
        ),
        SourceCapability(
            "secure-products",
            Access.RESTRICTED,
            "participant",
            "entitlement",
            "https://www.ercot.com/mp/data-products/data-product-details?id=np4-500-sg",
            "Secure network/model products and ECEII are outside public scope.",
        ),
        SourceCapability(
            "certified-products",
            Access.RESTRICTED,
            "participant",
            "entitlement",
            "https://www.ercot.com/mp/data-products/data-product-details?id=np9-170-sg",
            "Certified participant settlements and customer data are outside public scope.",
        ),
        SourceCapability(
            "ews-private-records",
            Access.RESTRICTED,
            "participant",
            "entitlement",
            "https://developer.ercot.com/applications/ews/Services%20Organization/",
            "EWS, private telemetry, bids, COP, and awards are excluded. Public delayed "
            "disclosures and aggregates do not grant access to these original records.",
        ),
        SourceCapability(
            "unclassified-products",
            Access.UNKNOWN,
            "unknown",
            "unknown",
            "https://www.ercot.com/mp/data-products",
            "Missing or unrecognized security labels do not establish public access.",
        ),
    )
