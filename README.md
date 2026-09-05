# tinyercot

Python client with 102 legacy typed ERCOT Public API endpoint families.

Legacy imports, signatures, and behavior stay fixed. Current server compatibility
is not verified. The opt-in offline catalog describes observed public sources
and access boundaries; it adds no data retrieval.

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

## Offline public catalog

```python
from tinyercot.catalog import Access, classify_access, operations, sources

# No credentials or network requests are needed for this metadata.
observed = operations(service="public-reports")
assert len(observed) == 249  # 242 data paths and 7 service operations.
assert all(op.support == "metadata_only" for op in observed)
assert classify_access("Certified") is Access.RESTRICTED
boundaries = sources()
```

The 2026-09-05 snapshot records 243 public data paths across two APIs.
It does not claim typed current coverage. Forty paths lack cached row fields;
all other cached rows remain unverified against current responses.
Secure, Certified, EWS, private participant records, and customer data are
restricted and excluded. Public API data requests still need an ERCOT account.
See [scope, provenance, and adapter boundaries](docs/public-foundation.md).

## Development and legacy generation

Generation uses hash-pinned local inputs. It never fetches an upstream URL.

```bash
uv sync --frozen --group dev
uv run python tools/generate_client.py --check
uv run pytest -q
uv run ruff check tools/generate_client.py tinyercot/catalog.py tests
uv run ruff format --check tools/generate_client.py tinyercot/catalog.py tests
uv build
```

To reproduce the legacy file, run `uv run python tools/generate_client.py`.
Use `--output /tmp/legacy.py` to write a review copy. Paths do not depend on the
working directory. `--check` never writes. Missing inputs or changed hashes fail
before output is written. The former authenticated `--refresh` and
`--cache-products` developer commands are removed. Metadata refresh and current
API generation need a separate reviewed tool; neither is part of this milestone.
