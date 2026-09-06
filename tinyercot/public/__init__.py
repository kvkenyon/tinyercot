"""Opt-in retrieval, typed public products, metadata, and source-specific files.

Use ReportsClient with generated endpoint constants or the products namespace.
Anonymous dashboard and annual-file clients are separate from authenticated
Public Reports metadata and selected archive downloads. Legacy imports remain
unchanged. Unknown file schemas and source lifecycle are explicit.
"""

from . import products
from ._generated import (
    DamCapacityPrice,
    DamPrice,
    RealTimePrice,
    SystemLoad,
)
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
from .additional_dashboards import (
    AdditionalDashboardClient,
    DashboardPrices,
    DayAheadDashboardPrice,
    RealTimeDashboardPrice,
    SupplyActualRow,
    SupplyDemandSnapshot,
    SupplyForecastRow,
    SupplyObservation,
    SupplyOutlookRow,
    SystemPricesSnapshot,
)
from .aggregate_dashboards import (
    AggregateDashboardClient,
    DcTieRow,
    DcTieSnapshot,
    GenerationOutageRow,
    GenerationOutagesSnapshot,
    OutageAmounts,
    OutageDays,
    OutageObservation,
)
from .api import (
    Credentials,
    PricePage,
    PublicClient,
)
from .api_archives import (
    APIArchive,
    APIArchiveClient,
    APIArchiveFile,
    APIArchivePage,
    APIBundle,
    APIBundlePage,
)
from .archive_reports import (
    RTArchiveClient,
    RTArchivePrice,
    RTArchiveRecord,
    iter_rt_archive,
)
from .archives import (
    ArchiveDocument,
    ArchivePrice,
    ArchiveRecord,
    ArchiveSample,
    Download,
    iter_dam_archive,
    sample_dam_archive,
)
from .coverage import (
    Coverage,
    coverage,
)
from .dashboards import (
    DashboardClient,
    DashboardSnapshot,
    FuelMixRow,
    FuelMixSnapshot,
    FuelMixValues,
    GridCondition,
    GridConditionsSnapshot,
    PrcRow,
)
from .live import (
    EsrRow,
    EsrSnapshot,
)
from .metadata import (
    Artifact,
    MetadataClient,
    Product,
)
from .reports import (
    DataPage,
    ReportsClient,
)
from .resource_dme import (
    ResourceDmeRecord,
    ResourceDmeRow,
    iter_resource_dme,
)
from .schema import (
    Endpoint,
)
from .web import (
    WebClient,
)

__all__ = [
    "DAM_CAPACITY_PRICES",
    "DAM_PRICES",
    "RT_PRICES",
    "SYSTEM_LOAD",
    "APIArchive",
    "APIArchiveClient",
    "APIArchiveFile",
    "APIArchivePage",
    "APIBundle",
    "APIBundlePage",
    "AccessDeniedError",
    "AdditionalDashboardClient",
    "AggregateDashboardClient",
    "ArchiveDocument",
    "ArchivePrice",
    "ArchiveRecord",
    "ArchiveSample",
    "Artifact",
    "AuthenticationError",
    "Coverage",
    "Credentials",
    "DamCapacityPrice",
    "DamCapacityPriceFilters",
    "DamPrice",
    "DamPriceFilters",
    "DashboardClient",
    "DashboardPrices",
    "DashboardSnapshot",
    "DataPage",
    "DayAheadDashboardPrice",
    "DcTieRow",
    "DcTieSnapshot",
    "Download",
    "Endpoint",
    "EsrRow",
    "EsrSnapshot",
    "FuelMixRow",
    "FuelMixSnapshot",
    "FuelMixValues",
    "GenerationOutageRow",
    "GenerationOutagesSnapshot",
    "GridCondition",
    "GridConditionsSnapshot",
    "LimitError",
    "Limits",
    "MetadataClient",
    "OutageAmounts",
    "OutageDays",
    "OutageObservation",
    "PrcRow",
    "PricePage",
    "Product",
    "PublicClient",
    "PublicDataError",
    "RTArchiveClient",
    "RTArchivePrice",
    "RTArchiveRecord",
    "RateLimitError",
    "RealTimeDashboardPrice",
    "RealTimePrice",
    "RealTimePriceFilters",
    "Receipt",
    "ReportsClient",
    "ResourceDmeRecord",
    "ResourceDmeRow",
    "SchemaMismatchError",
    "SourceUnavailableError",
    "StreamingLimits",
    "SupplyActualRow",
    "SupplyDemandSnapshot",
    "SupplyForecastRow",
    "SupplyObservation",
    "SupplyOutlookRow",
    "SystemLoad",
    "SystemLoadFilters",
    "SystemPricesSnapshot",
    "WebClient",
    "coverage",
    "iter_dam_archive",
    "iter_resource_dme",
    "iter_rt_archive",
    "products",
    "sample_dam_archive",
]
