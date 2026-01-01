# tinyercot

Fully-typed Python client for the ERCOT Public API.

**Why tiny?** The entire hand-written codebase is ~420 lines. Everything else is auto-generated from ERCOT's OpenAPI spec.

## Install

```bash
uv add tinyercot
```

## Setup

```bash
export ERCOT_USERNAME="your-username"
export ERCOT_PASSWORD="your-password"
export ERCOT_SUBSCRIPTION_KEY="your-subscription-key"
```

## Usage

### Single Page

```python
from datetime import date
import tinyercot

# Returns typed response with .data, .meta, .links
response = tinyercot.np4_190_cd.dam_stlmnt_pnt_prices(
    deliveryDateFrom=date(2025, 12, 29),
    settlementPoint="HB_HOUSTON",
)

# Convert to pandas DataFrame
df = response.to_df()
```

### Pagination (Sync)

```python
# Iterator - yields typed rows from all pages
for row in tinyercot.np4_190_cd.dam_stlmnt_pnt_prices_iter(
    deliveryDateFrom=date(2025, 12, 29),
):
    print(row.settlementPoint, row.settlementPointPrice)

# DataFrame - fetches all pages, returns single DataFrame
df = tinyercot.np4_190_cd.dam_stlmnt_pnt_prices_df(
    deliveryDateFrom=date(2025, 12, 29),
)
```

### Pagination (Async + Rate Limited)

Async methods automatically rate-limit to 20 req/min with retry on 429:

```python
import asyncio
import tinyercot

async def main():
    # Async iterator - rate-limited, non-blocking
    async for row in tinyercot.np4_190_cd.dam_stlmnt_pnt_prices_iter_async(
        deliveryDateFrom=date(2025, 12, 29),
    ):
        print(row.settlementPoint, row.settlementPointPrice)

    # Async DataFrame - rate-limited, non-blocking
    df = await tinyercot.np4_190_cd.dam_stlmnt_pnt_prices_df_async(
        deliveryDateFrom=date(2025, 12, 29),
    )

asyncio.run(main())
```

## API Pattern

Every endpoint generates 5 methods:

| Method | Returns | Use Case |
|--------|---------|----------|
| `endpoint()` | `Response` | Single page |
| `endpoint_iter()` | `Iterator[Row]` | Stream all pages (sync) |
| `endpoint_df()` | `DataFrame` | All pages as DataFrame (sync) |
| `endpoint_iter_async()` | `AsyncIterator[Row]` | Stream all pages (async, rate-limited) |
| `endpoint_df_async()` | `DataFrame` | All pages as DataFrame (async, rate-limited) |

## Development

Create a `.env` file with your credentials, then run IPython with dev deps:

```bash
uv run --env-file .env --group dev -- ipython
```

## Regenerate

```bash
uv run python tools/generate_client.py
```

With fresh response field data (requires credentials):

```bash
uv run --env-file .env python tools/generate_client.py --refresh
```
