# tinyercot

A small, fully typed ERCOT data client for retailers, battery operators, and
energy traders. Query recent data, stream historical archives and monthly
bundles, or read public load and generation files. Coverage focuses on data for market
decisions, settlement and resource planning.

## Install and connect

This development branch contains the API described below. Install from its checkout:

```sh
pip install .
```

Set `ERCOT_USERNAME`, `ERCOT_PASSWORD`, and `ERCOT_SUBSCRIPTION_KEY`, or pass
`username`, `password`, and `subscription_key` to `Client`. Credentials are read
lazily; anonymous public downloads do not need them.

```python
from datetime import date
from tinyercot import Client

with Client() as ercot:
    for price in ercot.np4_190_cd.dam_stlmnt_pnt_prices_iter(
        deliveryDateFrom=date(2026, 9, 1),
        deliveryDateTo=date(2026, 9, 1),
        settlementPoint="HB_HOUSTON",
    ):
        print(price.deliveryDate, price.settlementPointPrice)
```

Methods have named, typed filters and Pydantic row models. A method returns one
`Page[Row]`; `_iter` streams every page. `_async` and `_iter_async` provide async
access. Dates, decimals, missing values, and DST flags retain their source meaning.

## Get the available history

Use the same method name with `_history`. `backfill()` combines monthly bundles
with individual archives, including older and bundle-only reports:

```python
with Client() as ercot:
    history = ercot.np4_190_cd.dam_stlmnt_pnt_prices_history
    for price in history.backfill(
        where=lambda row: row.settlementPoint == "HB_HOUSTON",
        batch_size=25,
    ):
        print(price.deliveryDate, price.hourEnding, price.settlementPointPrice)
```

This requests all retained publications and can take considerable time. The
predicate filters typed rows after download. Original document IDs prevent
fetching the same publication twice; distinct corrections and repeated source
rows remain intact. Output is streamed without sorting.

`posted_from` and `posted_to` select **publication times**, which can differ from
operating dates. Omit them for the widest history, including bundle-only reports.
Use `publications()` to retain each archive's original posting metadata for
forecast backtests. A bundle's timestamp does not establish when its forecasts
were available. `read(zip_bytes)` decodes saved downloads with the same types.

Runnable exports from this repository:

```sh
uv run python -m examples.market_day 2026-09-01 --point HB_HOUSTON --output market-data
uv run python -m examples.price_history dam --point HB_HOUSTON --output dam-history.jsonl
uv run python -m examples.price_history rt --point HB_HOUSTON --output rt-history.jsonl
```

See the [market-data guide](docs/market-data.md) to choose price, load, forecast,
ancillary-service, outage, and disclosure readers, and the
[examples](examples/README.md) for export details and forecast vintages.

## Coverage

The September 7, 2026 inventory check matched **242 Public Reports queries** and
**249 HTTP operations** including shared metadata/download operations. Generated
history readers cover **289 tables across 113 products**. This establishes API
and known-format coverage, not uninterrupted history for every dataset.

Full-source comparisons cover retained DAM settlement prices, DAM ancillary
prices, and weather-zone actual load. Other products have sampled historical
layout checks; see the [coverage evidence](docs/data-coverage.md). Available
history and source gaps differ by product. The separate ESR service adds one
generated query and its history reader through `ESRClient`, using
`ERCOT_ESR_SUBSCRIPTION_KEY` with the same username/password. See the
[ESR workflow](docs/usage.md#energy-storage-four-second-data) for verified retention
and source freshness. MIS remains outside the current scope.

Direct public services include `hourly_load`, `fuel_mix`, `load_profiles`,
`loss_factors`, `load_forecast_performance`, and `dashboards`. Install `tinyercot[files]` for XLS/XLSX/XLSB readers
or `tinyercot[pdf]` for supported PDF tables. Detailed source-specific examples
remain in the [usage reference](docs/usage.md).

## Development

Product methods and row models are generated from saved ERCOT definitions. The
runtime depends on `httpx`, `httpx-retries`, and `pydantic`; optional file parsers
are loaded when used. Source fixtures support tests and generation and are
excluded from the installed wheel.

```sh
uv sync --group dev
uv run python tools/generate_client.py
uv run mypy tinyercot tests/typing_client.py examples --strict --follow-untyped-imports
uv run pytest
uv build
```
