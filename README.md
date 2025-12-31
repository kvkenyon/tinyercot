# tinyercot

Fully-typed Python client for the ERCOT Public API.

**Why tiny?** The entire hand-written codebase is ~230 lines. Everything else is auto-generated from ERCOT's OpenAPI spec.

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

```python
from datetime import date
from tinyercot import np4_190_cd

data = np4_190_cd.dam_stlmnt_pnt_prices(
    deliveryDateFrom=date(2025, 12, 29),
    settlementPoint="HB_NORTH",
)
```

## Development

Create a `.env` file with your credentials, then run IPython with dev deps:

```bash
uv run --env-file .env --group dev -- ipython
```

## Regenerate

```bash
uv run python tools/generate_client.py
```
