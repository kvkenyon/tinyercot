# Repository guidance

TinyERCOT preserves its legacy public Python API. The opt-in `tinyercot.catalog`
module supplies offline metadata only. Read `docs/public-foundation.md` before
adding current data capabilities. Read `docs/public-retrieval.md` for the opt-in
two-endpoint API client, annual file adapter, and ESR website feed.

## Local checks

```bash
uv sync --frozen --group dev --extra files
uv run python tools/generate_client.py --check
uv run python tools/generate_public.py --check
uv run --extra files pytest -q
uv run ruff check tools/generate_client.py tools/generate_public.py tools/probe_public.py tinyercot/catalog.py tinyercot/public tests
uv run ruff format --check tools/generate_client.py tools/generate_public.py tools/probe_public.py tinyercot/catalog.py tinyercot/public tests
uv build
```

Tests use synthetic credentials and mocked transport. Do not load `.env` for
these checks. The generator uses pinned local inputs and needs no credentials.
It has no `--refresh`, `--cache-products`, or `--pandas` option.

## Architecture and compatibility

- `tinyercot/_client.py` contains the legacy auth, transport, and `ErcotResponse`.
- `tinyercot/_generated.py` contains 35 product classes and 102 endpoint families.
  Each family has Pydantic Row and Response models plus five static methods.
- `tools/generate_client.py` reproduces the generated file from pinned inputs.
  Use `--check` for a comparison or `--output /tmp/legacy.py` for a review copy.
- `api_response_fields.json` is the frozen legacy field cache. It does not verify
  current schemas. `products.json` is historical evidence, not a generation input.
- `tinyercot/catalog.py` reads bundled public metadata without data requests.
- `tinyercot/public/` contains opt-in clients and separate errors and row models.
- `tools/generate_public.py` generates current models from pinned response fields.
  New endpoints need actual field evidence. Cached legacy rows do not qualify.

Real integration tests require explicit opt-in paths and an installed wheel.
The normal suite blocks sockets and skips them. Do not print credential files,
auth responses, tokens, or HTTPX request objects from real requests.

Do not edit the generated file manually. Keep the three legacy runtime files
unchanged for this milestone. New clients, errors, schema policies, file
adapters, and temporal behavior must use a separate opt-in surface.
Secure, Certified, EWS, and private participant/customer records are excluded.
