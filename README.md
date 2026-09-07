# tinyercot

A small, fully typed client for ERCOT public data.

**Development status:** all 242 Public Reports endpoints have typed methods and captured-response tests. The separate ESR API is awaiting an enabled subscription key. MIS is not included.

The live inventory check matched all 249 published HTTP operations: 242 generated
report queries and seven shared operations. All 5,973 query-parameter definitions
matched the saved inputs, and all four generated query variants expose the
expected named parameters and types. The live catalog lists the same 242 report
paths. See `tools/inputs/live-inventory-evidence.json` for the check date and
scope; endpoint coverage does not establish every historical file layout.

Public website files extend beyond that API inventory. `client.wind_integration`
provides typed daily summaries from ERCOT's directly linked wind ZIPs for
2010–2015 and January 2016, without credentials or MIS access. All 2,000 PDFs in
those seven ZIPs decoded successfully. This reader is separate from the 289
generated API-history readers. Other website archives and unlabelled chart values
remain outside this coverage. See `tools/inputs/public-website-archives-evidence.json`
for source URLs, missing dates, date conflicts and verification scope.

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
ZIP bytes. For decoded data, generated `_history` readers cover 289 tables across
113 catalog products: all 242 report-query tables, 33 additional CSV tables,
nine workbook products and five PDF readers. The same readers support individual
archives and monthly bundles.

The other three captured catalog products returned empty archive and bundle
listings. Historical layouts are still being checked; the examples and source
evidence below describe the formats and periods verified so far.

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
`kind="bundle"` for monthly bundle IDs. `history.rows(kind="bundle")` paginates
and decodes monthly bundles directly, with the same typed `where` predicate.
Its publication bounds filter bundle timestamps locally; they do not restrict
the dates of individual rows inside a bundle. For example:

```python
with Client() as ercot:
    for row in ercot.np6_345_cd.act_sys_load_by_wzn_history.rows(
        kind="bundle",
        posted_from=datetime(2018, 1, 31),
        posted_to=datetime(2018, 1, 31, 23, 59, 59),
    ):
        print(row.operatingDay, row.total)
```

The downloaded January 2018 load bundle contained 31 daily files and 744 hourly
rows, covering operating dates December 31 through January 30. Bundle names and
publication months are not delivery-date bounds. Mixed correction bundles are
filtered by CSV member name; months without the selected correction subtype yield
no rows. Unsupported selected tables still raise.

Archive and bundle retention differ. In the recorded checks, DAM prices and
system-load archives reached May 2014, while bundles began January 2018. RTD
price-adder archives reached June 2014, while bundles began January 2019. The
DAM-price, ESR Integration and event-trigger bundle listings lacked July 2026. The listed January 2018 DAM-price bundle returned HTTP 400 through POST,
but its published GET download link succeeded. The client now tries that link
when a single-bundle POST returns 400; all 473,256 price rows in its 31 files
decoded, covering delivery dates January 2 through February 1, 2018.
The December 2023 ESR Integration bundle decoded 26 daily PDF summaries.
These point-in-time observations are recorded in
`tools/inputs/history/bundle-evidence.json`. Use both listings when assessing maximum
available history; neither listing alone proves continuous coverage. Reading both
sources can repeat publications, which the client preserves. All 62 CSV files in
sampled January 2018 price/load bundles matched their individual archive copies
by filename and content. File-name timestamps are not reliable publication keys:
24 of 31 price files and four of 31 load files had timestamps differing from the
API publication timestamp even at whole-second precision. Automatic source
selection therefore needs stronger evidence than matching counts or timestamps.
If both bundle
download routes fail, the error propagates. Automatic selection between monthly
bundles and individual archives is not implemented yet. Unsupported CSV layouts
raise with the member name instead of silently dropping data.

Listing metadata includes the server's total and page counts; `iter_documents()` streams all listing pages.

### Direct public hourly load archives

Install `tinyercot[files]` for XLS and XLSX support. These files are downloaded
from ERCOT's public website without API credentials.

```python
from datetime import date
from tinyercot import Client

with Client(timeout=120) as ercot:
    for load in ercot.hourly_load.weather_zones(
        date_from=date(2002, 1, 1), date_to=date(2002, 1, 2)
    ):
        print(load.operatingDay, load.hourEnding, load.coast, load.total)

    archives = ercot.hourly_load.archives()
    archive = next(item for item in archives if item.year == 2002)
    data = ercot.hourly_load.download(archive)
    saved_rows = list(ercot.hourly_load.read_weather_zones(data))
```

`archives()` discovers all linked load files, including older control-area and
system-only publications. `weather_zones()` decodes the workbook series beginning
in 2002. It uses inclusive **operating-date** bounds and retains hour ending 24 on
its original operating day. The source's literal `DST` suffix stays in `dstLabel`;
it is not interpreted as a UTC offset or the API's repeat-hour flag. Excel serials
with millisecond rounding noise are read as their displayed whole hour, with the
unrounded converted clock retained in `sourceHourEnding`. Load values use
`Decimal`; missing cells remain `None`.

All 24 workbooks for 2002–2025 decoded: 210,384 hourly rows, with every one of the
1,893,456 load cells compared against its source (including nine absent cells).
The 2016 workbook has an hour with all nine values missing. In the September 2026
check, the linked **2026 ZIP failed its CRC check on two identical downloads**;
that integrity error propagates. Bound queries through 2025 to read the verified
completed years. The index has no 2001 file. See
`tools/inputs/public-hourly-load-evidence.json` for the inventory and source issues.

For the older system, control-area and load-serving-entity records, use the typed
`legacy()` reader. It emits one entity/hour measurement, with the source entity
and control-area relationship retained:

```python
with Client(timeout=120) as ercot:
    for load in ercot.hourly_load.legacy(
        date_from=date(1995, 1, 1), date_to=date(1995, 1, 2)
    ):
        print(load.operatingDay, load.hourEnding, load.entity, load.demand, load.unit)

    archive = next(a for a in ercot.hourly_load.archives() if a.year == 1995)
    data = ercot.hourly_load.download(archive)
    saved_rows = ercot.hourly_load.read_legacy(data, filename="erceei95.txt")
```

All eight linked pre-2002 files decoded: 562,115 entity/hour measurements, each
compared with its source. EEI files retain their MW values; the 1998 workbook
explicitly reports kW. The 1996, 1999 and 2000 text files do not state their units,
so `unit` remains `None` and numeric magnitudes are unchanged. Four published
`#VALUE!` cells retain `sourceError` and have `demand=None`. Repeated hour labels
and overlapping publications remain separate. The 1997 raw text and workbook
versions match for every hour, including the workbook's annual energy and peak.

Legacy date bounds are applied to file contents after considering all older
files: the file labelled 1996 continues into February 1997, and the ZIP labelled
1997 contains 1996 records. System totals, individual control areas and
load-serving entities are not added together or mapped to modern weather zones.
These readers decode hourly measurements; companion forecasts and separate
workbook summary tables remain outside their scope. See
`tools/inputs/public-legacy-hourly-load-evidence.json` for the source checks and
EEI format reference.

### Direct public wind archives

Install `tinyercot[pdf]`. These public website files need no API credentials.

```python
from datetime import date
from tinyercot import Client

with Client(timeout=120) as ercot:
    for wind in ercot.wind_integration.rows(
        date_from=date(2010, 8, 9), date_to=date(2010, 8, 10)
    ):
        print(wind.reportDate, wind.peakLoadMW, wind.maxWindMW)

    archives = ercot.wind_integration.archives()
    data = ercot.wind_integration.download(archives[0])
    saved_rows = list(ercot.wind_integration.read(data))
```

`archives()` discovers actual links on ERCOT's wind integration index. `rows()`
downloads overlapping annual or monthly ZIPs and applies inclusive **report-date**
bounds. `read()` also accepts a saved PDF. It exposes the printed summary tables,
including peak load, wind output and generation/penetration records as `Decimal`,
`date`, `time` and `datetime` values. Older missing fields remain `None`. Original
labels distinguish a previous record from a newly established one and preserve
“Wind Integration %” separately from newer penetration metrics. Source clocks
remain local and timezone-naive; older date-only records do not gain a time.

The inspected files span August 9, 2010 through January 31, 2016, with gaps and
revisions. ERCOT explicitly lists five missing 2014 reports. Two 2011 files have
headings that disagree with their filenames; report-date filters follow those
headings and `sourceMember` retains each filename. One malformed heading prints
`05/14/12013`; its chart and filename identify May 14, 2013, which is used for
`reportDate` while `reportDateText` preserves the typo. Reports are not deduplicated.
No hourly values are estimated from chart positions. This is coverage of these
seven linked ZIPs, not a promise of uninterrupted history or all website data.

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
HTTP; credentials are not part of the test suite. A separate live check used fresh
clients with the default transports to authenticate, query typed prices, read
May 2014 archives, recover a January 2018 bundle through its published GET link,
and make an async query. See `tools/inputs/history/sdk-workflow-evidence.json`
for the bounded queries and public response metadata.

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

Install `tinyercot[files]` for typed XLS/XLSX archives. This adds workbook support
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

Daily and hourly RUC transmission constraints (NP5-754/755) and RTD indicative
LMPs (NP6-970) also expose typed `_history` readers. Constraint rows retain IDs,
station names, decimal voltage values, and execution timestamps. RTD price rows
retain the run timestamp separately from the forecast interval and preserve old
settlement-point type codes. For example,
`ercot.np6_970_cd.rtd_lmp_node_zone_hub_history.rows(...)` reads indicative prices;
it does not replace the SCED LMP or settlement-price products. The oldest sampled
RTD archive in the September 2026 probe was from May 2014.

Mapping-report history covers electrically similar settlement points (NP4-158),
load distribution factors (NP4-159), de-energized settlement points (NP4-200), and
heuristic-pricing electrical bus mappings (NP4-231). Each exposes its generated
`_history` property. Load IDs and MRIDs remain strings, preserving leading zeros,
braces, and case. Older `LoadDistributionFactor` headers map to the same typed
`distributionFactor` field as newer files. Keep document publication metadata
when comparing mapping versions; source row dates describe the report's data.

DAM and RTM price-correction archives expose a history reader for each correction
subtype. These archives mix document types, so generated readers select matching
document names before downloading and the matching CSV member before decoding:

```python
with Client() as ercot:
    for correction in ercot.np4_196_m.dam_price_corrections_eblmp_history.rows(
        posted_from=datetime(2025, 12, 8),
        posted_to=datetime(2025, 12, 10),
    ):
        print(correction.electricalBus, correction.LMPOriginal, correction.LMPCorrected)
```

All eleven DAM/RTM correction subtypes found in the catalog have generated
readers, including SOG, shadow-price, settlement-point and ancillary-service
corrections. Original and corrected values remain separate. Older
LMP fields and legacy SOG `RTORDPA` fields are preserved rather than assigned to
newer fields. Publication, delivery/SCED, and correction timestamps keep their
source meanings; correction records are not automatically applied to other
reports. `ercot.np4_412_cd.epp_cumulative_hours_history` also reads emergency-pricing
cumulative-hour reports.

SOG real-time prices (NP6-326), SOG LMPs with adders (NP6-327), and weather
assumptions (NP4-722) have generated `_history` readers. SOG meter identifiers
remain strings even when entirely numeric, and legacy `RTORPA`/`RTORDPA` columns
remain separate from newer `RTRDPA`. Weather assumptions retain the published
zone values and hour labels; they are a distinct product from actual load and
load forecasts.

`ercot.np4_19_cd.dam_agg_as_offer_curve_history` reads aggregated ancillary-service
offer curves, including the sampled March 2014 layout. Service codes such as
legacy `OFFNS` and newer `ECRSM` remain as published. Prices and quantities retain
decimal precision and source order; sort explicitly if an application requires
ascending prices. Offer curves remain distinct from ancillary-service demand
curves.

Highest-price SCED bids (NP3-257), SCED ancillary-service offers (NP3-914), DAM
ancillary-service offers (NP3-915), and SCED energy offers (NP3-916) expose typed
`_history` readers. For example,
`ercot.np3_915_ex._3d_dam_high_as_offers_history.rows()` includes the sampled
March 2014 DAM layout. Older SCED batch identifiers remain strings; QSE and DME
values absent from historical files remain `None`. Published duplicate rows,
proxy-extension and penalty flags, and full decimal prices are preserved.

SCED ancillary-service offer disclosures (NP3-906) have nine typed history
readers, one for each published service. DAM energy-curve disclosures (NP3-907)
have fifteen: demand, supply and minimum supply, each for the system and four
regions. For example, `ercot.np3_907_ex._2d_agg_edc_north_history` selects the
North demand table from the shared ZIP; `ercot.np3_906_ex._2day_agg_sced_as_offers_regdn_history`
selects SCED regulation-down offers. These preserve every published curve point,
including negative prices and decimal MW quantities. The sampled archive
boundaries for these products are December 2025; this does not establish their
complete historical retention.

Two-day DAM bid/offer disclosures (NP3-909) and real-time generation/load
summaries (NP3-910) have 26 typed history readers, including their regional
tables. Historical PTP bid IDs remain strings. Older non-wind generation fields
remain separate from non-intermittent generation; absent storage or solar
fields remain `None`. DSR load summaries are present in the sampled 2014 archive
but absent from the sampled current ZIP; reading that file with the DSR reader
raises a missing-table error.

SCED energy-curve history (NP3-908) has readers for wind, solar, non-intermittent
and storage supply and controllable-load demand, including four regional tables
for each. Older files also contain DAM demand, supply and minimum-supply curves
under `_2d_agg_dam_*_history`, plus separate `_2d_agg_esc_non_wind*_history`
readers. These older categories are retained explicitly. The sampled March 2014
ZIP contains tables no longer included in the sampled August 2026 ZIP; requesting
a missing table raises an error. Header-only tables yield no rows.

DAM ancillary-service disclosures (NP3-911) have 36 readers matching the API
report tables and seven legacy RRS readers. Aggregate offer curves and the newer
DAM-specific curves keep separate `_2d_agg_as_offers_*_history` and
`_2d_agg_dam_as_offers_*_history` names. Legacy RRS load/generation cleared and
self-arranged quantities, and `RRSNC`, `RRSLD`, `RRSGN` offer curves, remain
separate from newer RRS response categories. The sampled 2014, 2025 and current
archives cover different sets of tables; a missing table raises an error rather
than silently substituting another category.

COP adjustment-period snapshots (NP1-301) and ancillary-service obligations
(NP1-302) have typed history readers. COP history preserves combined legacy
`RRS` separately from newer response categories and keeps `hourEnding` labels
such as `01:00` as strings. Older obligation and responsibility fields remain
separate from advisory/final obligations; absent values remain `None`. Archive
publication dates differ from the delivery dates in these delayed reports.

Seven-day event-trigger reports (NP3-987) have separate LMP, DAM MCPC and
real-time MCPC history readers. These tables are conditional: the latest ZIP
may contain only one of them. Sixty-day SASM disclosures (NP3-990) have four
readers for generation/load offers and awards. SASM IDs parse as timestamps,
including the AM/PM format in award files; legacy combined-RRS offers and
awards stay separate from newer response categories. Header-only files are
valid and yield no rows. A sampled populated SASM archive was published in
January 2026 for November 2025 activity, while the latest listed February file
was empty; latest publication does not imply recent activity.

`ercot.np3_991_ex._60_cop_all_updates_history` reads complete COP update history,
including the sampled 2018 layout. Update and submission timestamps remain
separate; the reader accepts the explicitly mapped minute and second formats.
Cancellation flags and all revisions remain as published. Legacy combined `RRS`
remains separate from newer response categories. Applications must select the
appropriate revision themselves; the reader does not collapse updates.

Sixty-day SCED disclosures (NP3-965) have eleven typed historical readers,
covering generation, load, storage, offer curves, updates, manual overrides,
self-arranged services and legacy demand-side response loads. Readers select
individual tables from the shared archive. Older QSE/DME fields may be absent,
and legacy `RRSGN`, `RRSLD`, `RRSNC` quantities remain separate from newer service
categories. Curve points and reported revisions remain as published.

Historical SCED and 15-minute price-adder workbooks (NP6-792/793) expose
`price_adders_history` readers with `tinyercot[files]`. Monthly sheets retain
`sourceSheet`; older ORDC/reserve fields and newer component adders stay
separate, with absent columns represented by `None`. Delivery dates, SCED
timestamps and published batch IDs remain available. A workbook's year label
does not guarantee a complete year: the sampled early 2018 SCED file contains
only January rows.

The capacity workbooks also have typed readers:
`ercot.np6_794_er.capability_history`,
`ercot.np6_795_er.clearing_prices_history` (SCED), and
`ercot.np6_796_er.clearing_prices_history` (15-minute). Resource capability
combinations retain their reported fields; historical `MCPC` remains separate
from `cappedMCPC` and `uncappedMCPC`. Monthly sheet names, service types and the
SCED timestamp or delivery interval identify each row. These readers use the
existing `tinyercot[files]` extra.

Exceptional fuel-cost submissions (NP4-494) expose
`fuel_cost_submissions_history` through the optional workbook reader. Delivery
hours remain as reported, including the documented repeated-hour value 25.
Monthly path-specific adders (NP7-535) expose `path_adders_history`, reading the
CSV in each archive. Target date and start date remain separate, with source,
sink, time-of-use and signed decimal coefficients preserved. In both sampled
archives, every CSV row matched its XML counterpart.

`ercot.eia_930_cd.hourly_operations_history` reads EIA same-day hourly reports.
Hour fields contain either UTC timestamps or demand values, according to the
row's `dataType`, and unreported hours remain `None`. Julian data dates are
parsed as dates. Date-bounded archive queries work for this product; older
unfiltered attempts timed out, while the latest check succeeded. The oldest
file in that listing was posted April 30, 2026, despite the product's earlier
catalog start date. This is observed availability, not a retention guarantee.

Annual SCED and wind samples from 2015–2025 were checked against the generated
readers (CSV headers and up to three rows, not every retained file). The 2016
wind layout preserves `HOUR_BEGINNING` as `hourBeginningTimestamp`; the 2017
layout retains its delivery date and hour number. Both retain combined
West/North values without assigning them to separate regions. All 431 rows
in those two wind files decoded successfully. Source evidence is in
`tools/inputs/history/annual-evidence.json`.

Annual DAM disclosure and regional solar checks decoded all 3,639,815 rows
in 146 CSV files from 14 downloaded publications. DAM samples cover one
January publication in each year from 2015–2025; the regional solar product
returned January files only for 2023–2025 in this check. Earlier empty January
listings are recorded, without inferring a product start date. Every decoded
file count matched an independent CSV row count. These files needed no reader
changes. See `tools/inputs/history/annual-dam-solar-evidence.json` for publication
queries, document IDs, source hashes and counts.

Annual 2015–2025 energy-curve and solar checks matched all 324 CSV members to
generated readers. The aggregate controllable-load reader accepts the older
`Aggr` filename spelling, including header-only files, while excluding regional
tables. Solar history accepts the intermediate delivery-date/hour layout with
`ACTUAL_SYSTEM_WIDE`. All 4,970,040 rows in the 20 selected controllable-load and
solar tables decoded, with independent CSV counts matching. Other curve tables
were checked only through their headers and first three rows. Publication IDs,
hashes and scope are recorded in `tools/inputs/history/annual-curves-solar-evidence.json`.

Intermediate SCED price-adder workbooks preserve `RTRUCCST30HSL` and
`RTNCLRNSCAP` as separate decimal fields. All 55,173 rows in seven January
publications from 2019–2025 decoded; timestamps, repeat-hour flags, system
lambda and both added fields matched the source cells on every row. Eight
demand-response workbooks from 2018–2025 also decoded all 816 rows, with all
seven data values per row matching their source cells. Their January 2024/2025
samples have 120 rows, compared with 96 in earlier samples. The separate
monthly deployment-factor product returned no January archives for 2015–2025.
The related 15-minute price-adder workbooks from 2018–2025 decoded 20,832
rows with all seven source values matching, including interval labels and
legacy price components. Newer components absent from those files remain
`None`. Each sampled workbook contains only the January worksheet.
Queries, document IDs, hashes and worksheet counts are recorded in
`tools/inputs/history/annual-workbooks-evidence.json`.

Annual ancillary-service disclosures from 2015–2025 decoded all 89,849 rows
in 208 CSV tables with independent row counts matching. Combined with six
COP-update samples, all 214 CSV members matched a generated reader. The COP
checks cover only headers and up to three rows; their January listings before
2020 were empty. No reader changes were needed. Publication queries, source
hashes and per-table counts are in `tools/inputs/history/annual-as-evidence.json`.

Quarterly outage samples from 2023–2025 decoded all 4,519 rows, preserving
separate planned and actual end dates. Annual load-forecast samples from
2019–2025 decoded 1,344 rows, preserving hour labels and DST flags. All source
data values matched independently in both checks; neither required reader
changes. Earlier January load-forecast listings in this probe were empty.
See `tools/inputs/history/outage-load-evidence.json` for the bounded query
periods, document IDs, hashes and counts.

The latest checks for NP6-569, NP6-655 and NP6-913 returned no archives or bundles.
Their typed catalog/document operations remain usable, but no historical row
schema is inferred from absent files. Point-in-time listing evidence is recorded
in `tools/inputs/history/availability-observations.json`.

Public ESR Integration Report PDFs (NP4-765-ER) expose five generated readers:
`daily_values_history`, `power_records_history`, `penetration_records_history`,
`soc_records_history` and `hourly_percentages_history`. Install `tinyercot[pdf]` for this optional support.
This report belongs to Public Reports and uses the same credentials.

```python
from datetime import datetime
from tinyercot import Client

with Client() as ercot:
    for row in ercot.np4_765_er.daily_values_history.rows(
        posted_from=datetime(2026, 9, 1),
        where=lambda row: row.peakLoadMW is not None and row.peakLoadMW > 80_000,
    ):
        print(row.reportDate, row.peakLoadMW, row.maxDischargeMW)
```

The table readers extract the first page's published tables. `reportDate` is the
operating date printed in the report; publication bounds select documents.
Power and energy fields name their MW/MWh units, percentage fields preserve
published percentages, and clocks retain the source's unspecified timezone.
`sourceNotes` preserves the daily table's definitions, including changes in
capacity terminology between older and newer reports. Record tables retain
separate power and penetration records, even when their MW values differ.
Older reports without a record section yield no record rows. Unsupported table
layouts raise. `hourly_percentages_history` reads the printed labels in the three percentage
charts: discharge/installed discharge capacity, charge/installed charge capacity,
and net output/ERCOT load. Values retain the printed decimal percentages. An
unlabelled bar has value `None`, not zero. `hourEnding` preserves source strings:
the sampled spring transition skips "03", and autumn charts show only "01"
through "24" without separately labelling a repeated hour. No extra hour or
timezone is inferred. The reader matches labels to the printed hour axis; it
does not estimate numbers from bar heights. Exact MW time series in the other
line charts remain outside the PDF reader's coverage.

Verified PDF table samples span December 2023, September 2024, September 2025
and September 2026. The first three omit the all-time record section; the 2026
sample contains seven record rows. These samples do not establish the exact
record-table introduction date or continuous historical completeness.


Intermediate 2020 and 2023 samples require additional historical layouts. The
SCED load-resource reader preserves all 35 published bid-curve points in the
2020 file, including blank points, alongside `HASL` and `LASL`. Older self-arranged
AS timestamps containing spaces before colons parse explicitly. Historical
ancillary-service responsibilities and quantities remain separate from newer
award/capability fields; the published `ECRSM ` header is recognized as well.

The wind reader preserves `actualLoadZoneSouthHouston`, `actualLoadZoneWest` and
`actualLoadZoneNorth` in the intermediate layouts. These fields remain distinct
from older combined-region and current `genLoadZone*` fields. With a separate
`deliveryDate`, the intermediate `HOUR_ENDING` value is an hour number rather than
the oldest layout's timestamp. All 213,456 rows across seven affected files were
decoded; the broader saved-file audit checks headers and short samples only and
does not establish continuous historical completeness.
