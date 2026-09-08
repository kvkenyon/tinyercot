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

`load_profiles.counts()` and `read_counts()` decode the underlying Data sheets in
[the public profile-count archive](https://www.ercot.com/files/docs/2021/10/21/Profile_Type_Counts.zip).
All 97,924 assignment records in 141 workbooks were independently compared with
the original cells: 97,924 integer counts and 391,696 dimension values (weather
zone, IDR/NIDR meter data type, TDSP and profile type). The pivot sheets are
filtered aggregate views over those Data tables; they are not counted as extra
assignments. Four header layouts differ only by an empty helper column.

The 139 dated workbooks have 138 distinct filename dates from April 9, 2013
through August 6, 2026; the original and corrected March 12, 2018 snapshots are
both retained. These are source labels, not availability timestamps. Two other
filenames contain `201500803` and `201605614`; their 1,382 records retain those
labels with `snapshotDate=None`, without using workbook-modification times to
guess dates. Unbounded reads include them; date-bounded reads exclude them.
Five May 2024 records have blank weather zones. They remain `weatherZone=None`,
including repeated dimension combinations with distinct counts. Blank trailing
rows are skipped; counts are neither aggregated nor filled. Source comparisons
and an eleven-workbook fixture are recorded in the load-profile evidence file.

## Historical settlement loss factors

`Client.loss_factors` follows the [data aggregation index](https://www.ercot.com/mktinfo/data_agg)
and its 25 linked annual pages. All **72 interval-data downloads**, totaling
215,272,347 bytes, were independently compared with the typed reader using
xlrd/openpyxl: **301,829 series/day rows, 28,975,512 numeric factors, and 478,576
blank interval cells**, including every identifier, timestamp and source column.
The [source manifest](../tools/inputs/public-loss-history-sources.csv) records each
actual URL, SHA-256, row/value counts and operating-date coverage.

Source dates span **July 31, 2001–July 31, 2026**. Series coverage is uneven:
actual distribution history begins **December 7, 2006**, with 25 dates in that
annual download. Index years, upload dates and worksheet titles are not coverage
guarantees. The 2003 distribution sheet labeled “Jan thru Jun” also contains
later dates; date filters use the records themselves. Files and sheets remain
separate, including overlapping fall-back rows.

Modern workbooks expose 100 numbered INTV positions; older XLS/XLSX workbooks
use clock columns and separate fall-back sheets. Each interval keeps its
position, unscaled factor and `sourceLabel`, including repeated clocks and
24:00. Blanks remain `None`. The 2013 actual TLF annual sheet contains one
100-interval fall-back row beneath a 96-interval header: all values and its
trailing timestamp are retained, and its interval labels are `None`. The
companion DST-sheet record is not silently deduplicated. Trailing 2003 orphan
loss-code labels without dates or values are not observations.

Recorder IDs, TDSP names and loss codes stay distinct. Nineteen 2014 forecast
DLF DST rows use `DISTLOSSFACT_...` recorder IDs and an unlabeled numeric second
column. These remain `recorder` and `sourceSecondaryIdentifier`; TDSP/loss code
are `None`. Legacy column-four markers remain in `sourceMarker`. Other legacy
second-column labels are also retained, alongside the typed loss code.

Early distribution workbooks omit the actual/forecast distinction internally.
Live reads retain the actual index link in `sourceFile` and use its forecast
label. Saved reads can provide `source_file=archive`; otherwise unidentifiable
`kind` values stay `None`. START TIME/STARTTIME and TIMESTAMP/LSTIME are parsed
without an inferred timezone or public-availability claim. Date bounds are
inclusive; `where` accepts a typed predicate. MIS routes remain excluded.

The original 2026 comparison and four-date fixture remain in
`tools/inputs/public-loss-factors-evidence.json`. New historical evidence is in
`tools/inputs/public-loss-history-evidence.json`, with all 26 original index
pages and nine complete, unchanged legacy workbooks used in tests. These cover
header variants, timestamps, repeated intervals, missing identifiers, orphan
labels and the misaligned 2013 row. Fixtures are excluded from the wheel.

## Annual transmission-loss coefficients and seasonal operator load shares

`Client.transmission_loss_coefficients` follows the same 26 data-aggregation
indexes as the interval-loss reader. It exposes the final published SSC/SIC
coefficients and the separate SONL/SOFFL/SONLF/SOFFLF input basis from **all 26
annual workbooks, 2001–2026**. All **948 area/season records**, **5,682 numeric
cells** and **six blanks** were compared directly with original XLS/XLSX cells,
including year/as-of headings, area labels, source rows and effective periods.
The six blanks are the LPL spring 2021 entry; it remains a record with missing
values. Both coefficient columns and all four input columns survive.

Areas are matched by published labels because the 2002 COCS coefficient columns
are shifted relative to their input columns. PUB and BPUB labels remain distinct,
as do Rayburn and TEXLA. Final and input ERCOT correction labels are retained
separately. SSC and SIC carry percent/MW and percent units; the on/off-peak input
loss-factor cells retain their fractional values. In all populated NOIE cases,
the original SSC × load + SIC matches the input loss factor × 100. The SDK does
not recalculate or apply coefficients. Internal base-case and “For Testing Only”
calculation tables remain in the downloadable original workbooks.

The 2001–2010 workbooks have no effective-period tables (**348 records**).
The source winter ranges in 2020 and 2026 are reversed (**19 records**):
`12/01/2021 - 02/28/2021` and `12/01/2027 - 02/28/2027`. Their raw text remains in
`sourceEffectivePeriod`, with both usable date bounds `None`; dates are not
repaired or inferred. The remaining **581 records** retain explicit bounds,
including the change from an August summer end in 2011 to September in 2012,
and leap-year winter ends. Workbook as-of dates and versions remain separate
from any claim about public availability. Live queries attach the original
`PublicFile`; saved reads accept it through `source_file`. Overlaps and revisions
are not deduplicated by year, area or season.

`Client.load_shed` reads both current workbooks linked from the
[load page](https://www.ercot.com/gridinfo/load). All **42 operator load-share
values**, headings, operator names, effective dates and notes were compared with
the originals. Summer starts **April 1, 2026**, winter **September 1, 2026**,
according to the workbook notes rather than upload dates. These are published
load percentages, not actual shed MW or probabilities. Delegation footnotes
remain attached; no end date or renormalized percentages are invented.

Both readers support original saved workbooks/ZIPs and typed predicates with
`tinyercot[files]`. The source manifest is
`tools/inputs/public-seasonal-tables-sources.csv`; verification and fixture
provenance are in `tools/inputs/public-seasonal-tables-evidence.json`. All 28
complete original workbooks are used in regression tests and excluded from the
wheel. Coefficient discovery reuses the 26 captured original index pages.

## CRR time-of-use hours and POLR territory totals

`Client.crr_hours` discovers the calendar linked from
[ERCOT's CRR page](https://www.ercot.com/mktinfo/crr). The complete captured
workbook contains 48 monthly records for January 2026–December 2029. Every
OffPeak, PeakWD, PeakWE and Total cell is compared with the typed result, along
with the delivery month and source identity. Counts are retained as published,
including 743 hours in March 2026, 721 in November 2026, and 696 in February
2028. This is a trading calendar, not observations of future market activity.

`Client.polr` discovers the counts/energy reports linked from
[ERCOT's retail page](https://www.ercot.com/mktinfo/retail). All 24 rows in the
captured 2026 report are compared with the original workbook: six territories
and four premise classes, with 24 active-ESIID counts and 24 annual-kWh totals.
Counts describe active ESIIDs with usage on March 31, 2026. Energy describes
all ESIIDs active during April 1, 2025–March 31, 2026. These are distinct
populations; no per-customer usage ratio is calculated. The source uses the
most current premise-type assignment, as retained in its cover notes.

Both services expose `files()`, `download(file)`, `rows(where=...)` and
`read(data, filename=..., where=...)`. Predicates receive concrete typed rows.
Dates come from table contents, not filenames or index labels. Saved ZIPs keep
overlapping members distinct. Both complete original workbooks are included
as regression fixtures, byte-for-byte. Source URLs, hashes and comparison
counts are in `tools/inputs/public-market-tables-evidence.json`. No older
history is inferred from the years embedded in download URLs.

## Retail transaction history

`Client.retail_transactions` discovers the monthly transaction archive linked
from [ERCOT's retail page](https://www.ercot.com/mktinfo/retail). The complete
inspected archive has 20 workbooks and 444 sheets, covering January 2025–August
2026. All 9,126 records were independently compared against the original files:
277,433 daily counts, 9,126 reported totals, 9,126 reported averages, every date,
transaction code and workbook/sheet identity. All 608 calendar dates appear in
the source headers. This describes aggregate transaction counts, not individual
customer records or metered energy.

There are 30 original transaction codes and a Grand Total row in each sheet.
Typed `transactionCode=None` identifies those 444 total rows. `sourceSheet`
retains each original category. Territory, customer-class and ERCOT-wide views
overlap and must not be added together. Four sheets in April 2025 and January
2026 are literally named ` Inbound` and ` Outbound`; their eight records retain
these labels without an invented category. Codes retain their literal spelling,
including suffixes such as `814_06_MVI` and `814_06_SW`.

Monthly totals match the sum of their published daily counts in this archive.
The 8,848 rounded averages remain exactly as published rather than being
recomputed. Each typed month keeps its daily dates/counts and separate reported
total/average. The `where` predicate can select dates, codes and categories.
`files()`, `download(file)` and `read(data, filename=..., where=...)` support
direct discovery and saved archives. Original member names and overlapping
files remain separate; the current archive filename does not limit the dates
that can be queried.

Evidence is recorded in `tools/inputs/public-retail-transactions-evidence.json`.
The regression fixture retains five complete original workbooks byte-for-byte,
covering all 30 codes, first/latest months, 28/30/31-day months and every unnamed
category. It contains 2,280 records and 68,864 daily counts. No older coverage is
inferred from the year embedded in the source URL.

## Interim indicative ORDC archive

`Client.indicative_ordc` reads the archive linked under the interim scarcity
pricing section on [ERCOT's real-time market page](https://www.ercot.com/mktinfo/rtm/index.html).
The complete original ZIP contains 34 CSVs and 9,826 records, spanning October
17, 2013 at 00:00:16 through November 19 at 23:55:08, with all 34 calendar dates.
The page description says November 20, but no record on that date is present.
All 49,130 numeric fields, timestamps, repeat-hour flags and member identities
were independently compared with the original CSVs. The entire original ZIP
is retained as the regression fixture; provenance is in
`tools/inputs/public-indicative-ordc-evidence.json`.

Every record is explicitly `indicative=True`, separate from the generated
realized ORDC/settlement histories. ERCOT labels this section as interim pricing
before June 1, 2014. The fields preserve SYSTEM_LAMBDA, RTOLCAP, RTOFFCAP, RTORPA
and RTOFFPA as decimals under their source names, without applying adders or
constructing a combined price. Original timestamp text is retained beside the
parsed naive timestamp. The source's `00:xx AM` notation maps to midnight;
9,814 N flags and 12 Y flags remain literal, including the November 3 repeat
hour. No UTC offset or uniform five-minute sampling is inferred. Nested ZIPs,
standalone CSVs and typed predicates are supported without optional packages.

## MORA forecast percentiles

`Client.resource_outlook.files()` discovers workbook links on the
[resource adequacy page](https://www.ercot.com/gridinfo/resource) and its linked
historical year indexes. All 37 downloaded workbooks have a PRRM Percentile
Results sheet. Their reporting months span December 2023–November 2026, with
36 distinct months and two December 2023 versions. The typed `percentiles()`
and `read_percentiles()` readers cover **27,500 original values**: 9,240 gross
demand, 8,228 solar, 9,592 wind, 374 thermal-outage, 33 non-extreme-weather outage
and 33 extreme-weather outage values. Every value, percentile, hour/daily label,
metric heading, report month, footnote and source identity was independently
compared with the original workbooks. No selected value was blank in this capture.

Source hour labels vary. December 2023 supplies solar hours 8–18 and wind hours
7–22, with daily thermal-outage percentiles and no gross-demand table. Later
files expand the hour coverage and introduce new demand definitions. No omitted
hour or metric is synthesized. Daily outages retain `hour=None`; percent strings
are normalized to fractions while original labels remain visible. Winter
weather-outage regimes and their explanatory footnotes stay distinct.

The 27,478 values whose headings specify MW retain that unit. The two earliest
daily-outage tables omit a unit in their labels, so their 22 values retain
`sourceUnit=None`. These are assessment-month forecast distributions, not dated
realized observations or joint scenarios. Report-month labels and member names
preserve the available revisions. URL dates and revision labels do not establish
point-in-time public availability.

Evidence is in `tools/inputs/public-mora-percentiles-evidence.json`. The fixture
retains nine complete original workbooks, byte-for-byte, containing 6,006 values
and every supported metric family. Resource-detail, capacity-summary and
load/resource-balance tables have separate readers described below.

## MORA resource capacities

`Client.resource_outlook.resources()` and `read_resources()` cover the Resource
Details sheets in the same **37 workbooks**, December 2023–November 2026. All
**61,949 rows** were compared against their original B–J source cells: **60,766
unit rows and 1,183 summary rows**. Counts include repeated monthly records and
both December 2023 versions, not distinct generating units. Summary rows include
totals, capacity contributions and adjustments; some have identifiers in the
source's unit-code column. Unit rows have an INR, county, zone or service field;
the source summaries lack those fields. Original names, codes, fuel labels,
categories, rating labels, worksheet rows and footer notes are retained.

There are 60,331 service years, 280 service dates, three literal `#N/A` errors and
1,335 blank service fields. No service date is inferred from the reporting month.
The 87 blank installed capacities and 14 blank reported capacities remain `None`;
zero and negative values remain numeric. The October 2025 workbook omits the
initial category heading, so its first 402 records retain `category=None`.
Unheaded helper cells beyond column J are excluded from the named resource table;
they include repeated capacity values and a zero beside a section heading.

These are assessment-month ratings, not measurements of generation or proof that
planned resources are in operation. Seasonal and monthly rating labels remain
explicit, as do planned, unavailable and mothballed categories. Footnotes explain
that battery fleet contribution is calculated separately, and that planned
resources approved for synchronization can be assumed available for the season.
Summaries and their underlying unit capacities should not be added together.

`tools/inputs/public-mora-resources-evidence.json` records the full source
comparison. Tests reuse the nine complete originals in `mora-percentiles.zip`
and add three complete originals in `mora-resources.zip` for service dates,
missing categories and helper columns. Fixtures are excluded from the wheel.

## MORA category capacities and load/resource balance

The `capacities()` / `read_capacities()` readers expose **1,494 category rows**,
with **1,494 installed-capacity values and 1,854 expected-capacity values**.
`balance()` / `read_balance()` expose **990 load/resource-balance rows**, with
**1,221 scenario values across 33 typed metrics**. All **4,569 numeric cells**
in both sheets of the same 37 workbooks were independently compared with the
source, including row coverage, scenario labels, report months, notes, clocks,
time-zone labels and category hierarchy. No numeric cell was blank in this capture.

Category rows distinguish operational, planned and total resources. The original
Excel indentation supplies `resourcePath`, keeping e.g. Wind/Other separate from
Storage/Other. Indentation levels need not be consecutive. Parent and child rows
both retain their source values and must not be added together. Installed capacity
is stored once per category; expected values form a typed list of scenarios.
The March 2024 expected-capacity header is blank and remains `None`.

Older workbooks publish two scenario columns. December 2023 has 8 a.m. and 5 p.m.
values; March 2024 distinguishes late-March conditions at 6 p.m. from early-March
cold conditions at 8 a.m. April 2024 includes two different wind scenarios at the
same 8 p.m. hour. Each original scenario label is retained, with its parsed local
clock and explicit CST/CDT label where present. The 840 scenario values without
a zone retain `timeZone=None`; the others comprise 1,692 CDT and 543 CST values.
No dated operating hour or UTC timestamp is inferred from the reporting month.

Balance metrics retain distinct large-load and large-flexible-load adjustments,
and distinguish thermal capacity that explicitly excludes emergency agreements.
Original metric labels and source notes accompany the stable typed names. These
are forecast/scenario quantities, not realized demand, supply or operating reserves.
The scenario tables do not provide the hour-by-hour probability images or embedded
risk-chart data; those are not counted in this coverage.

`tools/inputs/public-mora-summaries-evidence.json` records the source comparisons.
Tests reuse twelve original workbooks already retained for other MORA readers and
add the complete March 2024 workbook in `mora-summaries.zip`. The thirteen originals
contain 526 category rows (727 expected-capacity values), 338 balance rows (461
scenario values), all 33 metrics, and the missing heading. Fixtures stay outside
the wheel; category hierarchy requires the `files` extra and original XLSX format.

## Capacity changes and project histories

`Client.capacity_changes` discovers all **169 linked XLSX workbooks** on the
[resource page](https://www.ercot.com/gridinfo/resource) and its 26 historical-year
indexes. The source set covers **96 reporting months, August 2018–July 2026**,
including annual/monthly companion files and corrections. The current and
historical link captures were compared with the SDK discovery results, including
the older `Monthly Capacity Changes` title and capitalization differences.

The project reader exposes **42,628 records**. Every named field was compared
with the original workbooks, including projected COD, agreement and synchronization
dates, original identifiers, source year, technology, MW rating and financial
security. Repeated headers and one-cell group/footnote rows are not projects.
Resource codes in the INR column remain valid identifiers. The source year can
differ from the projected-COD year and is preserved independently.

There are 82 missing agreement dates and 13 literal agreement-status strings:
`12/31/1899` once, `Not Required` once and `Date Not Available` eleven times.
The literal 1899 marker is not converted into a real agreement date. The source
also has 52 missing fuel values and 58 missing financial-security values. Original
October 2023 reports retain their blanks; corrected versions retain the filled
values and the accompanying correction text. Comments about partial or rescinded
synchronization approval remain attached to their project records.

The totals reader exposes **16,554 rows with 92,312 numeric values and four blank
capacity cells**, all compared against the original source. Installed, synchronized
and operational measures retain separate typed fields. The combined installed/
operational-and-signed measures retain their original column labels; they are not
substituted for a total including every planned category. Other-planned capacity,
distributed generation, small generators and DGR comments stay distinct.

Periods comprise 10,722 integer years, 4,770 dates under `Month/Year`, and **1,062
dates under a `Year` heading**. The reader keeps each original period and heading,
including the twentieth day used in monthly charts. Period years span 1999–2033;
later points are source projections, not observed future capacity. A September
2018 battery sheet has seven annual totals and no project table; both readers
handle that distinction. Values from parent totals, components and companion
reports should not be added indiscriminately.

Live queries retain `sourceFile` with the original URL and title, distinguishing
the two November 2018 downloads that share a filename. Saved ZIPs retain member
paths. Different companion-file dates are not reconciled: July 2026 reports give
different projected CODs for the Wise County repower project. A report-month label
or source URL does not prove immutable publication time or actual commissioning.

Source URLs, hashes and per-file counts are recorded compactly in
`tools/inputs/public-capacity-changes-sources.csv`; comparison details and fixture
provenance are in `public-capacity-changes-evidence.json`. Seventeen complete
original workbooks are retained in the test ZIP, with URL-date folders preserving
same-name revisions. Fixtures and evidence are excluded from the wheel. Coverage
here concerns the underlying project and capacity tables; it does not assert that
every chart-specific annotation or other resource-page document is parsed.

## Historical zonal weather

`Client.historical_weather.rows()` and `read()` cover all eight zonal workbooks in
[ERCOT's historical weather ZIP](https://www.ercot.com/files/docs/2002/12/11/weather1996_2000.zip).
Each contains four worksheets: CLOUDCOVER, WINDSPEED, DEWPOINT and DRYBULB TEMP.
The source notes describe a weighted combination of weather stations. The public
index labels the archive 1996–2000 and says additional weather data is unavailable
under contractual limitations; the actual workbooks extend through January 10,
2001. Bounds use those actual dates.

Independent comparison covers every source cell: 58,784 variable/day records and
1,410,816 hourly values across 32 worksheets. Each zone/variable has 1,837
consecutive dates from January 1, 1996 to January 10, 2001, with 24 numeric cells
per date. Dates, zone identities, variable names, hour-column numbers and source
notes were also compared. A compact fixture retains six dates from all 32 sheets,
including leap day, both DST transition dates and the final January 2001 date.
Source hashes and comparison scope are in `tools/inputs/public-weather-evidence.json`.

The workbooks do not state measurement units; `sourceUnit` stays `None`, and no
scale conversion is performed. Hour numbers are the published column numbers,
without an inferred hour-ending convention, DST flag or UTC offset. The reader
can retain blank hourly cells as `None`, although none occur in this original
archive. No newer or continuous present-day weather history is claimed.

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

## Distribution-loss formula parameters

`Client.distribution_loss_coefficients.files/download/rows/read` covers all 28
summary workbooks linked from the [distribution methodology index](https://www.ercot.com/mktinfo/metering/dlfmethodology),
2001–2026. Both 2007 and 2024 period variants remain separate. Discovery tolerates
the source's 2023 “Lost Factors” title. The complete bundles remain downloadable;
the typed reader selects the ERCOT summary, excluding narrative attachments and
hypothetical example curves.

All **466 records and 1,398 numeric parameters** were compared against direct
spreadsheet reads: 114 legacy AAL/K/ADLF records and 352 F1/F2/F3 records. The six
explicit nullable parameter fields retain the two formula families. Source TDSP
names and loss codes remain unchanged. ERCOT annual MWh, interval count, average
interval MWh and optional peak MW preserve the published cached baseline values.
Negative parameters and rounded baseline averages are not corrected or rescaled.

The filename year is a label, not an effective date. Baseline dates describe the
load inputs. The 2026 workbook's Start title says 2025; both are retained. Formula
text, original baseline label, member, sheet, column and optional `PublicFile`
provide source context. No publication or coefficient applicability dates are
inferred, and no loss formula is applied by this reader.

Seventeen original XLS summaries use Excel's built-in workbook protection.
The optional files extra uses msoffcrypto-tool to read those originals with the
public default key; it does not require ERCOT credentials. Core-only discovery
and downloads remain independent of spreadsheet and decryption dependencies.

`tools/inputs/public-distribution-coefficients-sources.csv` records original
archive and summary hashes. `public-distribution-coefficients-evidence.json`
records verification and limitations. The fixture ZIP contains all 28 complete,
unchanged summaries, including protected bytes; the original discovery HTML is
also retained. Regression tests compare every parameter and the baseline fields
against direct spreadsheet reads, exercise anonymous discovery, preserve both
revisions, and check source-year conflicts and JSON round trips. Fixtures are
included in the source distribution, excluded from the installed wheel.

## Daily 4CP source energy

`Client.coincident_peaks.daily_files()` follows the current and 25 historical
aggregation indexes. Their one direct daily-source link is the
[2017 4CP source workbook](https://www.ercot.com/files/docs/2018/01/23/4CP_Daily_Posting_2017-11-27.xlsx).
`download(file)`, `daily()` and `read_daily()` expose its original workbook and
typed daily records, independently of MIS and API credentials. The existing
no-argument `download()` still retrieves the annual 1996–2020 allocation archive.

The daily workbook contains **16,445 rows in each of INITIAL and FINAL**, spanning
**2017-06-01 through 2017-09-30**: 135 source entities, 122 dates, and **3,157,440
numeric interval values** in total. INITIAL uses source channel 1, FINAL channel
2; their values differ and both remain queryable. The source includes ERCOT and
individual entities, so rows are not an additive partition. FARMERS ELECTRIC CO
OP INC PRTN RC (TDSP) has only 97 dates in each sheet; other entities have all 122.
No missing rows are synthesized.

`CoincidentPeakDay` retains the operating day, entity, settlement, channel,
`EnergyInterval` records, original unit header, file/member/sheet and one-based
source row. Each interval contains its original one-based position, source label
and nullable `energyMWh`. These files have 96 columns, including the original
`24:00` label, and no blank numeric cells. Clock labels have no inferred timezone.
The source's MWh values are not converted to MW or peak allocation shares.
Inclusive date filters and typed predicates do not combine settlement versions.
A file URL date or settlement stage does not establish historical availability.

The complete original workbook is retained unchanged in
`tools/inputs/coincident-peaks/daily-2017.xlsx`. Original URL/hash, coverage and
limitations are recorded in `public-daily-4cp-evidence.json`. Tests compare every
numeric interval and entity/date/channel/header directly with openpyxl, verify
all entity date sets, preserve the initial/final difference, and exercise exact
source-index discovery with anonymous date-filtered queries. The fixture ships
in the source distribution and is excluded from the installed wheel.

## Historical zonal-market energy

`Client.zonal_energy.files/download/rows/read` covers all ten generation/load
MWh workbooks linked from the [public aggregation indexes](https://www.ercot.com/mktinfo/data_agg),
2001–2005. `totals/read_totals` retain the published summary and detail aggregates
separately. Files are anonymous downloads; parsing uses the optional files extra.
Inclusive operating-date bounds and typed predicates apply to daily reads.
Bare unnamed workbooks require an explicit generation/load kind; live reads
attach the actual file link. Zone codes retain the original market vintage.

Source comparisons cover **13,886 daily records**, **1,332,244 numeric interval
values and 29,016 blank interval cells**, **1,170 additional source numbers**,
and **88 published totals** (52 summary, 36 detail). One undated `Grand` row has
96 interval-column aggregates, retained only among the totals. Generation raw
sheets for 2001–2004 duplicate the published daily values; they remain in the
original download without emitting duplicate daily observations. Cached summary
and detail totals can differ: the 2001 generation grand totals are respectively
115512611.682897 and 115512613.08008096 MWh. Neither is silently corrected.

Coverage begins **2001-07-31 for generation** and **2001-08-01 for load**.
All vintage zones have full calendar-year dates in 2002–2004; load also covers
all of 2005. Generation in 2005 has only 328 dates per zone, missing June 22
through July 28 in all five zones. No rows are synthesized to fill the gap.
Source clock/position labels do not establish UTC instants or modern-zone mappings.

Nine load rows extend to 100 values under 96 interval headers: four zones on
2003-10-26 and five on 2005-10-30. Those extra values reconcile with the original
daily totals; all 100 remain available, with clock labels `None` for the
misaligned rows. The 805 additional generation numbers instead remain typed
`ZonalSourceNumber` records with their original column and header, without an
assumed unit or interval meaning. The 2003 W03 source calls a numeric column
`ORIGIN`; its 365 daily values and one aggregate remain source numbers, leaving
`totalMWh=None`. String origin markers, recorder/channel fields and the actual
trailing timestamps are also retained. Numeric energy cells accidentally
formatted as dates in the XLS files remain their original numbers.

`ZonalEnergyTotal.scope` separates summary from detail totals; `share` retains
the original fractional value and `sourceShareHeader` retains its displayed
label. Original labels, headers and notes accompany totals, including unlabeled
grand totals. Values are never recomputed or rescaled. The filename year and
source timestamps do not establish observation availability or settlement finality.

`tools/inputs/public-zonal-energy-sources.csv` records all original URLs/hashes;
`public-zonal-energy-evidence.json` records counts and limitations. All ten complete
original workbooks are retained unchanged in `public-tables/zonal-energy.zip`,
including summaries and duplicate raw sheets. Regression tests compare each daily
interval, numeric metadata cell, source timestamp and published total directly
with xlrd, verify the missing dates and source quirks, and exercise anonymous
index discovery and typed saved/live queries. Fixtures remain outside the wheel.

## MORA conditional wind/BESS risk curves

`Client.resource_outlook.risk_points/read_risk_points` reads exact numerical
coordinates from the original chart caches and follows workbook/drawing
relationships to the source worksheet. All 37 retained MORA workbooks were
checked: three contain native numerical risk curves, yielding **72 points and
144 numeric coordinates**. June 2026 has ten points per EEA/EEA3-load-shed series;
October and November have thirteen per series. The remaining 34 reports do not
supply these numerical chart caches and yield no points through this method.
Their original graphics remain available in the workbook download.

`MoraRiskPoint` retains the reporting month, event, wind MW, fractional
probability, fixed BESS availability MW, simulation count, chart/scenario hours,
original axis/series labels, complete worksheet notes, original zero-based point
index and file/member/sheet/chart provenance. Values are parsed directly from
XML decimal strings, without interpolation or image digitization. The zero final
EEA3 probability in October remains zero. Revisions are not deduplicated.

The three source scenarios fix BESS at 2,070 MW (June), 4,473 MW (October) and
4,394 MW (November), with 10,000 model runs stated in each worksheet. These are
conditional modeled outcomes, not realized operating observations or an
unconditional forecast. November's chart hour is 20:00 while its worksheet
scenario hour is 19:00; both remain explicit. Neither an assessment month nor
source file URL establishes when the forecast became available, and no timezone
is inferred for these chart labels.

`tools/inputs/public-mora-risk-evidence.json` records source URLs/hashes, fixture
locations, comparison scope and limits. Two additional complete original
workbooks are retained in `public-tables/mora-risk.zip`; existing original
November and March fixtures are reused. Tests compare every original coordinate,
scenario context, both hours, zero probability and JSON round trips, and exercise
anonymous typed queries plus a report without numerical curves. Fixtures remain
outside the installed wheel.


## Complete intermediate and annual CSV checks

A subsequent check decoded every row in **221 distinct intermediate/annual CSV samples**
across **92 history readers and eight products**, totaling **28,881,274 rows**.
These cover SCED/DAM disclosures, aggregated offer curves, highest-offer data,
wind actuals, and load/solar forecasts. The earlier cross-product audit had checked
only their headers and up to three rows. Each complete file now decodes through
its concrete generated reader, with its row count cross-checked against a
separate CSV reader. No parser changes were needed.

The 433 oldest/current CSV members already had corresponding full-file decode
receipts in the per-product evidence, so those files were not decoded again.
The three saved audits contain 661 CSV entries, including seven files reused
between the intermediate and annual checks; those repeats are excluded from the
new totals. Every entry now has a complete-file decode receipt. It does not establish every intervening publication's layout,
gap-free history, or an independent comparison of every numerical value.

`tools/inputs/history/intermediate-full-files.csv` records each reader, original
archive/member identity, source hash, byte size, and source/decoded row count.
`intermediate-full-file-evidence.json` records the decoder commit and hashes,
scope, and totals. The same evidence records the separately listed annual DAM/RT
hub/load-zone and DAM ancillary-price products that use ICE/MIS routes; those
remain outside the no-MIS scope. Their oldest years were not queried, so the
Public Reports archive bounds are not a claim about all price history ERCOT holds.

## Modeled generation profiles

`Client.generation_profiles` adds typed access to direct wind and solar planning
profile downloads on the resource adequacy pages. It supports `DATE` with `TIME`
or `TIME_CST` CSV layouts (including an extra leading year column), embedded
Excel site metadata, and ZIPs containing those supported tables. Source column
labels are retained as keys in `GenerationProfileHour.generationMW`; site
metadata has its own `GenerationProfileSite` model.

Eight complete original downloads were checked against separate CSV/openpyxl
reads: **789,073 hourly rows and 18,187,437 generation values**. They cover the
1980–2020 metropolitan and rural distributed-solar series, 2020 single/dual-axis
hypothetical solar and operational/planned/hypothetical wind CSVs, and the
2020–2021 operational/planned solar and wind workbooks. The workbook numeric
comparison uses openpyxl's stored-number interpretation, not exact XML lexemes.
All embedded metadata fields for 377 workbook sites were also compared. Live
discovery found 69 datasets: 25 CSVs, 19 workbooks and 25 ZIPs.
All 25 discovered direct CSV header samples and their first two rows also decode;
that sample check does not establish their complete-file coverage.

Both workbooks retain repeated 01:00 clocks on November 1, 2020 and November 7,
2021. The wind workbook also contains January 1, 2022 at 00:00; its filename ends
in 2020–2021. The parser neither clips dates to filenames nor deduplicates clocks.

These are **modeled generation scenarios**, not metered historical generation or
point-in-time forecasts. The source's [development report](https://www.ercot.com/files/docs/2022/12/19/ERCOT_1980-2021_WindSolarGenProfiles_FINAL_public.pdf)
describes weather reconstruction and calibration to generation observations.
Separate profile vintages should not be combined as an observed fleet history.
Older ZIP layouts and the remaining Excel profile vintages remain unverified
or unsupported; this addition does not close those gaps. The four companion key
workbooks are covered below.

`tools/inputs/generation-profiles/evidence.json` records the eight original file
URLs, hashes, counts and boundaries. `profiles.zip` retains three complete,
unchanged originals for regression tests; `csv-header-samples.json` explicitly
contains only captured header/row excerpts. All fixtures stay outside the wheel.


### Generation-profile site keys

`generation_profiles.key_files()` discovers all four directly linked wind/solar
key workbooks for the 1980–2020 and 1980–2021 profile vintages. `read_keys()` yields
`GenerationProfileKey` objects containing typed site/unit rows, summary rows and
located source notes. Fresh downloads match all four original fixture hashes.

All source cells in **11 site/unit tables (1,828 rows)** and all numeric summary
rows (**32 rows**) were compared with independent original worksheet positions.
The reader preserves both solar table sections across repeated headers, detailed
wind unit mappings, distributed-solar metro and rural metadata, capacities,
coordinates, equipment descriptions and source labels such as `Lat`/`NA` tilt.
The older wind workbook's legend marks four sites and twelve unit rows as modeled
queued plants; those flags were checked without mistaking the adjacent legend for
a site's own flag. The newer workbooks have no such legend and return `None`.

Two source inconsistencies remain explicit. The 1980–2020 solar summary reports
313 utility profiles while detailed scenario totals sum to 331. In the
1980–2021 solar publication, 163 of 164 key unit codes match profile columns;
`TREBA_UNIT 1` in the key differs from `TREBA_UNIT1` in the profile. Neither is
silently normalized or repaired. Site families and publication vintages are never
automatically joined.

The four unchanged originals total 183,426 bytes under
`tools/inputs/generation-profiles/keys/`; their source URLs, hashes, table counts,
legend checks and identifier mismatch are recorded in `evidence.json`. Tests
exercise the originals, source-summary discrepancies, nested workbook ZIPs and
credential-free discovery/downloads. Fixtures remain excluded from the wheel.


### Older wind archives and hypothetical-solar workbooks

The generation-profile reader supports the older `YYYYMMDD` / `HHMM(CST)` CSV
headers and separates side-by-side date/clock tables into independently dated
records. `sourceBlock` identifies the original table on both records and site
metadata. Timestamp columns never enter the MW mapping, and an entirely empty
trailing block does not create an observation.

All **76 CSV members in seven wind archives** were inspected. They contain
**40 distinct CSV bodies**, with 36 byte-identical copies reused across archives.
Independent CSV comparisons cover every date, clock and MW value in those 40
bodies: **499,446 decoded records and 40,418,046 generation values**. These counts
retain overlapping source data; they are not unique market observations.

In `ERCOT_onshore_2011.CSV`, the first table contains 2011 data while the adjacent
offshore table contains 2013 data. The last six rows have an empty, shortened
offshore block. The parser retains 8,760 onshore and 8,754 offshore records with
their respective dates. Single-table files can also extend beyond filename years:
the 2016 wind files begin December 31, 2015 at 18:00 and end December 31, 2016 at
23:00. Clocks are retained without an inferred UTC conversion.

Both 2020–2021 hypothetical-solar workbooks were compared completely, covering
**35,088 hourly records and 5,228,112 generation values** across 149 sites per
workbook. All embedded site metadata was checked, including `SINGLE`/`DUAL`
tracking, 50 MW capacities, counties, CDR zones and hypothetical plant status.
The reader now exposes the original `Tracking` field as `site.tracking`.

Original file/member hashes, archive overlap and comparison scope are recorded
in `tools/inputs/generation-profiles/formats/evidence.json` and
`legacy-wind-members.csv`. Regression tests use the original 2015 wind ZIP,
a complete original compound-table CSV member and the unchanged dual-axis
workbook. Fixtures are excluded from the installed wheel.

The two older wind-shape workbook layouts are also supported. Complete original
workbook comparisons cover **131,496 records / 12,229,128 values / 93 sites**
for existing sites and **131,472 records / 17,485,776 values / 133 sites** for
hypothetical sites. Existing-site records run from December 31, 1996 at 19:00
through January 1, 2012 at 18:00; hypothetical records run from January 1, 1997
at 00:00 through December 31, 2011 at 23:00. Source boundaries are preserved.

Numeric site IDs, separate calendar columns, AWS names, annual energy and
capacity factors, and raw hypothetical summaries remain typed. The generic
`Sum` field is preserved without inferring its unit. Empty sheets and formatting
rows are ignored. [Comparison receipts](../tools/inputs/generation-profiles/legacy-workbooks/evidence.json)
record original URLs, hashes, reader versions and scope. Regression tests use
clearly labelled source-cell excerpts; the two original workbooks, each over
100 MB, are kept out of the repository and installed package.

Remaining profile formats include the earliest solar shapes, whose columns
include weather years and `TMY3`.
Those solar shapes require separate treatment of units and non-calendar-year
values. Fifteen of the nineteen newer profile workbooks remain unverified.


### Backfill startup on real-time settlement prices

Unbounded `backfill()` streams bundles before requesting the archive listing,
then pages through uncovered archives. Publication-bounded reads still select
archive IDs first. Both paths retain document-ID deduplication and distinct
corrections; row order remains source order.

A live NP6-905-CD check returned the first 1,000 rows after one bundle-listing
request and one bundle download, with **zero archive requests**. All seven
fields matched an independent CSV parser of the downloaded source. The first
row arrived in 11.757 seconds in that run; this is an observation, not a latency
guarantee. The [receipt](../tools/inputs/history/backfill-first-rows-evidence.json)
records the source and decoder hashes and request paths. This startup check
does not establish complete real-time price history coverage.


## Public peak-demand forecast scenarios

`Client.peak_demand_forecasts` covers all **11 XLS/XLSX peak-demand scenario
workbooks** linked from the live [load forecast index](https://www.ercot.com/gridinfo/load/forecast)
and its annual pages at the September 8, 2026 check. The 155 forecast-year rows
include **2,276 weather-scenario MW values**, **286 summary values** and **150
unlabelled auxiliary values**. Target years span 2014–2033 and weather scenarios
span 2002–2023 across vintages; these are not issue-date or actual-load bounds.

Regression tests compare complete original workbook tables using separately
recorded source row coordinates, including every numeric cell on forecast rows.
They cover old XLS headers and P50/P90 labels, gross/net/rooftop-PV blocks,
2024 large-load summaries and the 2025 TSP/adjusted sheets. The 2023 rooftop-PV
table starts at source year 2022 despite the gross/net tables starting at 2023;
that difference is retained. Its unlabelled auxiliary cells have source-column
keys without invented units. Excel's Compatibility Report is not forecast data.

[Source manifests and receipts](../tools/inputs/peak-forecasts/evidence.json)
record the comparison scope. All 11 unchanged original workbooks (268,611 bytes
before fixture compression) and captured index pages are retained under
`tools/inputs/peak-forecasts/` for offline tests and excluded from the wheel.
Source URLs distinguish identically named files in different publication paths.
Monthly, seasonal and weekly peak workbooks use separate readers below.
The main hourly long-term forecast workbooks and regional weather-year scenarios
are covered below; performance workbooks remain a known coverage gap.


## Public monthly peak-demand and energy forecasts

`Client.monthly_load_forecasts` discovers all **11 linked monthly XLS/XLSX
workbooks** from the public forecast index and its annual pages at the September
8, 2026 check. The reader returns **1,705 source rows and 3,408 numeric peak/energy
values**, with source target years spanning 2014–2044 across publications.
These bounds are not actual-load dates or publication/retention dates.

Tests compare every year/month/peak/energy cell using independently recorded
source coordinates in complete original workbooks. They retain both side-by-side
2025 scenarios: 240 ERCOT-adjusted rows and 241 TSP rows. The first TSP value pair
has no date, and the final December 2044 pair has blank values. The source's
apparent date/value offset is not repaired. All 481 rows in this workbook keep
unknown units because its column headings omit units. Earlier explicit MW/MWh
labels are represented in the unit fields. The 2024 large-load/4CP assumption
note remains available with each row.

[Comparison evidence](../tools/inputs/monthly-forecasts/evidence.json) and source
manifests accompany the 11 unchanged original files (264,087 bytes before fixture
compression). Tests reuse the peak-forecast index captures and verify discovery,
source-file predicates and both readers after their shared discovery refactor.
These fixtures are excluded from the installed wheel.


## Seasonal and weekly weather-zone peak tables

The September 8, 2026 live discovery matched **22 seasonal workbooks and two
weekly workbooks** in the [public load-forecast indexes](https://www.ercot.com/gridinfo/load/forecast).
Complete original-source comparisons cover **615 seasonal rows / 5,535 peak
values**, including 352 forecast and 263 historical rows, plus **263 weekly
forecast rows / 2,367 peak values**. Values include eight weather zones and the
independently published total. Counts retain overlapping source publications.

Historical year labels span 2002–2022 across vintages; seasonal target periods
span 2014–2033. Weekly begin dates span August 18, 2024–August 8, 2027 and their
end dates extend through August 14, 2027. These are source period labels, not
publication dates or evidence of uninterrupted unique observations.

Tests address every source date/year/period/hour and zone/total cell using
recorded table coordinates. They cover regional column reordering, historical
sections with misleading `Forecast Year` headers, separate gross/net/PV blocks,
parallel coincident/non-coincident tables, TSP/adjusted scenarios and winter
periods. Live download-title percentile labels are applied before filtering,
including the 2022 P90 workbook that omits that label inside the tables; saved
workbook reads leave such a percentile unknown. Historical rows retain no
forecast percentile. Original numeric totals and declared units are preserved.

[Evidence and manifests](../tools/inputs/zonal-peaks/evidence.json) accompany
24 unchanged original workbooks (560,216 bytes before fixture compression).
Tests reuse the existing forecast-index captures. Fixtures remain outside the
installed wheel. Hourly forecasts and forecast-performance workbooks remain
separate implementation gaps.

## Public hourly long-term load forecasts

`Client.hourly_load_forecasts` discovers the six main hourly forecast workbooks
on the public forecast index and its annual pages at the September 8, 2026 check.
Complete original-source comparisons cover **701,294 rows and 32,084,130 numeric
load-component values**:

| Publication | Source target dates | Rows | Numeric values |
| --- | --- | ---: | ---: |
| 2021 | 2021-01-01–2030-12-31 | 87,648 | 788,832 |
| 2022 | 2022-01-01–2031-12-31 | 87,664 | 2,366,640 |
| 2023 | 2023-01-01–2032-12-31 | 87,670 | 2,366,874 |
| 2024 | 2024-01-01–2033-12-31 | 87,672 | 5,874,024 |
| 2025 TSP provided | 2025-01-01–2044-12-31 | 175,320 | 10,168,560 |
| 2025 ERCOT adjusted | 2025-01-01–2044-12-31 | 175,320 | 10,519,200 |

These are overlapping planning vintages, not counts or bounds of actual demand.
All eight weather zones and published ERCOT totals have concrete typed fields.
Gross/base/net load, rooftop PV, EVs, flexible loads, contracts and officer-letter
loads remain separate. The 2024 flexible-load contract/officer-letter columns
are also distinct from the corresponding general load additions. Missing totals
and regions remain `None`, and negative source PV values are retained.

The originals contain 33 differences between the separate Date column and the
year/month/day columns, plus repeated hour labels and 23-/25-row dates.
`forecastDate` follows year/month/day; `sourceDate` keeps the separate Date value.
No hours are inserted, removed or timezone-adjusted. The 2022 workbook has
87,664 rows and the 2023 workbook has 87,670, despite different calendar lengths;
neither is reshaped to a conventional hourly grid. Formatted trailing blank rows
in the 2024 sheet are not data. The 2023 merged MW header establishes units for
all its numeric columns; the other five workbooks omit that explicit unit label.

Calamine is an optional `files` dependency, used locally by this reader for XLSX
and XLSB. Independent complete comparisons used openpyxl and pyxlsb respectively.
Offline tests use original row excerpts, retained binary/XML cell records,
independently extracted expected values, and the existing public index snapshots.
[Evidence and source manifests](../tools/inputs/hourly-forecasts/evidence.json)
distinguish full-source verification from the smaller offline fixtures. Fixtures
are excluded from the installed wheel.

The eight separate weather-year regional scenario files are covered below. The
winter reliability-standard forecast and forecast-performance families remain
additional gaps.

## Regional hourly weather-year scenarios

`Client.hourly_load_scenarios` discovers all eight files in the public
[2025 weather-year forecast index](https://www.ercot.com/gridinfo/load/forecast/2025).
The September 8, 2026 complete-source check covers **771,233 regional
hourly rows**, **34,704,958 numeric weather-year predictions**
and **3,566,972 numeric adjustment values**. Every source hour
has 45 labelled predictions for historical weather years 1980–2024. Forecast
dates span 2025-01-01 through 2035-12-31; these are scenario target dates, not
observed loads from the historical weather years.

| Region | Source hourly rows | Repeated hour labels |
| --- | ---: | ---: |
| Coast | 96,408 | 11 |
| East | 96,397 | 0 |
| Far West | 96,408 | 11 |
| North Central | 96,408 | 11 |
| North | 96,408 | 11 |
| South Central | 96,408 | 11 |
| South | 96,398 | 11 |
| West | 96,398 | 11 |

Calendar fields follow named columns, including North's Day/Hour/year/month/date
order. South and West have no separate Date column. South Central has no wzone
column, so its worksheet supplies the source zone; it also puts PV before EV.
West also contains 515 blank prediction cells, returned as None without a marker.
East, South and West publish no flexible-load adjustment column. Missing
components remain None, and the source EV/PV/flexible/contract/officer-letter
adjustments are preserved separately from each prediction.

South contains seven `#REF!` errors and five literal dot markers in `Pred_2017`.
For example, source row 27984 contains `#REF!`
(2028-03-12 hour 3). The typed numeric value is None, with that error label
in `sourceMarkers`; a blank value has no error marker. This real source cell
and all eleven other marker rows are retained in a regression fixture. The reader uses the shared streaming
XLSX reader, which preserves spreadsheet errors. Units are unlabelled in these
workbooks, and no timezone, DST flag or net-demand interpretation is inferred.

All numeric cells, clock values, errors, zone labels and original row positions
were compared against original worksheets using separately specified source
coordinates. The smaller offline fixtures retain original XML row excerpts,
with expected cells captured separately. [Evidence and manifests](../tools/inputs/load-scenarios/evidence.json)
distinguish these two verification scopes. Fixtures are excluded from the wheel.

## Separate ESR API

`ESRClient` adds the generated `rptesr_m._4_sec_esr_charging_mw` query, its sync
and async iterators, and `_4_sec_esr_charging_mw_history`. The September 8, 2026
service inventory contains eight operations: one row query and seven shared
metadata/listing/download operations. These are additional to the 242 Public
Reports queries, 249 Public Reports operations, and 289 Public Reports history
tables. The offline generator reads normalized ESR operations, live response
fields and the CSV mapping under `tools/inputs/esr`.

The service reported 4,087,281 query rows, 54,490 archive documents and zero
bundles. The oldest and newest query rows observed were May 29, 2025 20:20:00
and December 4, 2025 23:54:58 CPT; the oldest/newest archive postings were
May 29, 2025 20:27:53 and December 4, 2025 23:55:10. These are observed bounds,
not uninterrupted coverage or current operational freshness. Product metadata's
`lastPostDatetime` is later than the newest returned archive and is not used to
claim a later data boundary.

The complete oldest, middle and newest archived CSV samples contain 225 rows.
All five fields match independent CSV parsing, live paginated typed queries,
archive downloads and bounded publications. Live sync/async paging and all 13
query parameters were exercised. CSV `N` flags decode to false; local and UTC
timestamps retain their separate source values, without inferred timezone
offsets. The original nested ZIPs and API fixtures are used in regression tests.
The shared transport normalizes ESR metadata identifiers through aliases while
selecting the ESR base URL and separate subscription key. No bundles were
available to verify a live bundle download, and intervening archives have not
all been compared. [Verification receipt](../tools/inputs/esr/evidence.json).

## Hourly forecast-performance workbooks

`Client.load_forecast_performance` discovers all 48 currently linked hourly
metric workbooks from the load-forecast index and its annual pages. The two
2026 files have misleading Backcast link titles, so discovery also checks their
actual Metrics filenames. The separate monthly Forecast/Backcast workbooks
are not claimed by this reader.

Complete source-cell comparisons cover **316,123 hourly/calculation rows**,
**21,150 summary rows**, and **4,412,079 numeric values** in the 48 original
files (73,656,757 bytes). Of the hourly/calculation rows, 315,668 have a timestamp;
source timestamps range from February 1, 2022 01:00 through March 1, 2026 00:00.
These are source records, not unique observations or proof of uninterrupted
history. ERCOT and all eight weather zones retain their separate series.

The hourly reader preserves original actual/selected/model-code values and
published errors. Summaries distinguish average errors, frequency counts and
monthly MAPE, including the older layout's vertically stacked chart tables.
Duplicate pivot/helper tables are not added as extra market observations.
Six regression fixtures retain original sample and error cells from both
layouts, including the December 2023 negative/fractional Hour values and
calculation-only tails. Source Hour numbers remain `sourceHour`; valid whole
1–24 values additionally populate `hour`. Missing actuals remain missing.

The 924 preserved markers include Excel errors such as `#DIV/0!` and
zero/time-only secondary clocks. Timestamps, row locations and publication-file
identity remain separate from summary buckets; no issuance time or timezone is
inferred. All values retain their published scale. The November 2025 source's
hourly MAPE formula multiplies absolute relative error by 100, and its Monthly
cell averages that MAPE column; the reader preserves cached values rather than
recomputing them. [Complete comparison receipt](../tools/inputs/forecast-performance/evidence.json)
and [regression source coordinates](../tools/inputs/forecast-performance/samples.json).

## Monthly forecast-performance tables

`Client.monthly_forecast_performance` reads all 15 linked monthly Forecast/Backcast
workbooks. Live discovery matches the captured index, and fresh downloads of
all 15 originals match the committed fixture hashes byte for byte. The two
hourly Metrics files misleadingly linked as Backcast are handled by the
separate hourly reader.

Every monthly table cell was compared across the complete originals:
**3,330 records**, including **3,255 numeric values** and 75 blank future
values. Each file contains 125 forecast/target records, 72 year/month Backcast
records and 25 rolling Day-Ahead Backcast records. Source month labels span
January 2020–December 2026; the latest nonempty month is August 2026. Those
counts include overlapping tables and publication vintages, not unique months.

The 2,250 explicitly percentage-formatted values support a typed `percent`
conversion. Unlabelled Backcast scales remain raw `value` numbers with
`percent=None`. Original Excel date days, formats, source series, notes and
coordinates are retained. Calendar months are normalized separately, and
Goal/Stretch targets are distinct from forecast/backcast errors.

The complete source fixtures total 522,853 bytes before outer ZIP compression.
Tests compare all monthly values, labels, date pairs and number formats, plus
discovery, source metadata, scale handling and blank future values. Charts,
external chart references, an empty Average label, and two unlabelled diagnostic
error cells outside the monthly tables are not interpreted as additional
observations. [Verification receipt](../tools/inputs/monthly-performance/evidence.json).


### Anonymous dated market displays

Five HTML routes now have typed `client.dashboards` methods: `dam_spp`,
`real_time_spp`, `dam_mcpc`, `actual_loads_of_forecast_zones` and
`actual_loads_of_weather_zones`. Optional operating dates select ERCOT's
`YYYYMMDD_` URLs. Headers determine the finite typed series keys; values remain
Decimals, and operating days must agree with both the requested day and the
page heading. Literal period labels retain leading zeroes and repeated-hour
markers. No display time is assigned an inferred UTC offset.

Fixtures preserve 23 complete original HTML responses. All table cells are
compared independently in tests. Live dated comparisons verified 6,268 numeric
values across 13 nonempty displays plus two DAM responses correctly rejected
for a different day and missing market table. This includes 100/92 RT intervals
and 25/23 load hours on fall-back/spring-forward days. DAM spring-forward files
contain 23 hours. Both November 2025 DAM URLs instead returned an unavailable
market message for November 3; no coverage is claimed for those missing prices.
Three older sampled dates (2010-12-01, 2014-05-01, 2020-01-01) returned 404 for
all five routes. These observations establish neither earliest retention nor
continuous coverage. See `tools/inputs/market-displays/evidence.json`.


### Demand dashboard before day-ahead publication

The September 8, 2026 afternoon `system-wide-demand.json` response omitted
`dayAheadForecast` and `dayAheadHsl` from all 24 next-day hours. These values
are now optional typed decimals. The rest of the response remains available,
including the current day's actual load and next day's current load forecast.
Original pre-publication and published-response regression fixtures compare all
five demand/capacity series, clocks and flags. The 217 chart points in the current
and previous-day Load Forecast vs. Actual HTML matched the existing typed JSON
series after rounding to whole MW (ties to even). This checks those two snapshots,
not historical publication timing. See `tools/inputs/dashboards/demand-availability-evidence.json`.

The combined wind/solar dashboard has the same publication boundary: all six
next-day day-ahead fields were explicitly null in 24 rows (144 values). Their
types now admit `None`; full original pre-publication and published captures
verify that current forecasts and observed zero generation remain intact.


### Unavailable public LMP changes

A September 8, 2026 public LMP snapshot contained `-` in the five-minute LMP
change column for APPALOSA_ALL, HB_NORTH and MIDP_SLR_RN. `lmpChange` now admits
`None` for this marker, so all 1,123 settlement-point rows remain accessible.
Prices and the changes including adders remain exactly as published. The complete
original HTML is compressed in the regression fixture; every displayed field is
compared, with separate cases for negative changes, zero and unrecognized text.
