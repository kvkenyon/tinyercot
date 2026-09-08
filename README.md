# tinyercot

A small, fully typed client for ERCOT public data.

**Development status:** all 242 Public Reports endpoints have typed methods and captured-response tests. The separate ESR API is awaiting an enabled subscription key. MIS is not included.

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
    Path("prices.zip").write_bytes(
        ercot.download("np4-190-cd", [document.docId])
    )

    bundles = ercot.bundles("np4-190-cd")
    Path("monthly.zip").write_bytes(
        ercot.download("np4-190-cd", [bundles.bundles[0].docId], kind="bundle")
    )
```

Archive and bundle listings expose typed metadata. Downloads return the original
ZIP bytes. Listing metadata includes the server's total and page counts; `iter_documents()` streams all listing pages.

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
HTTP; credentials are not part of the test suite.
