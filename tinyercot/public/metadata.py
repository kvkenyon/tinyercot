"""Explicit public product and artifact discovery, separate from typed row coverage."""

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from tinyercot.catalog import Access, classify_access, operations

from ._http import Receipt, SchemaMismatchError
from .api import BASE, PublicClient

# Current product metadata still says Active; audited retirement notices prevail.
RETIRED_PRODUCTS = frozenset({"NP4-179-CD", "NP3-990-EX"})


@dataclass(frozen=True)
class Artifact:
    """One source artifact link, without an inferred response schema.

    Attributes:
        report_type_id: Source report identity.
        display_name: Source artifact title.
        path: Same-service endpoint path, or None when no endpoint is advertised.
    """

    report_type_id: int
    display_name: str
    path: str | None


@dataclass(frozen=True)
class Product:
    """Source product metadata with independent access and lifecycle evidence.

    Attributes:
        emil_id: Source product identity, without case conversion.
        name: Source product title.
        status: Source lifecycle status; does not override retirement notices.
        access: Source security classification, independent of authentication.
        content_type: DATA or BINARY as advertised by ERCOT.
        artifacts: Source artifact links; a link does not verify a row schema.
        raw: Original public product metadata, including additional fields.
    """

    emil_id: str
    name: str
    status: str
    access: Access
    content_type: str
    artifacts: tuple[Artifact, ...]
    raw: dict[str, Any] = field(repr=False, compare=False)


def decode_product(body: Any) -> Product:
    """Validate observed product identities without guessing optional metadata.

    Args:
        body: One public product metadata object.

    Returns:
        Required identities, access evidence and artifact links with raw metadata.

    Raises:
        SchemaMismatchError: Required metadata or same-service links differ.
    """
    try:
        for name in ("emilId", "name", "status", "contentType"):
            if type(body[name]) is not str or not body[name]:
                raise ValueError
        source = body.get("securityClassification")
        if source is not None and type(source) is not str:
            raise ValueError
        audience = body.get("audience")
        if audience is not None and type(audience) is not str:
            raise ValueError
        access = classify_access(source)
        audience_access = classify_access(audience)
        if Access.RESTRICTED in (access, audience_access):
            access = Access.RESTRICTED
        elif access is not Access.PUBLIC or audience_access is not Access.PUBLIC:
            access = Access.UNKNOWN
        artifacts = []
        for artifact in body["artifacts"]:
            if (
                type(artifact["reportTypeId"]) is not int
                or type(artifact["displayName"]) is not str
            ):
                raise ValueError
            endpoint = artifact.get("_links", {}).get("endpoint", {}).get("href")
            path = None
            if endpoint is not None:
                url = urlsplit(endpoint)
                if (
                    url.scheme != "https"
                    or url.netloc != "api.ercot.com"
                    or url.query
                    or url.fragment
                    or not url.path.startswith(
                        "/api/public-reports/" + body["emilId"].lower() + "/"
                    )
                ):
                    raise ValueError
                path = url.path.removeprefix("/api/public-reports")
                if not re.fullmatch(r"/[a-z0-9-]+/[a-zA-Z0-9_]+", path):
                    raise ValueError
            artifacts.append(
                Artifact(artifact["reportTypeId"], artifact["displayName"], path)
            )
        return Product(
            body["emilId"],
            body["name"],
            body["status"],
            access,
            body["contentType"],
            tuple(artifacts),
            dict(body),
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        raise SchemaMismatchError(
            "Public product metadata differs from its observed contract"
        ) from None


class MetadataClient(PublicClient):
    """An opt-in Public Reports metadata client; row schemas remain independent."""

    def products(self) -> tuple[tuple[Product, ...], Receipt]:
        """Fetch the public product root without following artifact links.

        Returns:
            Source-order product metadata and exact response provenance.

        Raises:
            PublicDataError: Access, transport, byte limits, or metadata fail.
        """
        payload = self._authenticated_payload("/", {})
        try:
            raw = payload.json()["_embedded"]["products"]
            if not isinstance(raw, list):
                raise TypeError
            products = tuple(decode_product(item) for item in raw)
            if len({p.emil_id for p in products}) != len(products):
                raise ValueError
            return products, payload.receipt
        except (KeyError, TypeError, ValueError):
            raise SchemaMismatchError(
                "Public product root differs from its observed contract"
            ) from None

    def product(self, emil_id: str) -> tuple[Product, Receipt]:
        """Fetch one product already present in the offline public path inventory.

        Args:
            emil_id: Case-insensitive observed Public Reports product identity.

        Returns:
            Source metadata and its exact public response receipt.

        Raises:
            ValueError: The product is outside the observed public inventory.
            PublicDataError: Retrieval or metadata validation fails.
        """
        known = {
            op.path.split("/")[1]
            for op in operations(service="public-reports")
            if op.kind == "data"
        }
        if emil_id.lower() not in known:
            raise ValueError("Product is outside the observed public inventory")
        payload = self._authenticated_payload("/" + emil_id.lower(), {})
        product = decode_product(payload.json())
        if (
            product.emil_id.lower() != emil_id.lower()
            or not payload.receipt.source_url.startswith(BASE)
        ):
            raise SchemaMismatchError("Product identity differs from the request")
        return product, payload.receipt
