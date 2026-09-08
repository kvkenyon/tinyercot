# tinyercot

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
Direct public load and fuel-mix files extend the available time series. Planning
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

Runnable [market-data examples](examples/README.md) export a day of settlement
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
and the current locational price map.

Detailed field mappings, historical layout changes and source limitations are
recorded in [data coverage](docs/data-coverage.md).
