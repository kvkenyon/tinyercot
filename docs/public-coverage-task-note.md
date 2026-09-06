# Public Reports batch task note

This independent slice stacks on PR #4 (`feat/public-metadata-expansion`,
`dea83409ad8666545f518154e90722f1b42ff69c`). It adds 64 generated Public Reports
operations to 56, for 120 in 87 namespaces, and two anonymous dashboards.
Existing PRs remain unchanged and unmerged. ESR service/auth work and the
archive samplers delivered separately in PR #5 are excluded.

## Measured retrieval and exclusions

The [receipt index](evidence/installed-registry-index.json) records 120 attempted
paths, **118 with successful current and oldest-first typed retrieval**, and
242 typed API rows in 237 successful designated response receipts. Those
receipts comprise 119 current and 118 historical responses; the extra current
response is the prior DAM second page. This batch adds 124 successful one-row
receipts for 62 new paths. Two other generated contracts have verified source
fixtures but no successful installed retrieval:

- `/np4-442-cd/hrly_sys_reg_wind_fcast_model`
- `/np4-443-cd/hrly_sys_reg_solar_fcast_model`

Both directions returned `SourceUnavailableError` in the initial probe and
one bounded retry. All eight failed operations remain in the index. Empty
`pending_generated_paths` means no unattempted generated paths; the two above
remain in `pending_generated_both_period_paths`. Generation is not live proof.
Counts do not infer authentication requests or transport attempt totals.

The [two anonymous dashboard receipts](evidence/installed-additional-dashboard-receipts.json)
record 80 RT prices, 24 DAM prices, 289 supply/demand rows, and 144 published
outlook rows (537 total). The price capture was correctly marked stale under
the ten-minute caller policy. No fresh capture replaced that observation.
No historical files were downloaded by this slice and no annual/history
extraction ran. Prior pagination and complete two-row RT selection evidence
is retained separately; one-row samples do not establish complete history.

The other 123 observed API paths remain outside generated coverage. Unknown
schemas are untyped; NP3-763-CD has contradictory declared/observed hour-ending
types. Five API operations in two retired products are explicitly retired,
with available history a separate scope. Hourly-load 2001 remains unavailable.
Secure, Certified, participant EWS, private bids/COP/awards/telemetry,
customer data and participant settlements remain restricted.

Authorized authenticated **public** ERCOT requests occurred. No restricted
request, paid access, secret copying, bulk historical extraction, forecast
computation, merge, or no-mistakes run occurred. Offline checks never loaded
the ignored credential file.

## Validation

An initial source-tree run passed 1459 tests with one skipped and two failures
against the stale receipt index. Rebuilding the index offline resolved those
failures. Final validation used the exact staged tree, excluding the other
worker's preserved local changes:

```sh
git checkout-index --all --prefix=/tmp/tinyercot-coverage-check.lDHLK0/
cd /tmp/tinyercot-coverage-check.lDHLK0
/tmp/tinyercot-locked-wheel/bin/python -m pytest -q
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m pytest -q
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m pytest -q tests/test_discover_public.py tests/test_installed_evidence_index.py tests/test_public_coverage.py tests/test_probe_registry.py tests/test_additional_dashboards.py
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m ruff check tools tinyercot/catalog.py tinyercot/public tests
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m ruff format --check tools tinyercot/catalog.py tinyercot/public tests
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python tools/generate_client.py --check
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python tools/generate_public.py --check
uv build
```

Full results: **1450 passed, 1 skipped** on each of Python 3.11.14 and 3.14.0.
The focused suite passed **82 tests**. Ruff passed with all **66 Python files**
formatted. Both generators reproduced pinned output. Wheel and sdist built.
Public Python documentation was reviewed for Google-style Args, Returns,
Raises and Attributes, including source time and access limitations.

The wheel built from that staged tree was installed outside the repository:

```sh
uv pip install --python /tmp/tinyercot-locked-wheel/bin/python --no-deps --reinstall /tmp/tinyercot-coverage-check.lDHLK0/dist/tinyercot-0.2.2-py3-none-any.whl
uv pip install --python /tmp/tinyercot-typing-proof.fbtIin/venv/bin/python --no-deps --reinstall /tmp/tinyercot-coverage-check.lDHLK0/dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-locked-wheel/bin/python -I tests/wheel_smoke.py
/tmp/tinyercot-locked-wheel/bin/python tools/check_typing.py --python /tmp/tinyercot-locked-wheel/bin/python
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -I tests/wheel_smoke.py
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python tools/check_typing.py --python /tmp/tinyercot-typing-proof.fbtIin/venv/bin/python
```

Both installed smoke and PEP 561 proofs passed: **510 legacy methods, 1334
legacy row fields, 120 endpoint/product facades, 1143 current row fields,
2001 filters, and 128 rejected invalid uses**, plus live/archive/metadata
contracts. This is an installed-wheel proof, not a source-tree substitute.

Final repository checks:

```sh
git diff --cached --check
git diff d1daad25df42d3fff41f88b907d99ef325b970e0 -- tinyercot/__init__.py tinyercot/_client.py tinyercot/_generated.py
git check-ignore .env
git status --short
git merge-base HEAD origin/feat/public-metadata-expansion
```

Whitespace checks passed, the legacy runtime diff was empty, and `.env` was
ignored. PR base was inspected. Unrelated ESR/archive work stayed unstaged.

## Bounded receipt commands

These installed probes ran from the repository. Successful saved periods were
never repeated; the final command selected only previously failed periods.

```sh
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 52 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 72 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 92 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 112 --count 20 --attempts 1
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 88 --count 2 --retry-failures --attempts 1
uv run python tools/index_public_evidence.py --registry .local-evidence/installed-registry
```

Source URLs and hashes are pinned per contract; the reusable workflow and
[primary OpenAPI/product sources](public-metadata.md#sources-and-reproduction)
remain documented. Further bounded Public Reports discovery continues in the
next slice without waiting for merges or duplicating ESR work.
