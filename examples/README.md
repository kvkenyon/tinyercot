# Market-data workflows

Run these examples from the repository with `ERCOT_USERNAME`, `ERCOT_PASSWORD`,
and `ERCOT_SUBSCRIPTION_KEY` set locally. They use the generated typed client and
write JSON Lines, one record per line. The output paths are overwritten on each
run; choose a separate directory for each operating day or settlement point.

## Prices and load for an operating day

```sh
uv run python -m examples.market_day 2026-09-01 --point HB_HOUSTON --output market-data/2026-09-01
```

The example follows every query page and writes:

| File | Data | Useful inputs for |
| --- | --- | --- |
| `dam_prices.jsonl` | Hourly DAM settlement prices for the selected point | Retail hedging and day-ahead trading analysis |
| `rt_prices.jsonl` | 15-minute RT settlement prices for the same point | Real-time exposure and battery revenue analysis |
| `dam_ancillary_prices.jsonl` | DAM clearing prices for all returned ancillary-service types | Ancillary-service market analysis |
| `actual_load.jsonl` | Hourly actual load for all eight weather zones and ERCOT | Demand features and retail forecasting |

Use `--point LZ_HOUSTON` for a settlement load zone or another published hub/load-zone
name. Weather zones and settlement load zones are different geographies. The files
retain their original frequency, fields, nulls and DST flags. Settlement prices
are distinct from SCED LMPs. Decimal values are serialized as strings to preserve
precision; hour-ending labels remain source labels. These inputs can feed an
analysis, but the example does not calculate trading returns or customer charges.

This example uses row-query endpoints. For older data outside an endpoint's query
retention, use its typed `_history.backfill()` reader; see the [historical download
examples](../docs/usage.md). Exporting no rows is not proof that no archive exists.

## Forecasts as they were published

```sh
uv run python -m examples.forecast_vintages 2019-01-01T00:30 2019-01-01T00:30 --output market-data/forecast-vintages.jsonl
```

Each line is a typed `ForecastVintage` containing the original archive `document`
and a typed historical `forecast`. Bounds select inclusive ERCOT-local posting
times. Every forecast issue is preserved, including repeated target dates or
identical predicted values. Some older forecast rows have no embedded
`postedDatetime`; the document's publication time remains available separately.

For an as-issued backtest, select documents whose `postDatetime` is no later than
the decision time, then select the desired forecast delivery date/hour. A delivery
date or a monthly bundle's posting time does not establish when a forecast became
available. Actual load and later forecast issues must not be substituted for a
forecast available at an earlier decision time.

Live checks of these functions are recorded in
[`market-workflows-evidence.json`](../tools/inputs/market-workflows-evidence.json).
They verify retrieval and serialization; they are not a forecast-accuracy backtest.


## Market context as it was published

```sh
uv run python -m examples.market_context 2026-09-01T00:00 2026-09-01T01:00 --output market-data/context
```

This exports four files using existing generated history readers:

| File | Published data |
| --- | --- |
| `load_forecasts.jsonl` | Seven-day weather-zone load forecasts |
| `wind.jsonl` | Regional wind actuals, forecasts and reported capability |
| `solar.jsonl` | Regional solar actuals, forecasts and reported capability |
| `outages.jsonl` | Hourly resource outage capacity |

Each line contains the original archive `document` and its typed `row`.
`PublishedRow[ConcreteHistoryRow]` can read that envelope back with the generated
type. Decimal strings, nulls, DST flags, delivery periods and separate forecast
issues survive the export. Bounds select inclusive ERCOT-local **publication
times**, without offsets; they do not restrict the delivery periods in each report.

For a trading or battery backtest, select the most recent available issue for each
source and target interval at the decision time. Use the document's posting time
even when the row has no embedded timestamp. Do not join on publication time:
these products publish on different schedules. Wind and solar reports contain
both actual and forecast fields; keep their meanings separate. The existing
`market_day` example supplies realized prices and load for comparison.

All selected issues and corrections remain separate. A narrow window may contain
no publication for a source; widen the window when looking for its preceding
issue. Output files are overwritten and an interruption can leave partial files.
This example retrieves model inputs; it does not calculate features or returns.

The [live receipt](../tools/inputs/market-context-evidence.json) records the checked
publication window and typed export counts.

## Retained settlement-price history

```sh
uv run python -m examples.price_history dam --point HB_HOUSTON --output dam-history.jsonl
uv run python -m examples.price_history rt --point LZ_HOUSTON --output rt-history.jsonl
```

Both commands use the concrete typed DAM/RT reader's `backfill()` method. They
combine monthly bundles and remaining individual archives, including publications
found only in bundles. The output keeps original fields, decimal strings, nulls,
and DST flags. Overlapping copies of a publication are retrieved once; distinct
corrections remain separate, and rows are not sorted.

Optional `--date-from YYYY-MM-DD` and `--date-to YYYY-MM-DD` filter inclusive
**delivery dates**, after download. They do not supply publication bounds or
reduce the amount downloaded. These are maximum-history workflows and can take
considerable time; use `market_day` for bounded recent queries. The output file
is overwritten, and an interrupted run can leave a partial file.

The price-history exporter is checked with saved original DAM/RT CSV samples and
mocked archive/bundle listings, including a bundle-only publication and an
archive-only publication. This verifies its use of the existing backfill reader;
it is not a new live comparison of every retained RT price row. See the
[market-data guide](../docs/market-data.md) for verified ranges and remaining gaps.
