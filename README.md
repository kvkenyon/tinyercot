# tinyercot

A small, fully typed client for ERCOT public data.

**Development status:** all 242 Public Reports endpoints have typed methods and captured-response tests. The separate ESR API is awaiting an enabled subscription key. MIS is not included.

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    prices = ercot.np4_190_cd.dam_stlmnt_pnt_prices_iter(
        deliveryDateFrom=date(2026, 1, 1),
        deliveryDateTo=date(2026, 1, 2),
        settlementPoint="HB_HOUSTON",
    )
    for price in prices:
        print(price.deliveryDate, price.settlementPointPrice)
```

Pass `username`, `password`, and `subscription_key` to `Client`, or set
`ERCOT_USERNAME`, `ERCOT_PASSWORD`, and `ERCOT_SUBSCRIPTION_KEY`.
Authentication is lazy; the client refreshes tokens and retries transient failures.

Each product exposes generated methods with named, typed filters and Pydantic row
models. A method returns one `Page[Row]`; its `_iter` variant streams all pages.
`_async` and `_iter_async` provide asynchronous access. Date and decimal values
retain their Python types. Nullable source cells are represented by `None`.

```python
from pathlib import Path
from tinyercot import Client

with Client() as ercot:
    products = ercot.products()
    history = ercot.archives("np4-190-cd")
    document = history.archives[0]
    Path("prices.zip").write_bytes(ercot.download("np4-190-cd", [document.docId]))

    bundles = ercot.bundles("np4-190-cd")
    Path("monthly.zip").write_bytes(
        ercot.download("np4-190-cd", [bundles.bundles[0].docId], kind="bundle")
    )
```

Archive and bundle listings expose typed metadata. Downloads return the original
ZIP bytes. Typed historical readers currently cover: DAM
settlement prices, real-time settlement prices, DAM ancillary-service clearing
prices, DAM bus LMPs and shadow prices, actual load by weather zone, forecast zone,
and study area, and all 17 tables in the 60-day DAM disclosure ZIP. The eight
single-table reports have oldest-listed and recent samples; 13 disclosure tables
have 2014 and recent samples, and four newer tables have recent samples only. Their
files have been downloaded and decoded; other archive schemas are still being
mapped.

```python
from datetime import datetime

with Client() as ercot:
    history = ercot.np4_190_cd.dam_stlmnt_pnt_prices_history
    for price in history.rows(
        posted_from=datetime(2014, 5, 1),
        posted_to=datetime(2014, 5, 1, 23, 59, 59),
        where=lambda price: price.settlementPoint == "HB_HOUSTON",
    ):
        print(price.deliveryDate, price.settlementPointPrice)
```

Publication timestamps are ERCOT local timestamps, and both bounds are inclusive.
They select files by **publication date**, which can differ from the dates inside
them. The predicate filters typed rows after download. With no publication bounds,
`rows()` reads all listed archive documents. Publication bounds are sent to ERCOT to limit listing pages at the source.
Matching documents are downloaded individually by default. Pass `batch_size=25`
to `rows()` or `download()` to group requests. Batches are capped by the product
metadata and the API ceiling of 1,000 files; larger batches use more memory.
Monthly bundles are still retrieved individually. Large backfills can take considerable time.
Corrections are preserved as published; rows are not deduplicated.

`history.read(zip_bytes)` reads an existing download, including nested ZIPs.
`history.download([doc_id])` downloads and decodes selected documents; pass
`kind="bundle"` for monthly bundle IDs. Bundle errors propagate; automatic bundle
fallback is not implemented yet. Unsupported CSV layouts raise with the member
name instead of silently dropping data. These readers add no runtime dependencies.

Listing metadata includes the server's total and page counts; `iter_documents()` streams all listing pages.

## Development

Runtime dependencies are `httpx`, `httpx-retries`, and `pydantic`. The handwritten
core handles authentication, transport, pagination, and metadata. Product methods
and row models are generated from saved ERCOT operation and field definitions.

```sh
uv sync --group dev
uv run python tools/generate_client.py
uv run mypy tinyercot tests/typing_client.py --strict --follow-untyped-imports
uv run pytest
uv build
```

Generation fails if an endpoint has no field schema. During discovery only,
`--allow-incomplete` emits available endpoints and reports the missing count.
Public dashboards are available through `ercot.dashboards`: fuel mix, grid
conditions, energy storage, generation outages, DC-tie flows, system prices,
supply/demand, combined wind/solar, system demand, ancillary services, weather,
and the current locational price map.

Source-specific corrections live in `tools/inputs/type-overrides.json`,
`row-fields.json`, and `query-defaults.json`. ERCOT declares hour-ending labels
and offer identifiers as numeric on two reports. The ESR-west report includes
two metadata-only columns absent from its rows and has an invalid default sort;
its generated method uses `SCEDTimestamp` by default. Captured responses support
these small corrections. Large forecasts may need a date filter or a longer
client timeout. Specify `sort` when supplying `dir`. Tests use saved public responses and mocked
HTTP; credentials are not part of the test suite.

Disclosure readers select their own CSV member from the shared ZIP. For example,
`ercot.np3_966_er._60_dam_load_res_data_history` returns generated historical rows
that preserve the old `RRSAwarded` field separately from newer `RRSPFRAwarded`,
`RRSFFRAwarded`, and `RRSUFRAwarded` fields. Fields absent in a captured schema
are `None`. The current API row contracts remain unchanged. Reading a ZIP that
predates a table raises a missing-member error; full-range queries across table
introduction dates still need handling.

Archive-only CSV products also have generated namespaces: resource ownership
(`ercot.np3_988_er.resources_history`), public load estimation counts
(`ercot.copg_316.load_estimation_counts_history`), and confidentiality-expired
adjusted meter load (`ercot.np1_300.adjusted_meter_load_history`). These expose the same typed
`read`, `download`, and `rows` methods without inventing row-query API endpoints.
DUNS identifiers remain strings, counts are integers, and percentages are decimals.

`ercot.eia_930_er.daily_operations_history` reads both captured EIA daily layouts.
Its `HR1` through `HR25` cells are `Decimal | datetime | None`: demand, generation,
and flow values stay numeric, while UTC rows carry timezone-aware timestamps.
A published `24:00:00Z` becomes midnight on the following date. The older
`postedDate` and `interconnectedBalancingAuthorityCode` fields are preserved
separately from the newer `dataDate` and `dataCode` fields. This reader preserves
wide source rows; it does not join timing rows to measurement rows.

Additional historical readers cover DAM energy bought/sold, PTP obligation
results, system lambda, real-time bus and settlement-point LMPs, ancillary-service
plans, and wind actuals/forecasts. Legacy bus `LMP` is separate from newer capped
and uncapped prices. The wind history model preserves the old combined west/north
region and full `hourEndingTimestamp` separately from newer region fields and
integer `hourEnding`. API posting timestamps absent from a CSV remain `None`.

Known optional columns can appear in intermediate combinations. Required model
fields still apply, and unknown columns, duplicate aliases, or ambiguous reused
headers raise an error. This supports compatible schema evolution without
silently discarding source columns or assuming changed fields mean the same thing.

Install `tinyercot[files]` for typed XLSX archives. This adds workbook support
without changing the dependencies needed for API and CSV access:

```python
with Client() as ercot:
    for row in ercot.np1_346_er.outages_history.rows(
        posted_from=datetime(2026, 8, 1),
        posted_to=datetime(2026, 8, 2),
    ):
        print(row.resourceName, row.actualOutageStart, row.plannedEndDate)
```

Workbook readers also cover monthly load-resource demand response
(`ercot.np3_108.demand_response_history`) and ancillary-service deployment factors
(`ercot.np5_520_er.deployment_factors_history`). `sourceSheet` preserves the source
worksheet, including separate CLR and NCLR demand response tables; older reports
have a single `Report Data` sheet. Month fields are dates on the first of the month.
Older outage reports expose `returnToServiceDate`; newer reports expose separate
`plannedEndDate` and `actualEndDate` fields. Missing fields remain `None`.
These readers have been checked against the oldest available and recent sampled
workbooks, not every intervening publication.


Historical readers also cover five-minute wind and solar generation, hourly solar
forecasts, geographical wind/solar generation and forecasts, and system-wide
demand. Use the API method name with `_history`, for example
`ercot.np4_742_cd.wpp_hrly_actual_fcast_geo_history.rows(...)`.
The older five-minute wind layout preserves its combined region as `LZWestNorth`;
individual west/north values remain `None`. Older solar forecasts preserve a full
`hourEndingTimestamp` instead of inventing a delivery date and integer hour.
Archived five-minute timestamps retain their seconds where supplied.

In the September 2026 archive probes, oldest downloadable samples reached April
2014 for five-minute wind and February 2016 for solar. Regional reports started
later, and the system-wide demand listing reached only March 2026. These are
observed archive bounds, not guarantees of complete intervening data or permanent
retention; inspect each product's listings when selecting a backfill.

System-lambda and price-adder history preserves the older ORDC fields separately
from current reliability-deployment adders. For example,
`ercot.np6_323_cd.rt_price_adder_sced_history` exposes legacy `RTORPA` and `RTOFFPA`
alongside `RTRDPA`; absent source columns are `None`. The older SCED lambda report
has `systemLambda`, while newer files have `cappedSystemLambda` and
`uncappedSystemLambda`. Reading an older file does not invent capped values.
The same `_history` workflow covers RTD indicative adders, state-estimator total
generation and DC-tie flows, HDL/LDL summaries, and SCED shadow prices. Publication
bounds select archive files; typed predicates can select timestamps, ties, or
constraints inside them. In the sampled listings, price-adders reached 2014,
state-estimator reports reached 2019, and HDL/LDL summaries reached April 2026.


Load-forecast history includes forecast/actual comparisons, seven-day forecasts
by forecast and weather zone, intra-hour weather-zone forecasts, and forecasts by
model/weather zone or study area. Use each generated method's `_history` property.
Hour-ending labels such as `24:00` remain strings where the report uses them;
model identifiers and in-use flags remain available for filtering.

To retain which publication each forecast came from, keep the listing metadata
alongside the rows:

```python
with Client() as ercot:
    history = ercot.np3_561_cd._7d_load_fcast_by_wzn_history
    for document in ercot.iter_documents(
        "np3-561-cd",
        posted_from=datetime(2026, 8, 1),
        posted_to=datetime(2026, 8, 2),
    ):
        for forecast in history.download([document.docId]):
            print(document.postDatetime, forecast.deliveryDate, forecast.coast)
```

`document.postDatetime` is ERCOT's publication time, not a guarantee of an earlier
model issue time. These CSVs omit `postedDatetime`, so that row field remains
`None` when reading the file; a delivery date must not substitute for publication
or issue time. Distinct publications can contain forecasts for the same delivery
hour, and are retained without deduplication.

Outage and adequacy history includes seven-day and longer planned-outage margins,
hourly resource outage capacity, short-term system adequacy, hourly RUC status,
and approved DC-tie schedules. For example,
`ercot.np3_233_cd.hourly_res_outage_cap_history.rows(...)` reads old system totals
as `totalResourceMW` and `totalIRRMW`; regional fields absent from those files
remain `None`. Old RUC reports similarly preserve `sumSCEDTotal` separately from
newer regional values. RUC and SCED timestamps retain their seconds, and DC-tie
schedules retain both GMT and local interval-ending fields. System-adequacy
hour-ending labels remain strings, including `24:00`.

Ancillary-service offers and sales, peaker net margin, system-wide offer caps,
RMR deployments, and day-ahead point-to-point option prices also expose typed
`_history` readers. Legacy offers retain `RRS` separately from later RRS
categories; legacy offer-cap files retain `SWCAP` separately from `DASWCAP` and
`RTSWCAP`. Missing later columns remain `None`. The latest listed total-offers
archive in the September 2026 probe was from December 2025; an archive listing
must be checked before assuming a product has current historical publications.

Renewable forecast archives include hourly forecasts by model (NP4-442/443) and
intra-hour regional forecasts (NP4-751/752). Each row keeps its `region`, `model`,
and `inUseFlag`; forecasts from alternative models are not merged. To select
ERCOT's in-use forecast for one region:

```python
with Client() as ercot:
    for forecast in ercot.np4_752_cd.ih_solar_fcast_geo_history.rows(
        posted_from=datetime(2026, 8, 1),
        posted_to=datetime(2026, 8, 2),
        where=lambda row: row.region == "CENTEREAST" and row.inUseFlag is True,
    ):
        print(forecast.intervalEnding, forecast.model, forecast.value)
```

`SYSTEM_TOTAL` rows remain separate from regional rows; summing both would count
both the total and its components. As with load forecasts, preserve document
metadata when publication time matters because these CSVs omit `postedDatetime`.

Weekly, daily and hourly RUC ancillary-service deployment factors (NP5-525/527/528)
and projected deployment factors (NP5-526) have generated `_history` readers.
For example, `ercot.np5_527_cd.druc_as_deploy_factors_history.rows(...)` retains the
RUC execution timestamp separately from delivery date/hour, service type, and the
decimal factor. The oldest files listed in the September 2026 probes were from
December 2025; these products do not establish a common start date for other
ancillary-service history.

DAM/SCED and hourly, daily, and weekly RUC ancillary-service demand curves
(NP4-212/213/214/215) expose typed `_history` readers. Each source point retains
its `demandCurvePoint`, `quantity`, `price`, service type, and delivery hour;
RUC curves also retain execution timestamps. For example,
`ercot.np4_214_cd.druc_as_demand_curves_history.rows(...)` returns every point,
including adjacent points with equal prices. Large curve publications are read
one downloaded file at a time by default; increasing batch size increases memory
use. Preserve document metadata when comparing separate publications.

Real-time ancillary-service history includes total available capability
(NP6-328), RTD indicative MCPCs (NP6-329), 15-minute clearing prices (NP6-331), and
SCED clearing prices (NP6-332). Use each product's `_history` reader. Indicative
prices retain the RTD execution time and forecast interval separately, with both
repeated-hour flags. SCED history retains legacy `MCPC` separately from newer
`cappedMCPC` and `uncappedMCPC`; missing source fields remain `None`. The products
remain distinct so indicative prices are not confused with clearing prices.
