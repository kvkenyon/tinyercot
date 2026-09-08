# Choosing market data

Start with the dataset that matches the decision or target you are modeling.
Scope is public data for pricing, dispatch, hedging, load forecasting, settlement,
and resource planning. Compliance-only legacy summaries and narrative documents
are outside that scope. Older market observations remain useful historical data.

All paths below are relative to a `Client()` named `ercot`. Each history reader
returns concrete Pydantic rows and supports `read`, `rows`, and `backfill`.

| Data | Typed history reader | Preserve when using it |
| --- | --- | --- |
| DAM settlement prices | `np4_190_cd.dam_stlmnt_pnt_prices_history` | Settlement point, hour ending, DST flag |
| RT settlement prices | `np6_905_cd.spp_node_zone_hub_history` | Point type, delivery hour and interval, DST flag |
| SCED settlement-point LMPs | `np6_788_cd.lmp_node_zone_hub_history` | SCED timestamp and original price fields |
| RTD indicative LMPs | `np6_970_cd.rtd_lmp_node_zone_hub_history` | Run timestamp and forecast interval |
| SCED price adders | `np6_323_cd.rt_price_adder_sced_history` | Legacy ORDC and newer reliability-adder fields separately |
| DAM ancillary-service prices | `np4_188_cd.dam_clear_price_for_cap_history` | Service type, hour ending, DST flag |
| RT ancillary-service prices | `np6_795_er.clearing_prices_history` / `np6_796_er.clearing_prices_history` | SCED and settlement intervals separately; capped/uncapped fields where supplied |
| Actual weather-zone load | `np6_345_cd.act_sys_load_by_wzn_history` | Operating day, hour ending, eight weather zones and system total |
| Seven-day weather-zone load forecasts | `np3_561_cd._7d_load_fcast_by_wzn_history` | Original publication plus target delivery date/hour |
| Regional wind actuals and forecasts | `np4_742_cd.wpp_hrly_actual_fcast_geo_history` | Region, forecast horizon, source timestamps |
| Regional solar actuals and forecasts | `np4_745_cd.spp_hrly_actual_fcast_geo_history` | Region, forecast horizon, source timestamps |
| Hourly outage capacity | `np3_233_cd.hourly_res_outage_cap_history` | Published totals and regions; older files may lack regions |
| Binding-constraint shadow prices | `np6_86_cd.shdw_prices_bnd_trns_const_history` | Constraint identity and SCED timestamp |
| DAM resource awards and offers | `np3_966_er._60_dam_gen_res_data_history` | Resource, delivery interval, original ancillary-service categories |
| SCED battery disclosures | `np3_965_er._60d_sced_esr_data_history` | Disclosure lag, resource identity, original interval |
| Public resource ownership | `np3_988_er.resources_history` | Published ownership/reference information and vintage |

For recent row-query data, remove `_history` and append `_iter` to stream every
page. Archive-only products, including the RT AS workbook readers and ownership
reference data above, have no corresponding row-query method. The generator does
not invent endpoints for them. XLS/XLSX history requires the `files` extra.

## Common workflows

**Retail exposure:** start with DAM/RT prices at the relevant settlement point,
actual load and forecasts, then add public `load_profiles`, `coincident_peaks`,
and `loss_factors` where applicable. Public system and profile data do not supply
a retailer's private customer interval loads or contracts. Weather zones and
settlement load zones are different geographies.

**Battery analysis:** combine settlement prices, ancillary-service prices,
constraints, outages, and renewable/load forecasts. Use the public
`dashboards.sced_capacity()`, `dashboards.ancillary_capacity()`, and
`dashboards.energy_storage()` snapshots for their published operating context.
Aggregate system data do not establish an individual battery's feasible dispatch.
The public SCED ESR disclosure is part of Public Reports; it is distinct from
the separate ESR API, now available through `ESRClient`; see the
[ESR workflow](usage.md#energy-storage-four-second-data). Its verified latest
record is from December 2025, so check source freshness before operational use.

For published forecast-error analysis, `load_forecast_performance` supplies
actual/selected hourly series and separate error summaries for ERCOT and the
eight weather zones. See the [performance workflow](usage.md#hourly-load-forecast-performance);
these workbooks do not establish original forecast issue times.

**Trading and forecasting:** preserve publication metadata for forecasts,
resource reports, and delayed disclosures. `history.publications()` keeps each
original archive `Document` beside its typed rows. Select information available
by the decision time before evaluating it against later realized outcomes.
Settlement prices, SCED LMPs, RTD indicative prices, and separate adders are
separate series; adding an adder to a series that already includes it double-counts it.

## How much history is verified?

The September 2026 checks establish different levels of evidence:

| Dataset | Verified historical extent | Evidence level |
| --- | --- | --- |
| DAM settlement prices | May 2, 2014–September 8, 2026; 81,236,426 rows, 1,230 observed points | Every field compared across retained archives and bundles; a point need not exist throughout the range |
| DAM ancillary-service prices | May 2, 2014–September 8, 2026; 461,736 rows | Every field compared across retained archives and bundles; ECRS begins June 10, 2023 |
| Actual weather-zone load | April 30, 2014–September 6, 2026; 108,285 rows | Every field compared; December 4, 2025 and three older hour-ending-24 observations are absent |
| RT settlement prices, wind, SCED constraints, hourly outage capacity | Earliest archive posting observed May 1, 2014 | Listing bounds and sampled layouts; complete intervening rows have not been compared |
| Solar actuals/forecasts | Earliest archive posting observed February 10, 2016 | Listing bounds and sampled layouts |
| Weather-zone load forecasts | Earliest archive posting observed January 1, 2019 | Oldest forecast decoded with original publication metadata; bundles cover a shorter period |
| RT ancillary-service prices | Earliest archive posting observed December 5, 2025 | Listing bounds and sampled workbook layouts |

An additional complete-file check decoded 28,881,274 rows in 221 distinct intermediate
and annual samples across disclosure, offer-curve, and forecast readers. It checks
decoding and source row counts, not every retained publication or independent
numerical values. The [receipt](../tools/inputs/history/intermediate-full-file-evidence.json)
and [per-file manifest](../tools/inputs/history/intermediate-full-files.csv) record
its scope and decoder version.

These are recorded checks, not promises of permanent ERCOT retention. Publication
boundaries are not delivery-date boundaries. The [source coverage notes](data-coverage.md)
and [full usage reference](usage.md) link the receipts, layout variants, and gaps.

## Retrieve the widest history

From the repository, export one settlement point using both retained sources:

```sh
uv run python -m examples.price_history dam --point HB_HOUSTON --output dam-history.jsonl
uv run python -m examples.price_history rt --point LZ_HOUSTON --output rt-history.jsonl
```

The export uses unbounded `backfill()`, so it includes bundle-only publications
and archives older than the bundles. Optional `--date-from` and `--date-to`
filter **delivery dates after download**; they do not reduce source downloads.
Unbounded backfills return bundle rows before fetching archive listings;
they then stream the uncovered archives. Large histories still take time.
For bounded recent data use the
[market-day example](../examples/README.md#prices-and-load-for-an-operating-day).

Output keeps original fields, decimal precision, nulls, and DST flags. It is not
sorted; distinct correction publications remain separate. Do not treat the
number of returned rows as a count of unique operating intervals. For
publication-aware exports, use the forecast-vintage example instead.

## Weather and fleet scenarios

[Modeled generation profiles](usage.md#modeled-wind-and-solar-generation-profiles)
provide typed wind and solar planning series, with verified samples extending
back to 1980. Use them for resource and fleet scenarios. They describe modeled
plants under reconstructed weather, rather than the observed historical fleet;
they must not be treated as historical forecasts in a trading backtest.

For longer-term demand and scarcity scenarios, `peak_demand_forecasts.rows()`
returns typed summer peak forecasts under historical weather years, with original
source-file metadata. It keeps gross/net demand, rooftop-PV impact, large-load
assumptions and TSP/adjusted scenarios separate. See the
[forecast workflow](usage.md#long-term-peak-demand-forecasts). These are planning
forecasts, not realized hourly demand. `monthly_load_forecasts.rows()` adds
monthly peak/energy values with source dates, declared units and publication
metadata; see the [monthly forecast workflow](usage.md#monthly-peak-demand-and-energy-forecasts)
for the 2025 source date/value ambiguity. Seasonal and weekly weather-zone
peaks are available through `seasonal_peak_forecasts` and `weekly_peak_forecasts`.
Their [workflow](usage.md#seasonal-and-weekly-weather-zone-peaks) keeps historical
sections, coincident/non-coincident peaks and forecast percentiles distinct.
`hourly_load_forecasts` adds hourly regional load components from the 2021–2025
publications, including both 2025 TSP and adjusted scenarios through target year
2044. The [hourly workflow](usage.md#hourly-long-term-load-forecasts) preserves
separate gross/net/PV/EV and large-load values, original hours and date discrepancies.
For regional weather exposure, `hourly_load_scenarios` adds all eight weather zones
with 45 weather-year predictions per source hour. The
[scenario workflow](usage.md#hourly-weather-year-load-scenarios) keeps predictions
and adjustment components separate, with source target dates through 2035.

## Current limits

All 242 report queries in the verified Public Reports inventory have typed
methods, and all their report tables have history readers. That does not prove
that every intermediate historical file format is supported or every public
website dataset has been decoded. Remaining website coverage includes the separate monthly Forecast/Backcast
summary workbooks and the
winter reliability-standard hourly forecast. Further historical layout verification is also
needed for core market products. Broad legacy document extraction is deferred
while market-data coverage and usability take priority.
MIS remains excluded. In particular, ERCOT separately
lists [annual DAM hub/load-zone prices](https://www.ercot.com/mp/data-products/data-product-details?id=NP4-180-ER),
[annual RTM hub/load-zone prices](https://www.ercot.com/mp/data-products/data-product-details?id=NP6-785-ER),
and [annual DAM ancillary-service prices](https://www.ercot.com/mp/data-products/data-product-details?id=NP4-181-ER)
through ICE/MIS listings. The captured product pages advertise no direct-file
alternative. Those sources are not queried by this client's Public Reports
backfills, and their earliest available years have not been established here.
The 2014 API archive bounds above therefore do not establish the earliest price
history ERCOT holds. Existing specialized readers are documented in the usage
reference.
