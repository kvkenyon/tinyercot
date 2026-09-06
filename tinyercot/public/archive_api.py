"""Public archive and bundle contracts with exact failed-transfer receipts.

Import this module directly. Root metadata controls public file access.
Binary content and retirement do not disable publicly listed file access.
"""

import httpx

from ._http import Limits, Payload
from .api import BASE, Credentials
from .api_archives import APIArchiveClient
from .archive_http import EvidenceHTTP, Exchange


class ArchiveAPIClient(APIArchiveClient):
    """Fetch public metadata and one selected archive or bundle ZIP.

    The inherited products(), archives(), bundles(), download(), and
    download_bundle() methods keep their document and ZIP checks. Listings
    have no documented query parameters. This client does not invent paging.
    Each download sends POST JSON with exactly one source docIds entry.
    All completed public attempts, including failures, have an exchange receipt.
    """

    def __init__(
        self,
        credentials: Credentials,
        *,
        limits: Limits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create a bounded client without a request.

        Args:
            credentials: Explicit authorized public account credentials.
            limits: Request, byte, retry, and pacing budgets.
            transport: Optional offline transport.
        """
        self._credentials = credentials
        self._http = EvidenceHTTP(limits or Limits(), transport)
        self._token = None
        self._expires_at = 0.0

    @property
    def exchanges(self) -> tuple[Exchange, ...]:
        """Return public attempt receipts without authentication payloads."""
        return tuple(self._http.exchanges)

    def _authenticated_payload(
        self,
        path: str,
        params: dict,
        *,
        method: str = "GET",
        json_body: dict | None = None,
    ) -> Payload:
        """Fetch a checked public route without replay after a denial.

        Args:
            path: Route already checked by the public metadata adapter.
            params: Validated public query parameters.
            method: Documented GET or POST verb.
            json_body: Selected public document IDs.

        Returns:
            Bounded public bytes and their receipt.

        Raises:
            PublicDataError: Authentication, transfer, or limits fail.
        """
        with self._http.lock:
            if self._token is None or self._http.clock() >= self._expires_at:
                self.refresh_token()
            return self._http.request(
                method,
                BASE + path,
                params=params,
                json_body=json_body,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Ocp-Apim-Subscription-Key": self._credentials.subscription_key,
                },
            )
