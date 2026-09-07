# tinyercot

Keep the SDK small and fully typed. Product methods and row models are generated;
handwritten code handles shared transport, typed metadata, and public dashboards.

- `tinyercot/_client.py`: authentication, sync/async retrieval, pagination, metadata, ZIP downloads.
- `tinyercot/_history.py`: shared typed CSV and nested ZIP readers. Verified mappings live in `tools/inputs/history-formats.json`.
- `tinyercot/_generated.py`: generated typed product namespaces; never edit manually.
- `tinyercot/_dashboards.py`: typed public dashboard payloads and retrieval.
- `tools/generate_client.py`: offline generation from `tools/inputs/operations.json`
  and `api_response_fields.json`.
- `tools/inputs/*overrides.json`, `query-defaults.json`, `row-fields.json`: narrowly
  documented corrections to ERCOT's inconsistent contracts.
- `tests`: captured public responses, mocked transport, and static typing checks.

Run `uv run python tools/generate_client.py`, `uv run pytest`,
`uv run mypy tinyercot tests/typing_client.py --strict --follow-untyped-imports`,
`uv run ruff check .`, and `uv build`.

No credentials are needed for imports, generation, or normal tests. Live API use
accepts constructor credentials or `ERCOT_USERNAME`, `ERCOT_PASSWORD`, and
`ERCOT_SUBSCRIPTION_KEY`. Never commit credentials. MIS is outside the current scope.
