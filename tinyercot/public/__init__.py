"""Opt-in bounded retrieval of selected public ERCOT data sources.

Use ReportsClient for generated current report contracts, PublicClient for DAM
price samples, and WebClient for annual files and the ESR live feed. Legacy
tinyercot imports and behavior are unchanged.
"""

from ._generated import DamCapacityPrice, DamPrice, RealTimePrice, SystemLoad
from ._http import (
    AccessDeniedError,
    AuthenticationError,
    LimitError,
    Limits,
    PublicDataError,
    RateLimitError,
    Receipt,
    SchemaMismatchError,
    SourceUnavailableError,
    StreamingLimits,
)
from ._schemas import (
    DAM_CAPACITY_PRICES,
    DAM_PRICES,
    RT_PRICES,
    SYSTEM_LOAD,
    DamCapacityPriceFilters,
    DamPriceFilters,
    RealTimePriceFilters,
    SystemLoadFilters,
)
from .api import Credentials, PricePage, PublicClient
from .archives import (
    ArchiveDocument,
    ArchivePrice,
    ArchiveRecord,
    ArchiveSample,
    Download,
    iter_dam_archive,
    sample_dam_archive,
)
from .coverage import Coverage, coverage
from .live import EsrRow, EsrSnapshot
from .reports import DataPage, ReportsClient
from .schema import Endpoint
from .web import WebClient

__all__ = [
    "DAM_CAPACITY_PRICES",
    "DAM_PRICES",
    "RT_PRICES",
    "SYSTEM_LOAD",
    "AccessDeniedError",
    "ArchiveDocument",
    "ArchivePrice",
    "ArchiveRecord",
    "ArchiveSample",
    "AuthenticationError",
    "Coverage",
    "Credentials",
    "DamCapacityPrice",
    "DamCapacityPriceFilters",
    "DamPrice",
    "DamPriceFilters",
    "DataPage",
    "Download",
    "Endpoint",
    "EsrRow",
    "EsrSnapshot",
    "LimitError",
    "Limits",
    "PricePage",
    "PublicClient",
    "PublicDataError",
    "RateLimitError",
    "RealTimePrice",
    "RealTimePriceFilters",
    "Receipt",
    "ReportsClient",
    "SchemaMismatchError",
    "SourceUnavailableError",
    "StreamingLimits",
    "SystemLoad",
    "SystemLoadFilters",
    "WebClient",
    "coverage",
    "iter_dam_archive",
    "sample_dam_archive",
]
