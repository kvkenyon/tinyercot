# tinyercot

Python client with 102 legacy typed ERCOT Public API endpoint families.

Legacy imports, signatures, and behavior stay fixed. Legacy server compatibility
is not verified. The opt-in `tinyercot.public` surface supports four current DAM,
RT-price and load endpoints, annual DAM file iteration, and the rolling website ESR
feed. The separate offline catalog records observed sources and access boundaries.

## Install

```bash
uv add tinyercot
```

## Legacy setup

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

## Opt-in public retrieval

The new client has **4 generated typed operations in 4 products out of 243
observed public data paths across 98 product namespaces**. This is partial
coverage. Unknown row schemas fail closed. Restricted services remain excluded.

```python
from datetime import date
from tinyercot.public import Credentials, PublicClient, WebClient, coverage

scopes = coverage()  # Offline; no credentials or network requests.
with PublicClient(Credentials.from_env()) as client:
    page = client.dam_prices(
        start=date(2026, 9, 4), end=date(2026, 9, 4),
        settlement_point="HB_HOUSTON", size=2,
    )
    capacity = client.dam_capacity_prices(
        start=date(2026, 9, 4), end=date(2026, 9, 4),
        ancillary_type="REGUP", size=2,
    )
    receipt = page.receipt  # Public URL, UTC retrieval time, byte count, SHA-256.

with WebClient() as client:
    snapshot = client.esr()  # Anonymous website feed, separate from Public Data API.
    stale = snapshot.is_stale()
```

Use an existing secure environment injection method for credentials. The new
client does not load `.env` or authenticate on import. It has per-instance
request and byte limits. Its errors, row models, and pagination are separate
from the legacy DataFrame and exception contracts.
See [exact coverage, annual files, evidence, and limits](docs/public-retrieval.md).

`ReportsClient` adds generated filters and streaming iteration for all four
verified endpoints. Its page, row, and request budgets can be removed explicitly
for a complete caller-selected query. Budget exhaustion raises an error.
`iter_dam_archive` similarly supports every worksheet and row in one selected
annual file. See the [complete iteration examples](docs/public-retrieval.md#complete-query-and-annual-file-iteration).

The wheel includes PEP 561 metadata and legacy transport stubs. Installed-wheel
checks verify 510 legacy methods, 1,334 row fields, and new public contracts.

## Development and legacy generation

Generation uses hash-pinned local inputs. It never fetches an upstream URL.

```bash
uv sync --frozen --group dev --extra files
uv run python tools/generate_client.py --check
uv run python tools/generate_public.py --check
uv run --extra files pytest -q
uv run ruff check tools tinyercot/catalog.py tinyercot/public tests
uv run ruff format --check tools tinyercot/catalog.py tinyercot/public tests
uv build
```

To reproduce the legacy file, run `uv run python tools/generate_client.py`.
Use `--output /tmp/legacy.py` to write a review copy. Paths do not depend on the
working directory. `--check` never writes. Missing inputs or changed hashes fail
before output is written. The former authenticated `--refresh` and
`--cache-products` developer commands are removed. Metadata refresh and current
API generation use separate inputs. `tools/generate_public.py` generates only
the registered source-backed current models from `tools/inputs/current/`. It never
downloads upstream specifications or overwrites the legacy generated file.
`tools/discover_public.py` projects additional contracts offline from saved primary
OpenAPI bytes, a bounded public response, and its matching receipt. Missing or
unknown schemas cannot be generated. CI installs the wheel outside the checkout
and runs `tools/check_typing.py --python /tmp/tinyercot-wheel/bin/python`.
