# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tinyercot** is a fully-typed Python client for the ERCOT Public API. The entire hand-written codebase is ~230 lines—everything else is auto-generated from ERCOT's OpenAPI spec and response field definitions.

## Commands

### Development Environment

Start an IPython session with dev dependencies and environment variables:
```bash
uv run --env-file .env --group dev -- ipython
```

### Code Generation

Regenerate the client from the ERCOT OpenAPI spec:
```bash
uv run python tools/generate_client.py
```

Regenerate with fresh response field data (requires ERCOT credentials):
```bash
uv run --env-file .env python tools/generate_client.py --refresh
```

Generate a pandas-based client (returns DataFrames instead of TypedDicts):
```bash
uv run python tools/generate_client.py --pandas
```

## Architecture

### Core Components

1. **`tinyercot/_client.py`** (~58 lines)
   - OAuth 2.0 authentication with ERCOT's B2C endpoint
   - Token caching (1-hour TTL) via `cachetools`
   - HTTP client with automatic retries via `httpx-retries`
   - `_get()` function for authenticated API calls
   - `_to_df()` function for pandas DataFrame conversion with proper type coercion

2. **`tools/generate_client.py`** (~238 lines)
   - Fetches ERCOT's OpenAPI spec to extract all endpoints and parameters
   - Fetches response field schemas from ERCOT's products API (cached in `api_response_fields.json`)
   - Generates `tinyercot/_generated.py` with fully-typed classes and methods
   - Maps OpenAPI types → Python types for query parameters
   - Maps ERCOT dataTypes → Python types for response fields

3. **`tinyercot/_generated.py`** (AUTO-GENERATED)
   - One class per EMIL ID (e.g., `np4_190_cd`)
   - Each class contains methods for endpoint suffixes
   - Each method has:
     - `TypedDict` for params (query parameters)
     - `TypedDict` for response rows (individual data records)
     - `TypedDict` for full response (meta, links, data)
   - **Never edit this file manually**—always regenerate via `generate_client.py`

4. **`api_response_fields.json`**
   - Cache of response field schemas for all ERCOT endpoints
   - Maps `{emil_id}/{suffix}` → `{field_name: dataType}`
   - Regenerate with `--refresh` flag (rate-limited to 1 req/sec)

### Code Generation Flow

```
ERCOT OpenAPI Spec → parse_openapi() → endpoints + tags
                                            ↓
ERCOT Products API → fetch_response_fields() → api_response_fields.json
                                            ↓
                            generate() → tinyercot/_generated.py
```

### Type Mapping

**Query Parameters** (from OpenAPI schema):
- `string` → `str`
- `integer` → `int`
- `number` → `Decimal`
- `boolean` → `bool`
- `format: "yyyy-MM-dd"` → `datetime.date`
- `format: "yyyy-MM-ddTH24:mm:ss"` → `datetime.datetime`

**Response Fields** (from ERCOT dataType):
- `VARCHAR` → `str`
- `INTEGER` → `int`
- `DOUBLE` → `Decimal`
- `BOOLEAN` → `bool`
- `DATE` → `datetime.date`
- `DATETIME` → `datetime.datetime`
- `TIME` → `datetime.time`

## Environment Variables

Required in `.env`:
```
ERCOT_USERNAME=your-username
ERCOT_PASSWORD=your-password
ERCOT_SUBSCRIPTION_KEY=your-subscription-key
```

Pass to commands via `uv run --env-file .env`.

## Key Design Principles

1. **Minimize hand-written code**: Use code generation to reduce maintenance burden
2. **Full typing**: All responses and parameters are fully typed via `TypedDict`
3. **Smart caching**: Response fields are cached to avoid slow API calls during generation
4. **Flexible output**: Support both raw JSON (`TypedDict`) and pandas `DataFrame` outputs
