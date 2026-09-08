# Usage reference

A small, fully typed ERCOT market-data client for retailers, battery operators,
and energy traders.

**Development status:** all 242 Public Reports endpoints have typed methods and captured-response tests. The separate ESR API is awaiting an enabled subscription key. MIS is not included.

The live inventory check matched all 249 published HTTP operations: 242 generated
report queries and seven shared operations. All 5,973 query-parameter definitions
matched the saved inputs, and all four generated query variants expose the
expected named parameters and types. The live catalog lists the same 242 report
paths. See `tools/inputs/live-inventory-evidence.json` for the check date and
scope; endpoint coverage does not establish every historical file layout.

The SDK focuses on operational and market time series: prices and settlements,
ancillary services, load and generation, forecasts, outages, constraints, offers,
and awards. Typed archive and monthly-bundle readers support historical analysis.
Direct public load, retail load-profile and fuel-mix files extend the available time series. Planning
studies and document-specific summary extraction are outside the release scope.

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

Runnable [market-data examples](../examples/README.md) export a day of settlement
prices, ancillary-service prices and actual load, or historical forecasts with
original publication metadata:

```sh
uv run python -m examples.market_day 2026-09-01 --point HB_HOUSTON --output market-data
uv run python -m examples.forecast_vintages 2019-01-01T00:30 2019-01-01T00:30 --output forecast-vintages.jsonl
```

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
listings, rechecked in the release audit. The examples and source evidence below
describe the verified historical formats and periods; they do not establish
gap-free coverage of every retained publication.

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

For long backfills, combine monthly bundles with individual archives:

```python
with Client() as ercot:
    for price in ercot.np4_190_cd.dam_stlmnt_pnt_prices_history.backfill(
        posted_from=datetime(2018, 1, 1),
        posted_to=datetime(2018, 12, 31, 23, 59, 59),
        where=lambda price: price.settlementPoint == "HB_HOUSTON",
        batch_size=25,
    ):
        print(price.deliveryDate, price.settlementPointPrice)
```

`backfill()` uses original document IDs inside bundles to avoid downloading the
same publication again, then fetches uncovered archive IDs. Distinct correction
IDs and repeated rows within a report remain intact; output is not sorted.
It holds listing IDs in memory and processes bundle members one at a time.

Shared disclosure reports can gain or lose tables over time. `backfill()` skips
reports where the requested named table is absent but other CSV tables are
present. It does not infer an introduction date. Empty ZIPs, non-CSV downloads,
and errors inside selected tables still raise. Explicit `read()` and `download()`
remain strict when their requested table is missing.

With publication bounds, the archive listing selects the original reports;
bundle timestamps only help choose candidate months. Reports missed by those
bundles are still fetched from archives. Omit both bounds to include all listed
archives **and bundle-only reports**, whose original posting metadata may no
longer be available. Use `where` to filter their typed row dates. Unknown bundle
member identities and unreadable selected data raise rather than silently omit
history; `rows()` and `rows(kind="bundle")` remain available for separate sources.

For forecast backtests, keep the publication metadata alongside the typed rows:

```python
with Client() as ercot:
    forecasts = ercot.np3_561_cd._7d_load_fcast_by_wzn_history
    for publication in forecasts.publications(
        posted_from=datetime(2019, 1, 1),
        posted_to=datetime(2019, 1, 1, 6),
    ):
        posted_at = publication.document.postDatetime
        for forecast in publication.rows:
            print(posted_at, forecast.deliveryDate, forecast.systemTotal)
```

`publications()` yields `Publication[Row]`: the original typed `Document`, its
`kind`, and a lazy iterator of typed `rows`. Listing alone does not download the
payload; consume rows while the client is open. Separate publications keep their
identities even when their row values match. This also works for workbook/PDF
history readers and with `kind="bundle"`. A bundle's posting time describes the
bundle, **not** when its component forecasts were available. Embedded row fields
remain unchanged: older forecast CSVs omit `postedDatetime`, so that field stays
`None` while archive publication metadata is available separately.

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
`tools/inputs/history/bundle-evidence.json`. Neither listing alone proves continuous
coverage. All 62 sampled January 2018 price/load bundle members carried the same
original document IDs as their archive listings, and their complete per-report
payload bytes matched. `backfill()` uses those IDs to combine sources. Filename
timestamps differ from the listed posting times in 28 of these reports and are
not used as publication keys. Live January 2018 backfills returned all 473,256
DAM price rows and 744 load rows, matching the recorded archive row multisets
with zero individual archive downloads. If both bundle download routes fail, the
error propagates. Unsupported CSV layouts raise with the member name instead of silently
dropping data.

The September 2026 live listing audit found these earliest archive posting dates
for key market products (these are publication boundaries, not proof of continuous
row coverage):

| Data | Earliest archive posting |
| --- | --- |
| DAM/RT settlement prices, DAM AS prices, actual load, wind, SCED constraints, hourly outage capacity | May 1, 2014 |
| Solar actual/forecast | February 10, 2016 |
| Weather-zone load forecasts | January 1, 2019 |
| Unplanned resource outages | December 7, 2022 |
| RT AS prices by settlement/SCED interval and indicative RT AS prices | December 5, 2025 |

A full retained actual-load backfill (NP6-345-CD) returned **108,285 rows** from
all 4,512 listed archive publications, combining 102 bundles with two archive
batches. Every field matched an independent CSV comparison. Operating dates
span April 30, 2014–September 6, 2026, with December 4, 2025 absent from both the
files and the report query. Three older dates also lack hour ending 24:00:
November 4, 2014; August 4, 2015; and March 15, 2016. These source gaps remain
explicit; rows are not synthesized. See `tools/inputs/history/bundle-evidence.json`
for the full-source check and adjacent-day query controls.

A full DAM ancillary-price backfill (NP4-188-CD) returned **461,736 rows** from
all 4,513 retained publications, spanning May 2, 2014–September 8, 2026. Every
field matched independent CSV parsing. Each service had continuous dates and
the expected daily count of unique hour/DST pairs within its observed range;
ECRS first appeared on June 10, 2023. The full-source check is also recorded in
`tools/inputs/history/bundle-evidence.json`.

A full DAM settlement-price backfill (NP4-190-CD) matched **81,236,426 rows**
across 1,230 settlement points, spanning May 2, 2014–September 8, 2026. It included
all 4,513 listed archives and one additional publication found only in a monthly
bundle. Every field matched independent CSV parsing. No delivery dates were
missing across the product; each observed point/publication had the expected
number of unique hour/DST pairs. This does not imply that each point existed
throughout the range. The full-source receipt and decoder version are recorded
in `tools/inputs/history/bundle-evidence.json`.

Weather-zone load forecasts had only five listed bundles, starting March 2026,
despite archives extending to 2019. Archive access therefore matters for complete
backfills. The oldest retrieved load-forecast publication contained 192 rows and
no embedded posting timestamps; `publications()` preserves its January 1, 2019
00:30 archive timestamp separately. Counts, original listing entries and the live
forecast check are recorded in `tools/inputs/history/market-availability.json`.

Listing metadata includes the server's total and page counts; `iter_documents()` streams all listing pages.

ERCOT's separate annual DAM/RTM hub-and-load-zone price products (NP4-180-ER,
NP6-785-ER) and annual DAM ancillary-price product (NP4-181-ER) use MIS download
routes on their current public pages. They are outside this release's **no MIS**
scope; earlier annual price history is not provided by the daily API readers.
The inspected routes are recorded in `tools/inputs/public-market-access-evidence.json`.

### Historical zonal generation and load

The older zonal-market MWh files are available with `tinyercot[files]`:

```python
from datetime import date

with Client() as ercot:
    for day in ercot.zonal_energy.rows(
        date_from=date(2004, 1, 1),
        date_to=date(2004, 1, 1),
        where=lambda r: r.kind == "load" and r.zone == "H04",
    ):
        print(day.totalMWh, day.intervals[0].energyMWh)
```

`files()`, `download(file)` and `read(data, filename=..., kind=..., where=...)`
support saved workbooks; bare unnamed files require `kind="load"` or
`kind="generation"`. `totals()` and `read_totals()` return the published summary
and detail totals separately, preserving their cached differences and shares.

All ten 2001–2005 originals yield **13,886 zone/day records** and **88 totals**.
2001 generation starts July 31, load August 1; 2005 generation is missing
June 22–July 28 in all five zones. Original zone codes remain unchanged and are
not mapped onto today's market. Numbered/clock interval labels have no inferred
UTC offset; extended load rows retain all 100 values with unknown clock labels.
`sourceNumbers` preserves numeric cells whose source headers do not establish
their meaning, including extra generation numbers and a mislabeled `ORIGIN`
column. These are kept separate from `energyMWh`. Totals are not reconciled,
missing dates are not filled, and source timestamps are not publication times.

### Historical four-coincident-peak allocations

Annual 4CP allocations are available without credentials through
`coincident_peaks`, using the optional `tinyercot[files]` dependencies:

```python
from tinyercot import Client

with Client() as ercot:
    for allocation in ercot.coincident_peaks.allocations(
        year_from=2020,
        year_to=2020,
        entity="AEP TEXAS CENTRAL COMPANY (TDSP)",
    ):
        print(allocation.averageLoad, allocation.unit, allocation.loadRatioShare)
        for peak in allocation.peaks:
            print(peak.month, peak.timestamp, peak.load)
```

`download()` returns the original 1996–2020 ZIP; `read_allocations(data)` accepts
saved ZIPs and workbooks with the same inclusive year and exact entity filters.
The annual reader covers 4,345 rows across all 25 years. Revisions remain separate;
`kind` distinguishes allocations, comparison tables and revision details. Source
member, worksheet, section and notes retain their context. DUNS identifiers stay
strings, including leading zeros. Loads retain their published kW/MW units, and
`adjustmentUnit` distinguishes factors from percentages. Missing peak clocks
remain `None`; the 1997 annual summary provides an average without monthly peak
columns, so its `peaks` list is empty.

`monthly(date_from=..., date_to=..., entity=...)` and `read_monthly(data, ...)`
return typed monthly peak records, using inclusive **peak dates**. They cover
7,633 records in 86 submitted/preliminary/settled tables from 1997–2007 within
the same archive. `loadType` identifies submitted load, coincident-peak load or
load responsibility; `unit` applies to `load`, and `energyMWh` remains separate.
Revisions, loss components and report differences are retained. Total rows remain
present, including three unlabeled source totals with `entity=None`.
`settlementRun` retains the published date, optional time, stage and channel;
an invalid source date stays visible in `sourceDate` with `runDate=None`.
Member, sheet, one-based source row, headings and notes provide provenance.

Daily 4CP source energy is also available:

```python
from datetime import date

with Client() as ercot:
    for day in ercot.coincident_peaks.daily(
        date_from=date(2017, 6, 1),
        date_to=date(2017, 6, 1),
        where=lambda r: r.entity == "ERCOT" and r.settlement == "FINAL",
    ):
        print(day.operatingDay, day.intervals[0].energyMWh)
```

`daily_files()` discovers public source workbooks; `download(file)` and
`read_daily(data, filename=..., date_from=..., date_to=..., where=...)` support
saved copies. The published 2017 workbook covers June–September, with **32,890
entity/day records** across initial and final settlement sheets. Both versions,
source channels and interval labels remain separate. These values are **MWh**;
no peak MW, allocation share or UTC timestamp is inferred. One entity has 97 of
the 122 dates in each sheet; missing dates are not filled. Source row, file link
and units remain attached. The tables include both ERCOT and individual entities,
so adding every row together would double-count energy.

Recent 4CP publications use MIS routes and remain outside this release's scope. See
`tools/inputs/public-four-cp-evidence.json` for source comparisons and limitations.

### Historical retail load profiles

`load_profiles` discovers ERCOT's annual backcasted load-profile files, currently
labelled 1997–2026. Install `tinyercot[files]`; API credentials are unnecessary.

```python
from datetime import date
from tinyercot import Client

with Client(timeout=120) as ercot:
    for day in ercot.load_profiles.rows(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 2),
        profile="BUSHIDG_COAST",
    ):
        print(day.operatingDay, day.profileType, day.weatherZone)
        for interval in day.intervals:
            print(interval.interval, interval.energyKWh)
```

Omit `profile` for all profile types and weather zones. `archives()` discovers
actual links, `download(archive)` returns the original ZIP, and `read(data)`
decodes saved ZIPs or workbooks with the same date/profile filters. Each daily
row retains every numbered interval column, including unused blank cells
(100 columns in annual backcasts; 96 in the original Hurricane Ike profiles).
These are modeled settlement profiles using observed weather, not individual
meter readings. No wall-clock timestamp is inferred from the interval number.
The 2007 auxiliary and 2008 pre-adjustment profiles remain separate through
`kind="auxiliary"` and `kind="original"`; original member and sheet names are
retained. `adjustments(date_from=..., date_to=...)` and `read_adjustments(data)`
return the Hurricane Ike factors separately, without applying them to kWh.
`sourceAddTime` preserves optional `ADDTIME` values,
without treating them as proof of public availability for backtesting.

The complete 2026 file contains 248 profiles and 52,328 profile-days through
August 30; May is absent from the workbook. These source gaps remain visible.
Format coverage and original-file comparisons are recorded in
`tools/inputs/public-load-profiles-evidence.json`.

Profile-assignment counts are available from the same service:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for count in ercot.load_profiles.counts(
        date_from=date(2026, 8, 6),
        where=lambda row: row.weatherZone == "COAST" and row.profileType == "BUSHILF",
    ):
        print(count.snapshotDate, count.tdsp, count.meterDataType, count.records)
```

`read_counts(data, filename=...)` accepts saved ZIPs or workbooks with the same
filters. These are assignment counts by profile, weather zone, meter type and
TDSP, separate from energy profiles. The direct archive contains 141 snapshots
and 97,924 records, with valid filename dates spanning April 2013–August 2026.
Original and corrected snapshots remain separate. `snapshotDate` is a filename
label, not proof of public availability. Two malformed date labels remain in
`sourceDateLabel` with `snapshotDate=None`: unbounded reads include them, while
date bounds exclude them. Five records retain an unknown weather zone as `None`.

### Historical settlement loss factors

`loss_factors` reads the directly published actual/forecast transmission and
distribution loss-factor workbooks with `tinyercot[files]`, without credentials:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for day in ercot.loss_factors.rows(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
        where=lambda r: r.kind == "actual" and r.level == "distribution",
    ):
        print(day.operatingDay, day.tdsp, day.lossCode, day.intervals[0].factor)
```

`archives()` discovers files on the current page and all linked annual indexes;
`download(archive)` returns the original workbook or ZIP. `read(data,
filename=..., source_file=archive, ...)` accepts saved files with the same
inclusive operating-date bounds and typed `where` filter. Overlapping files
and sheets remain separate.

The 72 inspected downloads contain **301,829 series/day records** and **28,975,512
numeric factors**, with source dates from July 31, 2001 through July 31, 2026.
Coverage varies by series: actual distribution factors begin December 7, 2006.
See the [per-file coverage manifest](../tools/inputs/public-loss-history-sources.csv)
for actual ranges; year and sheet labels do not guarantee a complete year.

Interval positions preserve every value and blank, including repeated clocks
on fall-back days. `sourceLabel` holds the legacy clock label or modern `INTV`
column name. One 2013 row has 100 values under a 96-interval header: all values
and its trailing timestamp survive, with interval labels set to `None`.
Factors keep their original scale and are never applied to load implicitly.

`sourceFile` retains the index link and title when supplied. Early distribution
workbooks do not contain an actual/forecast label: live queries use the index's
label, while saved reads without that metadata return `kind=None`. Recorder IDs,
TDSPs and loss codes remain distinct; unlabeled secondary identifiers and markers
are retained separately. No TDSP is inferred from a recorder ID. Source timestamps
have no inferred timezone and do not establish public availability. MIS feeds
remain outside this client's scope.

### Distribution-loss coefficients

Read the published retail distribution-loss parameters with `tinyercot[files]`:

```python
with Client() as ercot:
    for coefficient in ercot.distribution_loss_coefficients.rows(
        where=lambda r: r.year == 2026 and r.tdsp == "Oncor",
    ):
        print(coefficient.lossCode, coefficient.f1, coefficient.f2, coefficient.f3)
```

`files()`, `download(file)` and `read(data, filename=..., where=...)` also support
saved summaries and original ZIPs. The 28 summaries for **2001–2026** contain
**466 records**, including both period variants in 2007 and 2024. Older summaries
use separate `tdspAverageIntervalLoadMWh`, `kFactor` and
`annualDistributionLossFactor` fields; `formula` identifies the family.

The filename `year`, original title and load-baseline dates remain distinct.
They do not establish coefficient effective dates or publication timestamps.
Cached values retain their original scale and rounding. Original formula text
and source identity accompany every record; example curves are not observations.
The files extra handles the historical XLS summaries' built-in workbook protection.

### Seasonal loss coefficients and operator load shares

Annual transmission-loss coefficients are available through the same client:

```python
with Client() as ercot:
    for coefficient in ercot.transmission_loss_coefficients.rows(
        where=lambda r: r.year == 2026 and r.area == "ERCOT",
    ):
        print(
            coefficient.season,
            coefficient.slopePercentPerMW,
            coefficient.interceptPercent,
        )

    for share in ercot.load_shed.rows(where=lambda r: r.season == "winter"):
        print(share.transmissionOperator, share.loadSharePercent, share.effectiveFrom)
```

Both services expose `files()`, `download(file)` and `read(data, filename=...,
where=...)` for saved workbooks or ZIPs; parsing uses `tinyercot[files]`.
Coefficient discovery follows all 26 current/annual indexes and returns **948
area/season records for 2001–2026**. The published SSC/SIC values produce percent
loss; the separate on/off-peak load inputs are MW and their loss factors retain
the original fractional scale. Source correction labels remain distinct.
`asOf` comes from the workbook heading and is not a publication timestamp.

Missing coefficients remain `None`. Early files omit effective periods; the
2020 and 2026 winter ranges are reversed in the originals. Their usable date
bounds remain `None`, with the original text in `sourceEffectivePeriod`.
`source_file=file` can attach the original coefficient index link to saved reads;
live reads attach it automatically. Revisions remain separate.

The two current load-shed tables contain **21 operator load percentages each**,
effective April 1 and September 1, 2026. These are load shares, not shed MW or
outage probabilities. The reader keeps the original notes and assumes no end
date: ERCOT says each table remains effective until replaced.

### CRR hours and retail counts/energy

The direct public CRR calendar and provider-of-last-resort (POLR) territory
reports use the same small interface, with `tinyercot[files]`:

```python
from tinyercot import Client

with Client() as ercot:
    for month in ercot.crr_hours.rows(where=lambda r: r.month.year == 2026):
        print(month.month, month.peakWDHours, month.peakWEHours, month.offPeakHours)

    for usage in ercot.polr.rows(where=lambda r: r.premiseType == "Residential"):
        print(usage.territory, usage.activeEsiids, usage.energyKWh)
```

`files()` discovers current links, `download(file)` returns original bytes, and
`read(data, filename=..., where=...)` queries saved workbooks or ZIPs. Original
and revised files stay separate. The captured CRR calendar covers 48 delivery
months in 2026–2029; `month` is the first day of the delivery month. Published
hour counts retain DST effects and are not recomputed from calendar assumptions.

The POLR report contains 24 territory/customer-class totals. `snapshotDate`
describes active ESIIDs with usage on March 31, 2026; `energyPeriodStart` and
`energyPeriodEnd` describe all ESIIDs active during April 2025–March 2026.
These populations differ, so `energyKWh / activeEsiids` is not automatically
an annual per-customer usage measure. Dates come from the table headers;
original cover notes remain in `sourceNotes`. These are the observed downloads,
not a claim of older coverage or of realized future trading activity.

### Retail transaction history

`retail_transactions` reads daily transaction counts from the public monthly
archive with `tinyercot[files]`:

```python
from tinyercot import Client

with Client() as ercot:
    for month in ercot.retail_transactions.rows(
        where=lambda r: (
            r.month.year == 2025
            and r.sourceSheet == "ERCOT Inbound"
            and r.transactionCode == "814_01"
        ),
    ):
        for day in month.days:
            print(day.operatingDay, day.count)
```

`files()`, `download(file)` and `read(data, filename=..., where=...)` also support
discovery and saved workbooks/ZIPs. The inspected archive contains 20 months
(January 2025–August 2026), 9,126 monthly transaction/category records and 277,433
daily counts. Queries use the dates in the table, not the archive filename.

`transactionCode=None` identifies a sheet's Grand Total row. Codes and raw sheet
labels remain unchanged, including four sheets with unnamed categories.
Territory, customer-class and ERCOT-wide views overlap; do not sum across those
categories. `reportedTotal` and `reportedAveragePerDay` retain the source's
monthly summaries, including rounded averages. Missing count cells remain
`None`. No transaction-code business meaning or individual customer activity
is inferred from these aggregate counts.

### Interim indicative ORDC prices

`indicative_ordc` exposes ERCOT's direct interim ORDC archive without optional
dependencies. These are indicative results from before ORDC implementation,
with `indicative=True`; they are separate from realized settlement prices.

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for row in ercot.indicative_ordc.rows(
        where=lambda r: r.scedTimestamp.date() == date(2013, 11, 3)
    ):
        print(row.scedTimestamp, row.repeatedHourFlag, row.rtorpa, row.rtoffpa)
```

`files()`, `download(file)` and `read(data, filename=..., where=...)` support
discovery and saved CSVs/ZIPs. All 9,826 records in the direct archive are typed,
spanning October 17–November 19, 2013. The page description says November 20;
the dates above come from the actual files. Original reserve/input abbreviations,
timestamp text, repeat-hour flags and member names are retained. The source's
`00:xx AM` clock parses as midnight, with no inferred timezone. Every SCED row
remains separate; readings are not resampled or combined with settled prices.

### Resource outlooks

`resource_outlook.percentiles()` reads the probabilistic forecast tables in
Monthly Outlook for Resource Adequacy (MORA) workbooks with `tinyercot[files]`:

```python
from datetime import date
from decimal import Decimal
from tinyercot import Client

with Client() as ercot:
    for row in ercot.resource_outlook.percentiles(
        where=lambda r: (
            r.reportMonth == date(2026, 11, 1)
            and r.metric == "gross_demand"
            and r.percentile == Decimal("0.5")
        ),
    ):
        print(row.hour, row.value, row.sourceUnit)
```

`files()` discovers current and archived-year workbook links, `download(file)`
returns the original file, and `read_percentiles(data, filename=..., where=...)`
queries saved workbooks or ZIPs. All 27,500 percentile values in 37 linked
workbooks are supported, covering December 2023–November 2026, with both
December 2023 versions retained.

These are forecast distributions for the assessment month, not realized hourly
observations. `percentile` uses 0–1, normalizing explicit strings such as `50%`
while retaining `sourcePercentile`. `hour=None` identifies daily outage values.
Weather-related outages remain separate from other outages. Only published hours
and metrics are returned; early files have fewer hours. `sourceMetric` retains
changes in demand definitions, and `sourceNotes` retains weather-outage footnotes.
Units are `MW` where stated and `None` for the 22 earliest daily-outage values
whose table headings omit units. Report labels and file identities preserve
revisions, without asserting when they became publicly available. Percentiles
from different quantities should not be added or subtracted as if they were
joint scenarios.

`resource_outlook.resources()` also returns typed resource-detail rows, including
unit capacities, planned projects and capacity summaries:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for row in ercot.resource_outlook.resources(
        where=lambda r: r.reportMonth == date(2026, 11, 1) and r.kind == "unit",
    ):
        print(row.name, row.category, row.installedCapacityMW, row.reportedCapacityMW)
```

Use `read_resources(data, filename=..., where=...)` for saved workbooks or ZIPs.
All 61,949 resource-table rows across the same 37 workbooks are supported.
`kind="summary"` separates totals, capacity contributions and adjustments from
unit rows, including summaries that have a source unit code. Avoid adding summary
rows to their constituent units. Original categories distinguish operational,
planned, mothballed and unavailable resources; an omitted category remains `None`.
`inService` retains a year, date, source error such as `#N/A`, or `None`.

Installed and reported capacities remain separate decimals, with their original
rating labels and explanatory notes. A seasonal rating or planned service date
does not establish available generation; battery fleet contribution is calculated
separately by ERCOT. Missing capacities remain `None`, and negative adjustments
are preserved.

`resource_outlook.capacities()` reads category-level installed and expected
available capacity. For example, to query ERCOT's expected battery contribution:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for row in ercot.resource_outlook.capacities(
        where=lambda r: (
            r.reportMonth == date(2026, 11, 1)
            and r.section == "operational"
            and r.resourcePath[-1] == "Batteries"
        ),
    ):
        for scenario in row.availableCapacity:
            print(scenario.hourEnding, scenario.timeZone, scenario.valueMW)
```

`resourcePath` preserves the category hierarchy; parent and child totals overlap.
Installed capacity appears once on each row, while `availableCapacity` keeps
every published scenario separately. Older reports can have two hours, or two
scenarios at the same hour. `sourceScenario` retains that distinction. The source
clock is a typed `time`, with `timeZone=None` when ERCOT omits CST/CDT.

`resource_outlook.balance()` reads the monthly load/resource balance using 33
typed metric names, such as `average_weather_load`, `storage_capacity`,
`planned_thermal_outages` and `normal_condition_reserves`. Each row's `values`
contains the scenario values in MW. Use typed predicates to select a month or
metric. `read_capacities(data, ...)` reads saved XLSX files/ZIPs and
`read_balance(data, ...)` reads saved workbooks/ZIPs. Together these readers cover
all 4,569 numeric cells in the two tables across the 37 linked workbooks.

These are ERCOT's forecast assumptions and scenario results. Source metric labels
and explanatory notes preserve changes in their definitions; they are distinct
from actual capacity, demand or reserve observations. Embedded risk charts and
image-only probability tables are outside these readers.

### Capacity changes and project history

`capacity_changes` reads the project tables and annual/monthly capacity series
behind ERCOT's Capacity Changes by Fuel Type charts, using `tinyercot[files]`:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for project in ercot.capacity_changes.projects(
        where=lambda p: (
            p.reportMonth == date(2026, 7, 1) and p.sourceSheet == "Battery Chart"
        ),
    ):
        print(project.identifier, project.capacityMW, project.projectedCOD)
```

All 169 linked workbooks are supported: 42,628 project records and 16,554
capacity-series rows, covering every reporting month from August 2018 through
July 2026. `totals()` exposes installed, synchronized, operational and planned
capacity measures as separate typed fields. Source periods span 1999–2033 and
include future projections. Annual points retain an integer year; monthly points
retain their original full date, including dates under a source `Year` heading.

`files()` discovers current and archived-year links; `download(file)` returns the
original bytes. `read_projects(data, filename=..., source_file=..., where=...)`
and `read_totals(...)` query saved workbooks or ZIPs. `source_file` accepts a
`PublicFile` to retain its URL and title; live queries supply it automatically.
Saved reads use member filenames for `reportMonth`, leaving it `None` if unknown.
File names and URLs do not establish point-in-time public availability.

Project identifiers can be INRs or resource codes. Projected CODs, reported years,
agreement dates and synchronization approvals stay separate. Original status
strings, missing fields, small-generator groups, comments and corrections remain
visible. Companion reports and revisions are retained, including different URLs
with the same filename. Neither file variant nor a projected service date implies
that a project is commercially operating. Missing capacities remain `None`,
distinct from zero; `sourceColumns` records which measures were published.

### Historical IDR compliance summaries

`idr_compliance` exposes the public historical market/TDSP summary tables with
`tinyercot[files]`, without API credentials:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for row in ercot.idr_compliance.rows(
        date_from=date(2008, 7, 8), date_to=date(2008, 7, 8), entity="Market"
    ):
        print(row.operatingDay, row.reportRunDate, row.compliance, row.status)
```

`archives()` discovers the annual filing links; `download(archive)` returns the
original ZIP; `read(data, filename=..., ...)` decodes saved ZIPs or workbooks.
Bounds are inclusive operating dates. Every archive is considered because filings
can report much earlier dates. Repeated report vintages and original entity labels
remain separate. The seven published archives contain 894,851 dated records,
with operating dates spanning January 2002–September 2008.

`compliance` retains the source numeric scale. Excel errors and text such as
`Not MRE For Date` remain in `status`, with `compliance=None`. Zero-date template
rows filled entirely with `#N/A` are skipped. `reportRunDate` is the date printed
in the workbook, not proof of public availability. Source member/sheet names and
the outer archive filename, when supplied, remain attached to each record.

### Historical zonal weather

`historical_weather` reads ERCOT's direct public archive with `tinyercot[files]`:

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for day in ercot.historical_weather.rows(
        date_from=date(2000, 7, 1),
        date_to=date(2000, 7, 2),
        weather_zone="COAST",
        variable="DRYBULB TEMP",
    ):
        for hour in day.hours:
            print(day.operatingDay, hour.hour, hour.value, day.sourceUnit)
```

All eight weather zones and four variables (`CLOUDCOVER`, `WINDSPEED`, `DEWPOINT`,
`DRYBULB TEMP`) are typed. The source combines stations using weights; it contains
1,837 days per zone/variable from January 1, 1996 through January 10, 2001, despite
the archive's “1996–2000” filename. Dates are inclusive; omit filters for all data.
The workbooks do not state measurement units, so `sourceUnit=None` and values
retain their original scale. Hour numbers preserve the source's 24 columns
without assuming an ending time, DST convention or UTC offset.

`download()` returns the original ZIP. `read(data, ...)` accepts saved ZIPs and
workbooks with the same filters; pass the original `filename` for a standalone
workbook so its weather zone can be identified. Source notes and member/sheet
names remain attached to every record.

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
The 2016 workbook has an hour with all nine values missing. The linked 2026 ZIP
has stale directory metadata but an intact workbook. The reader recovers it using
the member's local sizes and checksum: all **5,087 hourly rows through July 31,
2026** and **45,783 load values** matched the source. Checksum failures and
incorrect local sizes still raise. Downloads retain the original bytes. The
index has no 2001 file. See `tools/inputs/public-hourly-load-evidence.json` for
the inventory, source comparison and recovery details.

The annual files and `np6_345_cd.act_sys_load_by_wzn_history` retain different
published values. Across 720 matching January 2018 hours, all 6,480 compared load
cells differed, including after rounding the annual values to two decimals. Keep
the source identified when combining these series; the API data cannot silently
replace a missing annual workbook. The source comparison is recorded in
`tools/inputs/public-hourly-load-evidence.json`.

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
See
`tools/inputs/public-legacy-hourly-load-evidence.json` for the source checks and
EEI format reference.

### Historical generation by fuel

`fuel_mix` reads the public annual settlement workbooks, independently of the
live `dashboards.fuel_mix()` feed. Install `tinyercot[files]` for XLS/XLSX support.

```python
with Client(timeout=180) as ercot:
    for day in ercot.fuel_mix.rows(
        date_from=date(2007, 1, 1), date_to=date(2007, 1, 1)
    ):
        print(day.operatingDay, day.fuel, day.settlementType, day.totalMWh)
        for interval in day.intervals:
            print(interval.ending, interval.dst, interval.energyMWh)

    for total in ercot.fuel_mix.summaries(year_from=2026, year_to=2026):
        print(total.month, total.fuel, total.energy, total.unit)
```

`archives()` discovers the current index links; `download()` returns the original
file. `read(data, filename=...)` and `read_summaries(data, filename=...)` decode
saved XLS/XLSX files or their ZIP archive. Standalone modern summary workbooks
need the original filename to identify the year. Older years share a roughly
51 MB ZIP download; bounded queries skip workbooks for other years after download.

Each daily row retains its original fuel name, settlement status, published total
and ordered interval cells. Midnight ends the operating day. Blank cells remain
`None`, WSL values can be negative, and DST columns retain their labels and
positions. Older `DST1`–`DST4` columns and unlabelled columns have no inferred clock
time. Malformed source values retain `sourceError`. Monthly/annual summaries retain
their own MWh/GWh units and precision, including source month markers such as
`Jan*`; they are not recomputed from daily rows. These settlement values are distinct
from instantaneous dashboard generation in MW. The workbook's chart-support sheets
are not included in these daily and summary table readers.

The September 2026 source check decoded all 20 linked annual workbooks: 62,071
daily fuel rows, 5,984,876 interval cells and 2,386 published totals. Every numeric
value, blank cell and preserved error matched an independent source read. The
2026 file currently ends July 31. See `tools/inputs/public-fuel-mix-evidence.json`.

### Historical generation schedules by zone

The public `zonal_generation` archive contains 889,140 scheduled MW records from
July 31, 2001 through April 11, 2007. It is a fixed historical snapshot, with seven
nested yearly ZIPs. It needs no credentials or optional dependencies.

```python
with Client() as ercot:
    for schedule in ercot.zonal_generation.rows(
        date_from=date(2001, 7, 31), date_to=date(2001, 7, 31)
    ):
        print(schedule.periodEnding, schedule.zoneId, schedule.scheduledMW)

    saved_zip = ercot.zonal_generation.download()
    saved_rows = ercot.zonal_generation.read(saved_zip)
```

`read()` also accepts a yearly ZIP or raw tab-delimited text. Each row retains the
local CPT period-ending timestamp without a UTC offset. Historical zone IDs change
between years and are preserved without assigning modern zone names. Date bounds
refer to `operatingDay`, the date of the 15-minute interval; midnight belongs to
the preceding operating day. August 9, 2001 is missing from the published data.
No intervals are synthesized. These schedules are distinct from actual generation
in the fuel-mix reports. All source timestamps, zone IDs and MW quantities were
compared directly; see `tools/inputs/public-zonal-generation-evidence.json`.

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
SCED capacity, the ancillary-service capacity monitor, and the current locational
price map.

```python
with Client() as ercot:
    capacity = ercot.dashboards.sced_capacity()
    for row in capacity.current.data:
        print(row.timestamp, row.increaseGenResESRs, row.decreaseGenResESRs)

    reserves = ercot.dashboards.ancillary_capacity()
    print(reserves.data.regulationAwardsGroup.regUpAwd)
```

SCED capacity includes current and previous day telemetry. The ancillary monitor
exposes 60 values across 12 named source groups, including battery capacity and
reserve awards. Both are public and require no credentials. Values are in MW;
SCED capacity does not account for individual resource ramp-rate or duration limits.

`ercot.dashboards.real_time_conditions()` reads the public system-conditions table,
including frequency, instantaneous time error, consecutive BAAL exceedances,
demand, capacity, generation, inertia and all five DC ties. Its `lastUpdated`
is a naive datetime because the display provides no UTC offset. This method
returns the current snapshot; it does not provide a historical archive.

`ercot.dashboards.real_time_lmps()` reads the latest public settlement-point table.
Use `hubs_and_zones=True` for the hubs/load-zones display. Each row keeps `LMP`,
`lmpChange`, `lmpWithAdder` and `lmpWithAdderChange` separate; changes are the
published five-minute changes. The snapshot includes `RTRDPA` and the display
update time, which also has no UTC offset. For historical LMPs and adders, use
the generated report-query and `_history` methods.

`ercot.dashboards.indicative_prices("HB_HOUSTON")` returns recent RTD runs for any
of the 15 published hubs/load zones. Each run retains its `RTDTimestamp`, the
display’s `actualLMP` value, and typed `intervals` with `intervalId`, `minutesAhead`
and `LMP`. The interval prices include reliability deployment adders, exposed by
`includesReliabilityAdder=True`. The separate `lastSCEDTimestamp` and run times
remain naive; no absolute interval timestamp is inferred from a minute offset.
For the longer historical record, use `np6_970_cd.rtd_lmp_node_zone_hub_history`.

Detailed field mappings, historical layout changes and source limitations are
recorded in [data coverage](data-coverage.md).

### Conditional MORA risk curves

With `tinyercot[files]`, read the numerical wind/BESS risk curves from MORA:

```python
with Client() as ercot:
    for point in ercot.resource_outlook.risk_points(
        where=lambda r: r.reportMonth.year == 2026 and r.event == "EEA3_load_shed",
    ):
        print(point.windGenerationMW, point.probability, point.bessAvailabilityMW)
```

`read_risk_points(data, filename=..., source_file=..., where=...)` supports saved
workbooks and ZIPs. There are **72 published points** in the June, October and
November 2026 workbooks. Probabilities remain fractions from conditional model
runs with fixed wind and BESS inputs. The original scenario notes accompany each
point. November's chart says 8 p.m. while its scenario says 7 p.m.; both hours
remain separate fields. These are simulated risk curves, not observed outcomes.
Reports with only graphical images return no numeric curve points; the original
reports remain available through `resource_outlook.download(file)`.

## Modeled wind and solar generation profiles

`generation_profiles` reads the hourly CSV and Excel tables published on ERCOT's
[resource adequacy archive pages](https://www.ercot.com/gridinfo/resource/2022).
These are retrospective **planning simulations**, including operational, planned,
hypothetical and distributed generation. A profile dated 1980 does not mean that
plant existed in 1980. Use them for weather and fleet scenarios; they are not
metered generation or forecasts that were available on that historical date.

Select a particular publication before downloading: files can be large and
multiple vintages overlap. Excel parsing uses `tinyercot[files]`.

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    source = next(
        file
        for file in ercot.generation_profiles.files()
        if file.url.endswith(
            "ERCOT-OperationalPlanned-SolarPVProfiles-2020-2021-CST-CDT.xlsx"
        )
    )
    data = ercot.generation_profiles.download(source)
    sites = list(ercot.generation_profiles.sites(data, filename=source.title))
    for hour in ercot.generation_profiles.read(
        data,
        filename=source.title,
        where=lambda row: row.profileDate == date(2020, 7, 1),
    ):
        print(hour.profileDate, hour.timeHHMM, hour.generationMW[sites[0].column])
```

`GenerationProfileHour` supplies a date, the source's HHMM clock and a typed
`dict[str, Decimal | None]` of MW values keyed by the original column labels.
`GenerationProfileSite` exposes embedded site IDs, capacities, county, CDR zone,
common name, plant status and solar tracking system when supplied. Separate key workbooks are not
implicitly joined; identifiers and capacities can change between vintages.

CSV clock strings, including leading zeros, are preserved in `sourceTime`, and
`sourceTimeColumn` preserves `TIME`, `TIME_CST` or the older `HHMM(CST)` label. No UTC offset or hour-ending
interpretation is inferred. Repeated clocks, missing values, overlapping files
and dates outside filename labels survive unchanged. Saved CSVs, workbooks and
ZIPs containing supported tables can be read locally. Unsupported layouts raise;
some older ZIP formats and workbook vintages remain unverified. See the
[coverage evidence](data-coverage.md#modeled-generation-profiles).

The separate keys can be discovered and read with the same service:

```python
with Client() as ercot:
    source = next(
        file
        for file in ercot.generation_profiles.key_files()
        if file.url.endswith("ERCOT-SolarPVProfiles-1980-2021-Key-public.xlsx")
    )
    key = next(
        ercot.generation_profiles.read_keys(
            ercot.generation_profiles.download(source), filename=source.title
        )
    )
    for plant in key.sites:
        if plant.cdrZone == "West" and plant.unitCode:
            print(plant.unitCode, plant.capacityMW)
```

`GenerationProfileKey` contains typed site/unit rows, published summary counts,
source title/date and notes with worksheet locations. Site rows retain source row
numbers, numeric site IDs, unit codes, location, capacity and available equipment
metadata. `tilt` preserves the source's `Lat` and `NA` labels as well as numbers.
`queuedModelFlag` reads the wind key's colour legend; `None` means no such legend
was supplied. Multiple unit codes for the same site remain separate records.

Use matching vintages and inspect unmatched identifiers before joining. In the
1980–2021 solar key, `TREBA_UNIT 1` contains a space absent from the profile column
`TREBA_UNIT1`; 163 of 164 unit codes match exactly. The SDK preserves both source
spellings. Published summaries are also retained independently: the 1980–2020
solar key reports 313 utility profiles while its detailed scenario totals sum
to 331. `sourceDate` is the workbook's own date, not an asserted publication time.


Older wind CSVs can contain independently dated tables side by side.
`sourceBlock` identifies each table (starting at 1) on both hourly records and
site metadata. The reader emits each block with its own date, clock and sites;
for example, a 2011 onshore table can share a file with 2013 offshore data.
Entirely empty trailing blocks produce no records. Records are emitted in source
row/block order, which need not be chronological across blocks. The original
`YYYYMMDD`/`HHMM(CST)` headers are supported alongside newer `DATE`/`TIME` layouts.

The older existing/hypothetical wind workbooks are also accepted by `read()` and
`sites()`. Their blank column headings use the numeric IDs from the source's
`Site ID`/`SITE_ID` row as string keys, without inventing padded IDs or unit codes.
`calendarDate` preserves the separate Year/Month/Day cells, while `profileDate`
and `sourceTime` retain the primary date/clock pair. The original `YYMMHH(CST)`
and `TIME-CST` clock labels remain available in `sourceTimeColumn`.

Site metadata includes the original AWS name, annual MWh and capacity-factor
mappings where published, and the hypothetical workbook's `sourceSum`,
`sourceCount` and `sourceCapacityFactor`. These summaries are read as supplied;
they are not recalculated from the hourly rows. `sourceSum` preserves the field
labelled `Sum` without assigning it an inferred unit. Empty worksheets and blank
formatting rows do not create observations.
