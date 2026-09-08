"""Shared transport and typed metadata for ERCOT's public API."""

from __future__ import annotations

import asyncio
import os
import threading
import time
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, Self, TypeVar

import httpx
from httpx_retries import Retry, RetryTransport
from pydantic import BaseModel, ConfigDict, Field

from ._capacity import CapacityChanges
from ._coincident_peaks import CoincidentPeaks
from ._dashboards import Dashboards
from ._distribution_losses import DistributionLossCoefficients
from ._fuel_mix import FuelMix
from ._idr import IdrComplianceHistory
from ._load import HourlyLoad
from ._load_profiles import LoadProfiles
from ._loss_coefficients import TransmissionLossCoefficients
from ._loss_factors import LossFactors
from ._mora import ResourceOutlook
from ._ordc import IndicativeOrdcHistory
from ._public_tables import CrrHours, LoadShed, PolrHistory
from ._retail import RetailTransactions
from ._weather import HistoricalWeather
from ._zonal_energy import ZonalEnergy
from ._zonal_generation import ZonalGeneration

T = TypeVar("T", bound=BaseModel)
Parameter = str | int | float | bool | Decimal | date | datetime | None
BASE_URL = "https://api.ercot.com/api/public-reports"
TOKEN_URL = "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"


class Link(BaseModel):
    href: str
    rel: str | None = None
    title: str | None = None
    type: str | None = None
    hreflang: str | None = None
    media: str | None = None
    deprecation: str | None = None
    profile: str | None = None
    name: str | None = None


class Artifact(BaseModel):
    reportTypeId: int
    displayName: str
    links: dict[str, Link] = Field(alias="_links")


class Product(BaseModel):
    emilId: str
    name: str
    description: str | None = None
    status: str
    reportTypeId: int
    audience: str | None = None
    generationFrequency: str | None = None
    securityClassification: str | None = None
    lastUpdated: date | None = None
    firstRun: date | None = None
    eceii: str | None = None
    channel: str | None = None
    userGuide: str | None = None
    postingType: str | None = None
    market: str | None = None
    extractSubscriber: str | None = None
    xsdName: str | None = None
    misPostingLocation: str | None = None
    certificateRole: str | None = None
    fileType: str | None = None
    ddlName: str | None = None
    misDisplayDuration: int | None = None
    archiveDuration: int | None = None
    notificationType: str | None = None
    contentType: str | None = None
    downloadLimit: int | None = None
    lastPostDatetime: datetime | None = None
    bundle: int | None = None
    protocolRules: dict[str, str] = Field(default_factory=dict)
    artifacts: list[Artifact] = Field(default_factory=list)
    links: dict[str, Link] = Field(default_factory=dict, alias="_links")


class Query(BaseModel):
    parameterCount: int = 0
    parameters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    sortedBy: str | None = None


class Pagination(BaseModel):
    totalRecords: int = 0
    pageSize: int = 0
    totalPages: int = 0
    currentPage: int = 0
    query: Query | None = None


class Report(BaseModel):
    reportName: str
    reportDisplayName: str
    reportId: str | int
    reportEMIL: str
    downloadLimit: int | None = None


class ResponseField(BaseModel):
    name: str
    label: str | None = None
    cardinality: int | None = None
    dataType: str
    searchable: bool = False
    sortable: bool = False
    hasRange: bool = False


class Row(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)
    meta: Pagination = Field(alias="_meta")
    report: Report
    fields: list[ResponseField]
    data: list[T]
    links: dict[str, Link] | list[Link] = Field(default_factory=dict, alias="_links")


class Document(BaseModel):
    docId: int
    friendlyName: str
    postDatetime: datetime
    links: dict[str, Link] | list[Link] = Field(default_factory=dict, alias="_links")


class ProductSummary(BaseModel):
    emilId: str
    name: str
    reportTypeId: int


class History(BaseModel):
    meta: Pagination = Field(alias="_meta")
    product: ProductSummary
    archives: list[Document] = Field(default_factory=list)
    bundles: list[Document] = Field(default_factory=list)
    links: dict[str, Link] | list[Link] = Field(default_factory=dict, alias="_links")


def _params(values: dict[str, Parameter]) -> dict[str, str]:
    return {
        k: ("true" if v else "false")
        if isinstance(v, bool)
        else v.isoformat()
        if isinstance(v, (date, datetime))
        else str(v)
        for k, v in values.items()
        if v is not None
    }


def _decode(body: dict[str, Any], row: type[T]) -> Page[T]:
    names = getattr(row, "__source_fields__", None) or [
        f["name"] for f in body["fields"]
    ]
    body["data"] = [
        row.model_validate(
            dict(zip(names, values, strict=True))
            if isinstance(values, list)
            else values
        )
        for values in body["data"]
    ]
    return Page[T].model_validate(body)


class VersionInfo(BaseModel):
    title: str
    description: str
    version: str
    build: str


class Version(BaseModel):
    info: VersionInfo
    openapi: str


class Transport:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        subscription_key: str | None = None,
        *,
        timeout: float = 30,
        client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._username = username or os.getenv("ERCOT_USERNAME")
        self._password = password or os.getenv("ERCOT_PASSWORD")
        self._key = subscription_key or os.getenv("ERCOT_SUBSCRIPTION_KEY")
        retry = Retry(
            total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        self._owns_client = client is None
        self._owns_async = async_client is None
        self._http = client or httpx.Client(
            timeout=timeout, transport=RetryTransport(retry=retry)
        )
        self._async_http = async_client or httpx.AsyncClient(
            timeout=timeout, transport=RetryTransport(retry=retry)
        )
        self._token = ""
        self._expires = 0.0
        self._lock = threading.Lock()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    async def aclose(self) -> None:
        self.close()
        if self._owns_async:
            await self._async_http.aclose()

    def _headers(self) -> dict[str, str]:
        with self._lock:
            if not (self._username and self._password and self._key):
                raise ValueError(
                    "ERCOT username, password, and subscription key are required"
                )
            if time.monotonic() >= self._expires:
                response = self._http.post(
                    TOKEN_URL,
                    data={
                        "username": self._username,
                        "password": self._password,
                        "grant_type": "password",
                        "scope": f"openid {CLIENT_ID} offline_access",
                        "client_id": CLIENT_ID,
                        "response_type": "id_token",
                    },
                )
                response.raise_for_status()
                body = response.json()
                self._token = body["id_token"]
                self._expires = time.monotonic() + max(
                    0, int(body.get("expires_in", 3600)) - 60
                )
            return {
                "Authorization": f"Bearer {self._token}",
                "Ocp-Apim-Subscription-Key": self._key,
            }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Parameter] | None = None,
        doc_ids: Sequence[int] | None = None,
    ) -> httpx.Response:
        for attempt in range(2):
            response = self._http.request(
                method,
                BASE_URL + "/" + path.lstrip("/"),
                headers=self._headers(),
                params=_params(params or {}),
                json={"docIds": list(doc_ids)} if doc_ids is not None else None,
            )
            if response.status_code != 401 or attempt:
                response.raise_for_status()
                return response
            self._expires = 0
        raise AssertionError("unreachable")

    def _page(self, path: str, row: type[T], params: dict[str, Parameter]) -> Page[T]:
        return _decode(
            self._request("GET", path, params=params).json(parse_float=Decimal), row
        )

    def _iter(
        self, path: str, row: type[T], params: dict[str, Parameter]
    ) -> Iterator[T]:
        page = 1
        while True:
            result = self._page(path, row, {**params, "page": page})
            yield from result.data
            if page >= result.meta.totalPages:
                return
            page += 1

    async def _apage(
        self, path: str, row: type[T], params: dict[str, Parameter]
    ) -> Page[T]:
        for attempt in range(2):
            headers = await asyncio.to_thread(self._headers)
            response = await self._async_http.get(
                BASE_URL + "/" + path.lstrip("/"),
                headers=headers,
                params=_params(params),
            )
            if response.status_code != 401 or attempt:
                response.raise_for_status()
                return _decode(response.json(parse_float=Decimal), row)
            self._expires = 0
        raise AssertionError("unreachable")

    async def _aiter(
        self, path: str, row: type[T], params: dict[str, Parameter]
    ) -> AsyncIterator[T]:
        page = 1
        while True:
            result = await self._apage(path, row, {**params, "page": page})
            for item in result.data:
                yield item
            if page >= result.meta.totalPages:
                return
            page += 1

    @property
    def zonal_generation(self) -> ZonalGeneration:
        return ZonalGeneration(self._http)

    @property
    def fuel_mix(self) -> FuelMix:
        return FuelMix(self._http)

    @property
    def coincident_peaks(self) -> CoincidentPeaks:
        return CoincidentPeaks(self._http)

    @property
    def load_profiles(self) -> LoadProfiles:
        return LoadProfiles(self._http)

    @property
    def historical_weather(self) -> HistoricalWeather:
        return HistoricalWeather(self._http)

    @property
    def idr_compliance(self) -> IdrComplianceHistory:
        return IdrComplianceHistory(self._http)

    @property
    def loss_factors(self) -> LossFactors:
        return LossFactors(self._http)

    @property
    def zonal_energy(self) -> ZonalEnergy:
        return ZonalEnergy(self._http)

    @property
    def transmission_loss_coefficients(self) -> TransmissionLossCoefficients:
        return TransmissionLossCoefficients(self._http)

    @property
    def distribution_loss_coefficients(self) -> DistributionLossCoefficients:
        return DistributionLossCoefficients(self._http)

    @property
    def load_shed(self) -> LoadShed:
        return LoadShed(self._http)

    @property
    def crr_hours(self) -> CrrHours:
        return CrrHours(self._http)

    @property
    def polr(self) -> PolrHistory:
        return PolrHistory(self._http)

    @property
    def retail_transactions(self) -> RetailTransactions:
        return RetailTransactions(self._http)

    @property
    def indicative_ordc(self) -> IndicativeOrdcHistory:
        return IndicativeOrdcHistory(self._http)

    @property
    def resource_outlook(self) -> ResourceOutlook:
        return ResourceOutlook(self._http)

    @property
    def capacity_changes(self) -> CapacityChanges:
        return CapacityChanges(self._http)

    @property
    def hourly_load(self) -> HourlyLoad:
        return HourlyLoad(self._http)

    @property
    def dashboards(self) -> Dashboards:
        return Dashboards(self._http)

    def version(self) -> Version:
        return Version.model_validate(self._request("GET", "version").json())

    def products(self) -> list[Product]:
        return [
            Product.model_validate(p)
            for p in self._request("GET", "").json()["_embedded"]["products"]
        ]

    def product(self, emil_id: str) -> Product:
        return Product.model_validate(self._request("GET", emil_id.lower()).json())

    def archives(
        self,
        emil_id: str,
        *,
        page: int = 1,
        size: int = 1000,
        posted_from: datetime | None = None,
        posted_to: datetime | None = None,
    ) -> History:
        return History.model_validate(
            self._request(
                "GET",
                f"archive/{emil_id.lower()}",
                params={
                    "page": page,
                    "size": size,
                    "postDatetimeFrom": posted_from,
                    "postDatetimeTo": posted_to,
                },
            ).json()
        )

    def bundles(self, emil_id: str, *, page: int = 1, size: int = 1000) -> History:
        return History.model_validate(
            self._request(
                "GET", f"bundle/{emil_id.lower()}", params={"page": page, "size": size}
            ).json()
        )

    def iter_documents(
        self,
        emil_id: str,
        *,
        kind: Literal["archive", "bundle"] = "archive",
        size: int = 1000,
        posted_from: datetime | None = None,
        posted_to: datetime | None = None,
    ) -> Iterator[Document]:
        """Iterate every page of an archive or bundle listing."""
        page = 1
        while True:
            history = (
                self.archives(
                    emil_id,
                    page=page,
                    size=size,
                    posted_from=posted_from,
                    posted_to=posted_to,
                )
                if kind == "archive"
                else self.bundles(emil_id, page=page, size=size)
            )
            for document in history.archives if kind == "archive" else history.bundles:
                if posted_from is not None and document.postDatetime < posted_from:
                    continue
                if posted_to is not None and document.postDatetime > posted_to:
                    continue
                yield document
            if page >= history.meta.totalPages:
                return
            page += 1

    def download(
        self,
        emil_id: str,
        doc_ids: Sequence[int],
        *,
        kind: Literal["archive", "bundle"] = "archive",
    ) -> bytes:
        """Download selected archive documents or bundles as a ZIP file."""
        try:
            return self._request(
                "POST", f"{kind}/{emil_id.lower()}/download", doc_ids=doc_ids
            ).content
        except httpx.HTTPStatusError as error:
            if (
                kind != "bundle"
                or len(doc_ids) != 1
                or error.response.status_code != 400
            ):
                raise
            # Some listed bundles reject POST but work through their published GET link.
            return self._request(
                "GET", f"bundle/{emil_id.lower()}", params={"download": doc_ids[0]}
            ).content
