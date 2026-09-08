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
examples](../README.md). Exporting no rows is not proof that no archive exists.

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
