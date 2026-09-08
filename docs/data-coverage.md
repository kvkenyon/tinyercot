# Historical formats and source coverage

These notes describe verified source layouts and limitations, rather than a claim
of uninterrupted history. Paths under `tools/inputs/` are relative to the repository
root. See the [quick start](../README.md) and [runnable examples](../examples/README.md).

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
predates a table raises a missing-member error when using `read()` or `download()`.
For full-range retrieval, `backfill()` skips absent named tables in shared CSV
reports, including bundle members and remaining individual archive downloads.
This also handles tables that disappear from later reports without inventing an
introduction or retirement date. A missing generic CSV report, empty ZIP, corrupt
ZIP or invalid selected table still raises.
A live SCED disclosure check returned zero ESR rows for May 1, 2014 and all
96,480 ESR rows for September 6, 2026, matching the saved original. The selected
table is absent from the older file. See `tools/inputs/history/sparse-table-evidence.json`.

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
but absent from the sampled current ZIP. Explicit `read()` and `download()`
raise a missing-table error; `backfill()` skips that absent table.

SCED energy-curve history (NP3-908) has readers for wind, solar, non-intermittent
and storage supply and controllable-load demand, including four regional tables
for each. Older files also contain DAM demand, supply and minimum-supply curves
under `_2d_agg_dam_*_history`, plus separate `_2d_agg_esc_non_wind*_history`
readers. These older categories are retained explicitly. The sampled March 2014
ZIP contains tables no longer included in the sampled August 2026 ZIP. Explicit
`read()` and `download()` reject missing tables; `backfill()` skips them.
Header-only tables yield no rows.

DAM ancillary-service disclosures (NP3-911) have 36 readers matching the API
report tables and seven legacy RRS readers. Aggregate offer curves and the newer
DAM-specific curves keep separate `_2d_agg_as_offers_*_history` and
`_2d_agg_dam_as_offers_*_history` names. Legacy RRS load/generation cleared and
self-arranged quantities, and `RRSNC`, `RRSLD`, `RRSGN` offer curves, remain
separate from newer RRS response categories. The sampled 2014, 2025 and current
archives cover different sets of tables. Explicit `read()` and `download()`
reject missing tables; `backfill()` skips them. No reader substitutes another
category for an absent table.

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

## Direct historical retail load profiles

`Client.load_profiles` reads the annual files linked from
[ERCOT's historical load-profile index](https://www.ercot.com/mktinfo/loadprofile/alp).
All 30 linked archives (1997–2026) were downloaded and their worksheet headers
inspected. Six profile header layouts and a separate adjustment-factor layout
span XLS and XLSX files, including three profile layouts within 2012.
Compact source-derived test workbooks retain notes, headers, dates,
and selected data rows; their source and fixture hashes are recorded in
`tools/inputs/public-load-profiles-evidence.json`.

Each row contains one profile/weather-zone combination and trade date, with all
numbered 15-minute kWh columns preserved (100 in the annual backcasts, 96 in the
2008 original-profile companion table). Blank cells remain `None`. The
2013 source samples contain 92 nonempty cells on the spring transition and 100
on the autumn transition. No UTC timestamp is inferred. Optional `ADDTIME` is
retained as `sourceAddTime`, without assuming a timezone or public release time.
[ERCOT's published file layout](https://www.ercot.com/files/docs/2011/08/29/fileformatsloadprofiles.xls)
describes backcasts as settlement profiles using observed weather inputs.

The 2007 ZIP includes a separate auxiliary workbook. Its rows keep
`kind="auxiliary"` and their original filename. Workbook notes distinguish old
and new profile models around May 14, 2007; auxiliary production ends November
14. Do not collapse these overlapping rows into the main backcast series.

The 2008 archive also includes original pre-adjustment COAST profiles and
Hurricane Ike adjustment factors for September 13–28. Original rows have
`kind="original"`. `adjustments()` and `read_adjustments()` expose the factors
through their own typed model, with date, interval number and weather zone.
All 1,536 factors were compared with the complete original source table;
factors are never silently applied to energy values.
The direct factor download was verified byte-for-byte equal to the companion
workbook in the annual ZIP, so `adjustments()` fetches that smaller file directly.

Complete original-file comparisons cover 1997, 2007, 2008, 2012 and 2026:
255,408 profile-days and 25,540,160 interval cells. Each typed value, date, interval
number and source identity was independently compared with the original workbook.
The older checked years have no missing dates within their observed ranges;
1997 begins January 3, as its source note explains. These checks establish those
files' contents; the other linked years have header-layout evidence only.

Every field and all 5,232,800 interval cells in the complete 2026 archive were
independently compared with the source workbook: 52,328 rows, 248 profiles,
211 dates spanning January 1–August 30. All of May is absent. This is the
published file's coverage, not a guarantee of continuous historical availability.

## Historical four-coincident-peak allocations

`Client.coincident_peaks.allocations()` reads the annual allocation tables in
[ERCOT's public 1996–2020 archive](https://www.ercot.com/files/docs/2022/01/13/1996-2020_FourCoincidentPeakCalculations.zip).
The source includes originals, revised filings, comparison tables, and revision
components. They remain separate records with source member, sheet and section;
`kind` distinguishes allocation, comparison and revision-detail tables. The
reader does not select a supposedly final revision or recalculate reported shares.

The 1996 summary includes monthly loads in kW and loss-adjustment components.
The 1997 summary occurs below monthly submitted-load tables and contains annual
averages and adjustment percentages, but no monthly load columns. Its `peaks`
list is empty. Subsequent tables retain kW or MW as published. `adjustmentUnit`
is `factor` for the 1996 calculation and `percent` for the older tables whose
headers specify percentages; no scale conversion is performed. DUNS and entity
codes remain strings. Peak clocks are parsed only when supplied by the annual
column headers, with no inferred timezone or public-availability timestamp.

Independent extraction of the original archive verifies 4,345 rows across 43
annual worksheets and all 25 years: 27,290 numeric values plus source identity,
year, record kind, identifiers and published peak clocks. Tests retain all annual
worksheets from the source workbooks, rewritten with their cached values and
notes; the fixture omits unrelated workbook sheets. Hashes and comparison scope
are recorded in `tools/inputs/public-four-cp-evidence.json`.

`monthly()` and `read_monthly()` cover all 86 monthly peak tables in that archive:
7,633 records spanning 1997–2007, checked independently against 22,950 original
numeric cells, every peak timestamp, 5,249 settlement-metadata records, and
source identifiers. This is the monthly-table range, distinct from the annual
allocation range. Submitted kW, loss-adjusted peak kW and settled MW/MWh remain
distinct via `loadType`, `unit`, `energyMWh` and named adjustment fields. Relative
differences retain their dimensionless source values. SIS report cells have no
explicit published unit and remain unscaled in `sisLoadReport`.

Totals are retained, including three unlabeled 1997 totals (`entity=None`). An
unlabeled cross-month transmission-loss calculation below the 1997 peak tables
is not represented as a monthly load. Source row numbers, headers, table notes
and row notes are preserved. Original and revised 2001 files report different
August peak dates; both remain queryable by their actual peak dates. The August
2005 preliminary workbook has a worksheet named July; the source heading controls
the date. Peak clocks have no inferred timezone. Settlement run dates/times and
explicit stage/channel labels remain separate; missing times are `None`. The
source typo `9/17/032` is preserved with `runDate=None`, without guessing a year.
Preliminary report labels remain separate from FINAL settlement-run labels.

Tests retain all monthly worksheets from 29 source workbooks (68 sheets), including
their cached values and notes. Supporting calculation matrices and contact lists
are outside these peak-table readers.
The current NP9-83-M product page exposes report type 13037 through MIS listing
and download routes, which were inspected without calling MIS. The public direct
ZIP therefore supplies history through 2020, not recent 4CP filings.

The inspected UFE page provides annual PowerPoint analysis reports. No slide
extraction was added: these reports fall outside this release's operational
and market time-series focus.
