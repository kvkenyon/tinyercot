"""Public Reports archive metadata and one explicitly selected ZIP download.

Source: https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview
Only archive metadata is typed here. Binary file row schemas remain unknown.
"""

import datetime
import re
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Literal, cast

from tinyercot.catalog import Access

from ._http import (
    AccessDeniedError,
    Receipt,
    SchemaMismatchError,
)
from .api import BASE
from .archives import checked_zip
from .metadata import MetadataClient, Product

# Retirement is lifecycle evidence, not an entitlement or history-availability gate.
_RETIRED = frozenset(
    {"np4-179-cd", "np3-990-ex", "np6-569-cd", "np6-655-cd", "np6-913-cd"}
)


@dataclass(frozen=True)
class APIArchive:
    """One publicly listed archive document, without an inferred file schema.

    Attributes:
        emil_id: Normalized public product identifier.
        document_id: Source integer document identity.
        friendly_name: Source document label, never interpreted as a local path.
        post_datetime: Original publication text. A missing offset stays missing.
    """

    emil_id: str
    document_id: int
    friendly_name: str
    post_datetime: str


@dataclass(frozen=True)
class APIArchivePage:
    """A source archive listing page with explicit pagination evidence.

    Attributes:
        documents: Public archive identities in source order.
        total_records: Source-advertised document count, not row count.
        page_size: Source-advertised listing page size.
        total_pages: Source-advertised listing page count.
        current_page: Source-advertised current page number.
        receipt: Exact metadata response identity.
        lifecycle: Root/audit lifecycle evidence, independent of public history access.
    """

    documents: tuple[APIArchive, ...]
    total_records: int
    page_size: int
    total_pages: int
    current_page: int
    receipt: Receipt
    lifecycle: Literal["active", "retired-or-inactive", "unknown"] = "unknown"


@dataclass(frozen=True)
class APIBundle(APIArchive):
    """A separately listed historical bundle with a source signed document ID.

    Attributes:
        emil_id: Normalized public product identifier.
        document_id: Source signed bundle identity; observed IDs are negative.
        friendly_name: Original historical-bundle label.
        post_datetime: Original publication text, without inferred timezone.
    """


@dataclass(frozen=True)
class APIBundlePage(APIArchivePage):
    """A historical bundle page with the archive-page pagination attributes.

    Attributes:
        documents: Source-order bundle identities requiring download_bundle().
    """

    documents: tuple[APIBundle, ...]


@dataclass(frozen=True)
class APIArchiveFile:
    """One bounded ZIP with no asserted typed file-row coverage.

    Attributes:
        document: Explicitly selected source archive identity.
        receipt: Download URL, retrieval time, exact hash and received byte count.
        members: Validated ZIP member names; nothing is extracted to disk.
        body: Complete bounded ZIP bytes, excluded from the object representation.
        row_schema: Always unknown; this adapter does not decode member rows.
    """

    document: APIArchive
    receipt: Receipt
    members: tuple[str, ...]
    body: bytes = field(repr=False)
    row_schema: Literal["unknown"] = "unknown"


class APIArchiveClient(MetadataClient):
    """A public archive client gated by this instance's fetched product metadata.

    Call products() before archives(). Each metadata refresh invalidates previous
    download selections. Public historical files remain selectable for inactive
    or retired products when the current listing verifies their availability.
    """

    def products(self) -> tuple[tuple[Product, ...], Receipt]:
        """Fetch root metadata and reset this instance's public archive gate.

        Returns:
            Source product metadata and its public response receipt. Restricted
            and unknown entries remain visible but cannot authorize downloads.

        Raises:
            PublicDataError: Root retrieval or metadata validation fails.
        """
        self._archive_products: dict[str, Product] = {}
        self._archive_documents: dict[tuple[str, int], APIArchive] = {}
        self._bundle_documents: dict[tuple[str, int], APIArchive] = {}
        products, receipt = super().products()
        self._archive_products = {
            product.emil_id.lower(): product for product in products
        }
        return products, receipt

    def archives(self, emil_id: str) -> APIArchivePage:
        """Fetch one archive metadata page for an explicitly public root product.

        Args:
            emil_id: Product present in this instance's prior products() result.

        Returns:
            Typed document metadata with the source's pagination counters.
            Further pages are not followed.

        Raises:
            ValueError: The identifier is malformed or absent from fetched metadata.
            PublicDataError: Access, transport, or source shape fails.
        """
        return cast(APIArchivePage, self._history(emil_id, "archive"))

    def bundles(self, emil_id: str) -> APIBundlePage:
        """Fetch one historical bundle page for a verified public product.

        Args:
            emil_id: Product present in this instance's prior products() result.

        Returns:
            Typed bundle identities and source pagination counters. Bundle IDs
            are distinct from archive IDs and may be negative.

        Raises:
            ValueError: The identifier is malformed or absent from fetched metadata.
            PublicDataError: Access, transport, or source shape fails.
        """
        return cast(APIBundlePage, self._history(emil_id, "bundle"))

    def _history(
        self, emil_id: str, kind: Literal["archive", "bundle"]
    ) -> APIArchivePage | APIBundlePage:
        """Validate one explicitly selected listing route and its document IDs.

        Args:
            emil_id: Caller-selected public product identifier.
            kind: Exact listing route; never inferred from a failed request.

        Returns:
            A typed page matching the selected source route.

        Raises:
            ValueError: The public product identifier is unsupported.
            PublicDataError: Access, transport, or listing validation fails.
        """
        product_id = emil_id.lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", product_id):
            raise ValueError("Malformed public product identifier")
        products = getattr(self, "_archive_products", {})
        if product_id not in products:
            raise ValueError("Call products() and select an observed public product")
        product = products[product_id]
        if product.access is not Access.PUBLIC:
            raise AccessDeniedError("Archive product is not explicitly Public")
        lifecycle: Literal["active", "retired-or-inactive", "unknown"] = "unknown"
        if product_id in _RETIRED or product.status.casefold() in {
            "inactive",
            "retired",
        }:
            lifecycle = "retired-or-inactive"
        elif product.status.casefold() == "active":
            lifecycle = "active"
        cache = self._archive_documents if kind == "archive" else self._bundle_documents
        retained = {key: value for key, value in cache.items() if key[0] != product_id}
        cache.clear()
        cache.update(retained)
        payload = self._authenticated_payload(f"/{kind}/" + product_id, {})
        try:
            body = payload.json()
            if body["product"]["emilId"].lower() != product_id:
                raise ValueError
            if type(body["product"]["reportTypeId"]) is not int:
                raise ValueError
            meta = body["_meta"]
            counters = tuple(
                meta[name]
                for name in ("totalRecords", "pageSize", "totalPages", "currentPage")
            )
            if any(type(value) is not int or value < 0 for value in counters):
                raise ValueError
            total, size, pages, current = counters
            raw = body[kind + "s"]
            if (
                not isinstance(raw, list)
                or size < 1
                or current != 1
                or pages != (total + size - 1) // size
                or len(raw) != min(total, size)
                or body["_links"]["self"]["href"] != BASE + f"/{kind}/" + product_id
            ):
                raise ValueError
            documents = {}
            for item in raw:
                identity = item["docId"]
                name = item["friendlyName"]
                posted = item["postDatetime"]
                if (
                    type(identity) is not int
                    or not -(2**63) <= identity < 2**63
                    or identity == 0
                    or (kind == "archive" and identity < 0)
                    or identity in documents
                    or not isinstance(name, str)
                    or not name
                    or not isinstance(posted, str)
                    or not posted
                ):
                    raise ValueError
                datetime.datetime.fromisoformat(posted)
                expected = BASE + f"/{kind}/{product_id}?download={identity}"
                if item["_links"]["endpoint"]["href"] != expected:
                    raise ValueError
                model = APIArchive if kind == "archive" else APIBundle
                documents[identity] = model(product_id, identity, name, posted)
            cache.update({(product_id, key): value for key, value in documents.items()})
            if kind == "bundle":
                return APIBundlePage(
                    cast(tuple[APIBundle, ...], tuple(documents.values())),
                    total,
                    size,
                    pages,
                    current,
                    payload.receipt,
                    lifecycle,
                )
            return APIArchivePage(
                tuple(documents.values()),
                total,
                size,
                pages,
                current,
                payload.receipt,
                lifecycle,
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            pass
        raise SchemaMismatchError(
            "Public archive metadata differs from the observed contract"
        )

    def download(
        self,
        document: APIArchive,
        *,
        max_members: int = 64,
        max_expanded_bytes: int = 32_000_000,
    ) -> APIArchiveFile:
        """Download exactly one unchanged listed document as a validated ZIP.

        Args:
            document: An unchanged public archive from this instance's listing.
            max_members: Maximum ZIP member count, including directories.
            max_expanded_bytes: Maximum combined advertised expanded byte count.

        Returns:
            Raw ZIP bytes, member names, selection identity and a receipt. Member
            row schemas remain unknown and no typed data coverage is asserted.

        Raises:
            ValueError: A ZIP structure budget is invalid.
            PublicDataError: Selection, transport, ZIP, or byte checks fail.
        """
        return self._download(document, "archive", max_members, max_expanded_bytes)

    def download_bundle(
        self,
        document: APIBundle,
        *,
        max_members: int = 512,
        max_expanded_bytes: int = 256_000_000,
    ) -> APIArchiveFile:
        """Download one explicitly selected historical bundle using its own route.

        Args:
            document: Unchanged public bundle from this instance's bundles() call.
            max_members: Maximum ZIP member count, including directories.
            max_expanded_bytes: Maximum combined advertised ZIP expansion.

        Returns:
            Selected bundle bytes, ZIP member metadata, and a bound receipt.
            Member row schemas remain unknown unless a separate decoder verifies them.

        Raises:
            ValueError: A ZIP structure budget is invalid.
            PublicDataError: Selection, transport, ZIP, or byte checks fail.
        """
        return self._download(document, "bundle", max_members, max_expanded_bytes)

    def _download(
        self,
        document: APIArchive,
        kind: Literal["archive", "bundle"],
        max_members: int,
        max_expanded_bytes: int,
    ) -> APIArchiveFile:
        """Transfer one document through its explicitly selected source route.

        Args:
            document: Unchanged document selected from this route's listing.
            kind: Exact download route; no fallback is attempted.
            max_members: Maximum ZIP member count.
            max_expanded_bytes: Maximum advertised expanded bytes.

        Returns:
            Complete bounded ZIP bytes and their selection/receipt identity.

        Raises:
            ValueError: A structure budget is invalid.
            PublicDataError: Selection, transport, or ZIP validation fails.
        """
        if any(
            type(value) is not int or value < 1
            for value in (max_members, max_expanded_bytes)
        ):
            raise ValueError("ZIP structure budgets must be positive")
        key = (document.emil_id, document.document_id)
        cache_name = "_archive_documents" if kind == "archive" else "_bundle_documents"
        if getattr(self, cache_name, {}).get(key) != document:
            raise AccessDeniedError(
                "Download requires this client's public archive listing"
            )
        payload = self._authenticated_payload(
            f"/{kind}/{document.emil_id}/download",
            {},
            method="POST",
            json_body={"docIds": [document.document_id]},
        )
        with checked_zip(
            payload.body, max_members=max_members, max_expanded_bytes=max_expanded_bytes
        ) as archive:
            members = tuple(
                item.filename for item in archive.infolist() if not item.is_dir()
            )
            if not members:
                raise SchemaMismatchError("Public archive ZIP contains no files")
            try:
                if archive.testzip() is not None:
                    raise SchemaMismatchError(
                        "Public archive ZIP member checksum failed"
                    )
            except (zipfile.BadZipFile, zlib.error, NotImplementedError):
                raise SchemaMismatchError(
                    "Public archive ZIP member decoding failed"
                ) from None
        return APIArchiveFile(document, payload.receipt, members, payload.body)
