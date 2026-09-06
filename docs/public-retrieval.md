# Opt-in public retrieval

This additive milestone preserves the legacy client. Import retrieval tools
from `tinyercot.public`. The Stage-0 catalog remains an audit snapshot.
Use `coverage()` for retrieval scope states.

## Coverage and evidence

On 2026-09-05/06 UTC isolated installed wheels retrieved and decoded public data.
Generated typed API coverage is **4 operations in 4 products**: NP4-190-CD,
NP4-188-CD, NP6-905-CD, and NP6-345-CD. PR #2 established the first two DAM
contracts; this iteration adds RT settlement prices and weather-zone actual load
through a shared registry and retrieval client.
The denominator is **243 observed public data paths in 98 product namespaces**
(242 public-reports paths and one public-data ESR path). This is a bounded
vertical slice, not broad typed coverage. The legacy 102 endpoints do not add
to current verified coverage. Website ESR is separate from the four-second
Public Data API. A namespace count does not establish an EMIL product census.

| Evidence class | Exact supported or observed scope |
| --- | --- |
| Typed installed-client current fetch | NP4-190-CD DAM settlement prices: two pages of two HB_HOUSTON rows for 2026-09-04; another row after explicit ID-token reacquisition. NP4-188-CD: two REGUP capacity-price rows for 2026-09-04. |
| Typed installed-client historical fetch | NP4-190-CD HB_HOUSTON and NP4-188-CD REGUP: one oldest-first row each returned 2023-12-13. NP4-180-ER report 13060: four rows each from 2010/Dec_1 and 2026/Aug workbooks, with truncation and cache reuse verified. |
| Typed installed-client live fetch | Website ESR: 482 rolling rows in the final installed probe; source offset/epoch and freshness checks passed. Not four-second API coverage. |
| New typed installed-client current fetch | NP6-905-CD HB_HOUSTON RT prices and NP6-345-CD weather-zone load: two rows each for 2026-09-04. |
| New typed installed-client historical fetch | One oldest-first row per new endpoint, both dated 2023-12-11. These dates establish observations, not complete retention. |
| Complete bounded installed-client query | Two RT rows for HB_HOUSTON, 2026-09-04, hour 1, intervals 1–2, retrieved across two one-row pages with matching totals. |
| Real source retrieval only | NP4-190-CD product metadata, retained as a fixture. This is not an implemented product-metadata method. |
| Fixture-only behavior | Rate limits, transport retries, expired tokens, 401/403, malformed JSON/ZIP/XLSX, cache mutation, repeated pages, DST transitions. These faults were simulated, not induced on ERCOT. |
| Deferred schema | The other 239 observed data paths. Stage 0 recorded 40 missing and 203 unverified cached schemas. Current field evidence verifies four endpoints. No guessed raw or typed models. |
| Restricted | Secure, Certified, EWS, private telemetry, bids/COP/awards, participant settlements and customer data. No requests. |
| Unavailable | Retired total-AS-offer and SASM sources and the unavailable hourly-load 2001 year, as recorded in the audit. |

Only two selected annual files were downloaded. Each was retrieved once during
source discovery and once through the installed adapter. Later uses reuse a
hash-verified cache. No all-year iteration or bulk historical extraction ran.
Authorized Public API authentication did occur in this milestone. No credential
or token values were retained in evidence, fixtures, logs, source, or PR text.

The oldest row is the earliest returned observation for the selected point at
the retrieval time. It is not proof of complete history or stable retention.
Archive publication time, data date, and retrieval time remain separate.
No adapter provides an as-of vintage, revision merge, or complete-year claim.
Typed installed-client retrieval means generated or explicit Pydantic row decoding.
The wheel now separately includes PEP 561 metadata. An isolated mypy proof checks
all 510 legacy method return contracts, all 1,334 legacy row fields, new public
row/filter/iterator contracts, and rejection of four invalid uses. Legacy
runtime files remain byte-identical; companion stubs expose their existing types.

## Use annual files

Install the optional XLSX decoder with `uv add 'tinyercot[files]'`.
Listing and live metadata do not require this extra.

```python
from pathlib import Path
from tinyercot.public import WebClient, sample_dam_archive

with WebClient() as client:
    documents, listing_receipt = client.dam_archives()
    document = next(d for d in documents if d.friendly_name == "DAMLZHBSPP_2010")
    download = client.download_dam_archive(document, cache=Path(".ercot-cache"))
    sample = sample_dam_archive(download, sheet="Dec_1", max_rows=4)
    assert sample.truncated  # A sample does not establish complete annual coverage.
```

The adapter uses the source page's `mirDownload` route. A discovery request to
`ViewReport` returned HTTP 200 with an HTML "No Document" page. HTTP status alone
does not verify a file. The adapter checks the public listing, received byte
count, ZIP structure, XLSX headers, cell types, and cached hash. It rejects
partial or changed cache entries. The caller must inspect and repair them
explicitly. It does not overwrite a prior document when publication changes.
Cache writes use POSIX exclusive-file and hard-link operations.

Each download selects one listed public file. `sample_dam_archive` preserves
its one-sheet/1,000-row contract. The new `iter_dam_archive` can visit every
worksheet and row, with configurable scan, row, member, and expansion safeguards.
The cache preserves document ID, publication time, original retrieval time,
and hash. Workbook prices use Decimal conversion of numeric source cells.
Date, hour-ending, and repeated-hour fields stay separate. No guessed UTC
mapping joins the source's ambiguous local market intervals.

## Complete query and annual-file iteration

```python
from datetime import date
from tinyercot.public import Credentials, ReportsClient, RT_PRICES, StreamingLimits

with ReportsClient(
    Credentials.from_env(), limits=StreamingLimits(max_requests=None)
) as client:
    for row in RT_PRICES.iter_rows(
        client,
        filters={
            "deliveryDateFrom": date(2026, 9, 4),
            "deliveryDateTo": date(2026, 9, 4),
            "settlementPoint": "HB_HOUSTON",
        },
        sort="deliveryInterval", size=1000, max_pages=None, max_rows=None,
    ):
        process(row)  # Caller-defined consumer; no accumulation is required.
```

`DAM_PRICES`, `DAM_CAPACITY_PRICES`, `RT_PRICES`, and `SYSTEM_LOAD` each bind a
generated row and TypedDict filter contract. Number filters accept float,
Decimal, or int; date filters require Python dates. Unknown fields and invalid
ranges fail before authentication. The 1,000-row page cap and default 100-page,
100,000-row, and 100-request budgets are local safeguards, not asserted ERCOT
service limits. Set the three total budgets to None only for an intentional
complete query. Per-response bytes, retry attempts, and pacing stay bounded.
Iteration rejects changing totals, a repeated preceding page, or final counts
that disagree with `totalRecords`. Source order and duplicates are preserved;
unchanged totals cannot prove a stable as-of snapshot.

```python
from contextlib import closing
from tinyercot.public import iter_dam_archive

# download is one previously selected, receipt-verified public annual ZIP.
with closing(iter_dam_archive(download, max_rows=None, max_scan_rows=None)) as rows:
    for record in rows:
        process(record.row, record.sheet, record.row_number)
```

Omit `sheets` to visit every worksheet in source order, or select exact names.
Rows stream through openpyxl's read-only mode; the bounded compressed ZIP and
XLSX member remain in memory. Closing early releases the workbook. Complete
iteration is tested with a synthetic two-sheet, 2,010-row file; real validation
only sampled the two already cached annual files. It does not establish that
ERCOT's requested file contains a complete year or every historical revision.

## HTTP, token, and time contracts

Defaults allow 20 HTTP attempts per client, including authentication and
retries, at least 2.1 seconds between starts, and at most 4 MB per response.
These are per-client ceilings, not an account-wide rate limiter. Callers that
run several clients must coordinate their total request rate.
The new surface retries 429, 502, 503, 504 and transport failures within its
attempt budget. It respects bounded Retry-After delays. It does not follow
redirects or retry 403. One 401 can trigger one ID-token reacquisition.
The client reacquires before the documented expiry with a 60-second margin.
`refresh_token()` means a new ID-token POST, not use of a returned refresh token.
The verified form-encoded request keeps credentials out of URLs.

The ESR decoder checks source offsets against America/Chicago and checks epoch
milliseconds against each timestamp. It retains the source DST flag without
guessing its meaning. Source update time and freshness remain visible; a stale
snapshot is not silently described as current. The rolling feed supplies no
history or latency guarantee. Future and old source timestamps are stale.
Mocked DST fixtures cover the repeated fall hour and the missing spring hour.

## Reproduction and evidence

The generators read only hash-pinned local inputs. Current row pins include
actual response field descriptors and query provenance. Nullability is unknown;
the four models reject nulls and cover observed non-null rows only. Field order
comes from each response, while unknown/missing names or source types fail.
The registry generates every pinned query filter. This does not establish every
filter's server-side range semantics or coverage of every schema epoch.

`tools/discover_public.py --spec saved-openapi.json --response small-response.json
--receipt public-receipt.json --path /np6-905-cd/spp_node_zone_hub --output
candidate.json` projects evidence offline. The exact OpenAPI hash must match
the primary catalog pin; the receipt must match the response URL, bytes and hash.
Review the candidate and register its hash/names in `tools/inputs/current/provenance.json`,
then run `tools/generate_public.py`. Generation never refreshes upstream data.
Missing fields, empty/null samples, or unsupported types remain missing/unknown;
they do not create a raw or typed adapter. The catalog retains every unsupported
operation independently of this four-endpoint registry.

`docs/evidence/fixture-provenance.json` records public source hashes, retrieval
times, fixture hashes, and excerpt transformations. `installed-receipts.json`
records installed-client fetches without headers, credential values, or row
values. API fixtures are small public responses. ESR is an explicit excerpt.
`installed-reports-receipts.json` records the six new installed-client requests.
Workbook tests build tiny XLSX files from recorded source cells. Full annual
archives and raw live snapshots are not checked in.

The normal suite blocks network access. The real integration entry point is
skipped unless `TINYERCOT_LIVE_TESTS=1`. It also requires explicit absolute paths
in `TINYERCOT_INSTALLED_PYTHON`, `TINYERCOT_CREDENTIALS_FILE`, and
`TINYERCOT_PROBE_OUTPUT`. Use an isolated installed wheel with the files extra.
The credential path must be a regular mode-0600 file with the three ERCOT keys
and JSON-quoted values, as produced by the authorized local vault export.
Do not commit that file. `tools/probe_public.py --live` performs a fixed small
2026-09-04/oldest-price check, one rolling ESR request, one public listing, and
the two selected annual samples. Reuse its output cache to avoid redownloads.
`--reports-only` instead makes six bounded RT/load data requests: current,
oldest-first, and the complete two-row selection. Neither probe runs in CI.

Primary sources: ERCOT's [current Public Reports specification](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview),
[authentication guide](https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication/),
[known limits](https://developer.ercot.com/applications/pubapi/known-limits/),
[public annual DAM product](https://www.ercot.com/mp/data-products/data-product-details?id=np4-180-er),
and [ESR website feed](https://www.ercot.com/api/1/services/read/dashboards/energy-storage-resources.json).

## Audited source families

This table enumerates all 39 audited families, including 33 deferred public or
conditional boundaries, three restricted families, and three unavailable gaps.
Supported narrow subsets above do not mark an entire family covered. Product
IDs and primary ERCOT URLs are retained in `tinyercot/public/_coverage.json`.
This inventory includes website collections as well as EMIL products.

| Family | State | Product or collection IDs |
| --- | --- | --- |
| DAM prices, lambda, constraints | deferred | NP4-183-CD, NP4-188-CD, NP4-190-CD, NP4-191-CD, NP4-523-CD |
| RT SCED prices and constraints | deferred | NP6-787-CD, NP6-788-CD, NP6-322-CD, NP6-86-CD, NP6-905-CD |
| Price corrections and investigations | deferred | NP4-196-M, NP4-197-M, NP4-46-AN, NP4-47-AN, NP4-48-AN, NP4-49-AN |
| Historical hub/zone and AS price files | deferred | NP4-180-ER, NP6-785-ER, NP4-181-ER |
| RTD indicative prices and capacity prices | deferred | NP6-970-CD, NP6-325-CD, NP6-329-CD |
| RTC+B ancillary prices, capability, and SOG | deferred | NP6-323-CD, NP6-324-CD, NP6-326-CD, NP6-327-CD, NP6-328-CD, NP6-331-CD, NP6-332-CD |
| Historical RT adders and RTC+B archives | deferred | NP6-792-ER, NP6-793-ER, NP6-794-ER, NP6-795-ER, NP6-796-ER |
| DAM plans, energy totals, AS offers/demand curves | deferred | NP4-33-CD, NP4-19-CD, NP4-192-CD, NP4-193-CD, NP4-212-CD, NP4-532-CD, NP1-302 |
| Legacy total AS offers | unavailable | NP4-179-CD |
| RUC demand curves, deployment factors, constraints | deferred | NP4-213-CD, NP4-214-CD, NP4-215-CD, NP5-525-CD, NP5-526-CD, NP5-527-CD, NP5-528-CD, NP5-520-ER, NP5-753-CD, NP5-754-CD, NP5-755-CD, NP5-108-CD, NP3-764-CD |
| System and zonal actual load | deferred | NP6-345-CD, NP6-346-CD, NP6-344-CD, NP6-235-CD, GEN-55-CD |
| Load forecasts | deferred | NP3-565-CD, NP3-566-CD, NP3-560-CD, NP3-561-CD, NP3-562-CD |
| Long hourly-load archive | deferred | WEBSITE-LOAD-HISTORY |
| Wind and solar actual/forecast series | deferred | NP4-732-CD, NP4-733-CD, NP4-737-CD, NP4-738-CD, NP4-742-CD, NP4-743-CD, NP4-745-CD, NP4-746-CD |
| Renewable forecast models and intra-hour forecasts | deferred | NP4-442-CD, NP4-443-CD, NP4-751-CD, NP4-752-CD |
| Storage four-second Public Data API | deferred | RPTESR-M |
| Live storage, fuel mix, and generation outages | deferred | GEN-545-UI, GEN-544-UI, GEN-546-UI |
| Live grid conditions, reserves, supply and demand | deferred | GEN-530-UI, GEN-518-UI, GEN-506-UI, GEN-536-UI, NP6-904-CD, NP6-906-UI, GEN-547-UI |
| Live price, weather, combined renewable displays | deferred | GEN-502-UI, GEN-523-UI, GEN-522-UI, GEN-526-UI, GEN-540-UI, GEN-542-UI, GEN-539-UI, GEN-537-UI, GEN-507-UI |
| Outage capacity, unplanned outages, adequacy | deferred | NP3-233-CD, NP1-346-ER, NP3-763-CD, NP3-161-CD, NP3-162-CD, OPG-103-ER |
| DC tie schedules, flows, and state-estimator aggregates | deferred | NP3-765-CD, NP6-626-CD, NP6-625-CD, GEN-538-UI |
| 2-day dispatch, energy curves, bids and offers | deferred | NP3-906-EX, NP3-907-EX, NP3-908-ER, NP3-909-ER, NP3-910-ER, NP3-911-ER |
| 3-day and event disclosures | deferred | NP3-257-EX, NP3-914-EX, NP3-915-EX, NP3-916-EX, NP3-987-EX |
| 60-day SCED and DAM disclosures, including ESR | deferred | NP3-965-ER, NP3-966-ER |
| COP snapshot and all updates | deferred | NP1-301, NP3-991-EX |
| Legacy SASM disclosures | unavailable | NP3-990-EX |
| Settlement-point and electrical-bus mapping | deferred | NP4-160-SG, NP4-158-SG, NP4-200-CD, NP4-231-CD, NP4-159-CD |
| Public CRR auctions, ownership, and PTP results | deferred | NP7-802-M, NP7-803-M, NP7-535-SG, NP7-536-SG, NP7-157-SG, NP7-464-CD, NP4-194-CD |
| Scarcity, fuel cost, demand response, and integration reports | deferred | NP4-790-CD, NP4-791-CD, NP4-412-CD, NP4-494-ER, NP3-107, NP3-108, NP3-109, NP3-110, NP4-760-ER, NP4-765-ER, EIA-930-ER |
| Load profiles, loss factors, and settlement aggregates | deferred | ZP18-68-M, ZP18-67-M, ZP18-265-SG, NP13-9-SG, NP13-14-SG, NP13-262-SG, NP13-268-SG, NP9-598, NP1-300, COMS-770-SG |
| Adequacy, planning, CDR, MORA and SARA history | deferred | NP3-774-M, NP3-784-M, NP3-773-M, NP3-240-M, PG7-048-M |
| Interconnection, resource lists and DG reports | deferred | PG7-201-ER, NP3-988-ER, NP16-533-M, NP3-823-M, NP12-215-ER, NP16-474-M |
| Frequency events and public notices | deferred | NP12-261-M, NP12-265-M, NP6-87-AN, OPG-453-AN, OPG-158, ZP4-405-M, NP4-50-AN |
| Weather archive contractual boundary | deferred | WEBSITE-WEATHER-1996-2000, NP4-722-CD |
| Unavailable hourly-load year | unavailable | WEBSITE-LOAD-2001 |
| Certified participant settlements and retail usage | restricted | NP9-170-SG, NP9-566-SG, ZP12-245, COMS-448 |
| Secure models, network ratings and ECEII | restricted | NP4-500-SG, NP6-216-ER, NP3-217-CD, NP3-459-SG |
| Participant EWS, telemetry, private bids/COP/awards | restricted | NP4-302-UI, NP4-303-UI |
| Zonal-era and other old public collections | deferred | WEBSITE-ZONAL-ARCHIVES |
