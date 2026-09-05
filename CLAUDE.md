# Repository guidance

TinyERCOT preserves its legacy public Python API. The opt-in `tinyercot.catalog`
module supplies offline metadata only. Read `docs/public-foundation.md` before
adding current data capabilities.

## Local checks

```bash
uv sync --frozen --group dev
uv run python tools/generate_client.py --check
uv run pytest -q
uv run ruff check tools/generate_client.py tinyercot/catalog.py tests
uv run ruff format --check tools/generate_client.py tinyercot/catalog.py tests
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

Do not edit the generated file manually. Keep the three legacy runtime files
unchanged for this milestone. New clients, errors, schema policies, file
adapters, and temporal behavior must use a separate opt-in surface.
Secure, Certified, EWS, and private participant/customer records are excluded.
