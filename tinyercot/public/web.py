"""Public-only MIS annual file and rolling ESR feed adapters."""

import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Self

import httpx

from ._http import _HTTP, AccessDeniedError, Limits, Receipt, SchemaMismatchError
from .archives import ArchiveDocument, Download, checked_zip
from .live import EsrSnapshot, decode_esr

LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
ESR_URL = (
    "https://www.ercot.com/api/1/services/read/dashboards/energy-storage-resources.json"
)


class WebClient:
    """An anonymous client for two verified public website source routes.

    No ERCOT credential headers are used. Only public DAM annual archives and
    the aggregate ESR feed are implemented. Downloads require a receipt cache.
    """

    def __init__(
        self,
        *,
        limits: Limits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create the web adapter without any network request.

        Args:
            limits: Per-instance request, response, and retry ceilings.
            transport: Optional HTTPX transport for offline tests.
        """
        self._http = _HTTP(limits or Limits(), transport)
        self._listed: dict[str, ArchiveDocument] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release this instance's HTTP connections."""
        self._http.close()

    def esr(self) -> EsrSnapshot:
        """Fetch one rolling ESR aggregate snapshot without polling.

        Returns:
            Typed source observations, freshness evidence, and raw receipt.

        Raises:
            PublicDataError: Transport, byte limits, or source shape checks fail.
        """
        return decode_esr(self._http.request("GET", ESR_URL))

    def dam_archives(self) -> tuple[tuple[ArchiveDocument, ...], Receipt]:
        """List only public report-13060 annual files.

        Returns:
            Source-order documents and the listing receipt. Nonpublic records
            fail closed. Listing a year does not prove complete annual data.

        Raises:
            PublicDataError: Access, transport, or listing shape checks fail.
        """
        payload = self._http.request("GET", LIST_URL, params={"reportTypeId": 13060})
        body = payload.json()
        self._listed = {}
        try:
            entries = body["ListDocsByRptTypeRes"]["DocumentList"]
            if not isinstance(entries, list) or len(entries) > 100:
                raise ValueError
            documents = []
            for entry in entries:
                item = entry["Document"]
                if item["SecurityStatus"] != "P":
                    raise AccessDeniedError("MIS listing contains a nonpublic document")
                if (
                    item["Extension"].lower() != "zip"
                    or int(item["ReportTypeID"]) != 13060
                ):
                    raise ValueError
                identity = item["DocID"]
                if (
                    not isinstance(identity, str)
                    or not identity.isdecimal()
                    or len(identity) > 24
                ):
                    raise ValueError
                name = item["FriendlyName"]
                if (
                    not isinstance(name, str)
                    or not name.startswith("DAMLZHBSPP_")
                    or not name.removeprefix("DAMLZHBSPP_").isdecimal()
                ):
                    raise ValueError
                stamp = datetime.datetime.fromisoformat(item["PublishDate"])
                size = int(item["ContentSize"])
                if stamp.tzinfo is None or size <= 0 or identity in self._listed:
                    raise ValueError
                document = ArchiveDocument(identity, 13060, name, stamp, size, "P")
                self._listed[identity] = document
                documents.append(document)
            return tuple(documents), payload.receipt
        except (KeyError, TypeError, ValueError):
            self._listed = {}
        raise SchemaMismatchError(
            "MIS listing differs from the observed public annual contract"
        )

    def download_dam_archive(
        self, document: ArchiveDocument, *, cache: Path
    ) -> Download:
        """Download one listed public file or reuse its verified local receipt.

        The source page uses mirDownload for files. ViewReport can return an
        HTTP-200 HTML 'No Document' page and is deliberately not used here.
        Files and receipts use document identity; revised documents do not
        overwrite a previous version. No automatic year traversal occurs.

        Args:
            document: An unchanged public entry listed by this client instance.
            cache: Local directory for complete files and credential-free receipts.

        Returns:
            A hash-verified complete ZIP and its original publication metadata.

        Raises:
            PublicDataError: Access, transfer, archive, cache, or limit checks fail.
            OSError: Local cache storage cannot be created or written.
        """
        if (
            document.security != "P"
            or document.report_type_id != 13060
            or self._listed.get(document.document_id) != document
        ):
            raise AccessDeniedError(
                "Download requires this client's public listing evidence"
            )
        if document.byte_count > min(self._http.limits.max_bytes, 4_000_000):
            from ._http import LimitError

            raise LimitError("Advertised archive exceeds the download ceiling")
        cache = Path(cache)
        if cache.is_symlink():
            raise SchemaMismatchError("Receipt cache cannot be a symlink")
        cache.mkdir(parents=True, exist_ok=True)
        path = cache / f"13060-{document.document_id}.zip"
        receipt_path = cache / f"13060-{document.document_id}.json"
        if path.is_symlink() or receipt_path.is_symlink():
            raise SchemaMismatchError("Cached archive or receipt is a symlink")
        temporary = cache / f".{document.document_id}.part"
        if temporary.exists() or temporary.is_symlink():
            raise SchemaMismatchError("Incomplete download needs explicit cache repair")
        if path.exists() or receipt_path.exists():
            try:
                if path.stat().st_size > min(self._http.limits.max_bytes, 4_000_000):
                    raise ValueError
                raw = path.read_bytes()
                if receipt_path.stat().st_size > 16_000:
                    raise ValueError
                saved = json.loads(receipt_path.read_text())
                expected_url = str(
                    httpx.URL(
                        DOWNLOAD_URL,
                        params={
                            "doclookupId": document.document_id,
                            "reportTypeId": 13060,
                        },
                    )
                )
                if (
                    saved["source_url"] != expected_url
                    or saved["document_id"] != document.document_id
                    or saved["source_published_at"] != document.published_at.isoformat()
                    or saved["sha256"] != hashlib.sha256(raw).hexdigest()
                    or saved["byte_count"] != len(raw)
                ):
                    raise ValueError
                receipt = Receipt(
                    saved["source_url"],
                    datetime.datetime.fromisoformat(saved["retrieved_at"]),
                    saved["sha256"],
                    saved["byte_count"],
                )
                if (
                    receipt.retrieved_at.tzinfo is None
                    or len(raw) != document.byte_count
                ):
                    raise ValueError
                return Download(document, path, receipt, True)
            except (OSError, KeyError, TypeError, ValueError):
                pass
            raise SchemaMismatchError(
                "Incomplete or changed cache; explicit repair is required"
            )
        payload = self._http.request(
            "GET",
            DOWNLOAD_URL,
            params={"doclookupId": document.document_id, "reportTypeId": 13060},
        )
        if payload.receipt.byte_count != document.byte_count:
            raise SchemaMismatchError("Downloaded size differs from the public listing")
        with checked_zip(
            payload.body, max_members=24, max_expanded_bytes=32_000_000
        ) as archive:
            files = [item for item in archive.infolist() if not item.is_dir()]
            if len(files) != 1 or not files[0].filename.lower().endswith(".xlsx"):
                raise SchemaMismatchError("Expected one XLSX member in the annual ZIP")
        receipt = payload.receipt
        record = {
            "source_url": receipt.source_url,
            "retrieved_at": receipt.retrieved_at.isoformat(),
            "sha256": receipt.sha256,
            "byte_count": receipt.byte_count,
            "document_id": document.document_id,
            "source_published_at": document.published_at.isoformat(),
            "friendly_name": document.friendly_name,
        }
        # Keep failed writes separate. A partial cache never triggers a redownload.
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload.body)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        descriptor = os.open(
            receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "w") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
        return Download(document, path, receipt)
