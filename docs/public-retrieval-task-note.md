# Public retrieval task note

Status: Bounded retrieval milestone complete; direct stacked PR handoff.
Do not merge this PR or foundation PR #1.

Branch: `feat/public-retrieval`.
PR base: `feat/public-foundation`, commit
`4b26c8a91efbba668dbbc40f564bbe812d4ae792`.
Remote main remains audit base `d1daad25df42d3fff41f88b907d99ef325b970e0`.

## Scope

The captain's later inbox instruction authorized real Public API access through
a local vault export. This supersedes the original Stage-0 public-metadata-only
stopping point. Stage-0 evidence remains in `docs/task-note.md` and PR #1.

- Add opt-in `PublicClient` with two generated models: NP4-190-CD DAM settlement
  prices and NP4-188-CD DAM capacity clearing prices. Generate offline from
  hash-pinned, observed response fields. Reject unknown fields and null rows.
- Add bounded pagination for DAM settlement prices, explicit credentials,
  synchronized ID-token acquisition and expiry margin, one 401 reacquisition,
  safe errors, pacing, retry and response/request ceilings.
- Add anonymous `WebClient` for public report-13060 annual ZIP/XLSX samples and
  the rolling website ESR feed. Require a receipt cache for annual downloads.
  Keep source publication, retrieval time, local market fields, and hashes.
- Add all 39 audited family boundaries and all 257 observed API operation
  states to opt-in `coverage()`. Two API paths and two website subsets are
  covered within their stated limits. No entire broad family is marked covered.
- Keep all three legacy runtime files unchanged. Existing imports, defaults,
  signatures, exceptions, pagination, and DataFrame behavior stay fixed.

Generated typed coverage is **2 operations in 2 products out of 243 observed
data paths across 98 product namespaces**. The other 241 data paths remain
deferred. Stage 0 recorded 40 missing and 203 unverified cached row schemas.
Current evidence verifies only these two endpoints. The website ESR adapter
does not implement the separate four-second Public Data API.

## Real evidence

An isolated installed wheel passed real current and historical API fetches for
both generated models. Current selections used 2026-09-04, HB_HOUSTON or REGUP,
and at most two rows per page. Both oldest-first selections returned one row
dated 2023-12-13. These are observations, not complete-retention guarantees.
Two DAM pages and a fetch after explicit token reacquisition passed.

The installed client decoded 482 ESR observations with time/freshness checks.
It listed 17 public annual files, selected only 2010 and 2026, and decoded four
rows from Dec_1 and Aug respectively. Cache reuse passed. Each annual file was
downloaded once during source discovery and once by the installed adapter.
Later installed probes used the cache for both files. No all-history or
all-sheet extraction ran. Public receipts and fixture provenance are in
`docs/evidence/`. The evidence-class table and all source families are in
`docs/public-retrieval.md`.

Real authorized ERCOT authentication occurred. Credential and token values
were not printed or retained in evidence, source, tests, commits, or PR text.
The vault-created local `.env` is ignored and mode 0600. No restricted request,
paid access, bulk history, forecaster work, no-mistakes run, or merge occurred.

## Exact local validation

The following final checks passed:

```bash
uv run python tools/generate_client.py --check
uv run python tools/generate_public.py --check
uv run --extra files pytest -q
UV_PROJECT_ENVIRONMENT=/tmp/tinyercot-py311 uv run --frozen --python 3.11 --extra files pytest -q
uv run ruff check tools/generate_client.py tools/generate_public.py tools/probe_public.py tinyercot/catalog.py tinyercot/public tests
uv run ruff format --check tools/generate_client.py tools/generate_public.py tools/probe_public.py tinyercot/catalog.py tinyercot/public tests
uv build
uv export --frozen --no-dev --no-emit-project --output-file /tmp/tinyercot-requirements.txt
uv pip sync --python /tmp/tinyercot-wheel/bin/python /tmp/tinyercot-requirements.txt
uv pip install --python /tmp/tinyercot-wheel/bin/python --no-deps dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-wheel/bin/python -I tests/wheel_smoke.py
git diff --check
```

Results: **941 passed, 1 skipped** on Python 3.14.0 and 3.11.14. The skipped
integration entry point requires explicit environment opt-in. All normal tests
block sockets. Ruff checked 26 authored Python files. Both generators reproduced
their pinned output. The built wheel passed isolated imports and metadata use
with sockets blocked and without the optional XLSX dependency. The source and
wheel archives exclude the local credential file and bulk source files.

Real installed-client commands, run separately from the offline suite:

```bash
uv venv /tmp/tinyercot-retrieval-wheel
uv pip install --python /tmp/tinyercot-retrieval-wheel/bin/python 'dist/tinyercot-0.2.2-py3-none-any.whl[files]'
uv pip install --python /tmp/tinyercot-retrieval-wheel/bin/python --reinstall --no-deps dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-retrieval-wheel/bin/python -I tests/wheel_smoke.py
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_public.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed
```

Google-style documentation review covered authored Python summaries, Args,
Returns, Raises, Yields, and Attributes sections. The repository has no static
type-check command or PEP 561 contract. Existing unrelated example/frozen-file
Ruff findings remain excluded, as recorded in Stage 0. No unrelated work was
discarded or reformatted. CI runs offline on Python 3.11 and 3.14.
Diff review found that an interrupted HTTP-200 token body did not enter the
transport retry path. The fix and a mocked partial-token regression test pass.

## Deferred and excluded

No implementation blocker remains for this bounded milestone. The 241 other
data paths, generic API archive/bundle operations, other MIS products, rolling
feeds, schema epochs, all-filter contracts, as-of revisions, full history,
automatic polling, async retrieval, and package-wide static typing are deferred.
The 39-family table marks 33 deferred public/conditional boundaries, three
restricted families, and three unavailable gaps. Secure, Certified, participant
EWS, private telemetry/bids/COP/awards, settlements, and customer data remain
excluded. Retired AS-offer/SASM sources and hourly load 2001 remain unavailable.
