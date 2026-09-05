"""Opt-in bounded retrieval of selected public ERCOT data sources.

Use PublicClient for current DAM API prices and WebClient for public annual
files and the ESR live feed. Legacy tinyercot imports and behavior are unchanged.
"""

from ._generated import DamCapacityPrice, DamPrice
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
)
from .api import Credentials, PricePage, PublicClient
from .archives import (
    ArchiveDocument,
    ArchivePrice,
    ArchiveSample,
    Download,
    sample_dam_archive,
)
from .coverage import Coverage, coverage
from .live import EsrRow, EsrSnapshot
from .web import WebClient

__all__ = [
    "AccessDeniedError",
    "ArchiveDocument",
    "ArchivePrice",
    "ArchiveSample",
    "AuthenticationError",
    "Coverage",
    "Credentials",
    "DamCapacityPrice",
    "DamPrice",
    "Download",
    "EsrRow",
    "EsrSnapshot",
    "LimitError",
    "Limits",
    "PricePage",
    "PublicClient",
    "PublicDataError",
    "RateLimitError",
    "Receipt",
    "SchemaMismatchError",
    "SourceUnavailableError",
    "WebClient",
    "coverage",
    "sample_dam_archive",
]
