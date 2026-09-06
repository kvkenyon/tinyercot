# Metadata expansion task note

PR #4 stacks on `feat/public-rt-load` at
`12d60654632ce5c47543ef5f3410ec55972c8471`. It adds 52 generated operations,
bringing typed installed-client retrieval to 56 unique paths of 243 observed
public data paths. The other 187 paths remain active work. The stable public
entry point is `products.<product>.<operation>`; existing imports and the three
legacy runtime files remain unchanged.

The exact machine-readable index is
`docs/evidence/installed-registry-index.json`: 57 current requests across 56
paths, 56 oldest-first requests across 56 paths. The extra current request is
an earlier DAM second page. Pagination is separate: two paths have live
multiple-page evidence; one RT selection completed two pages/two rows. The
new 52-path batch contributes no pagination or completeness claim. No full
history or complete annual file was extracted.

Additional bounded scopes are metadata root/archive/bundle listings, four
anonymous rolling dashboards, RT annual listing/cached 2010 and 2026 decoding,
and current/oldest DME CSV decoding from captured ZIPs. Public retired-product
listings are available. One monthly bundle transfer was unsuccessful, so no
successful bundle download is claimed. Public BINARY documents and available
retired history remain active work. Secure, Certified, EWS, private participant
records and customer data stay restricted; hourly-load 2001 stays unavailable.
Authorized public authentication occurred; no restricted requests, paid access,
secret copying, forecaster computation, or bulk historical extraction occurred.

## Local checks

These working-tree commands passed:

```sh
uv run python tools/generate_client.py --check
uv run python tools/generate_public.py --check
uv run --extra files pytest -q
uv build
uv pip install --python /tmp/tinyercot-typing-proof.fbtIin/venv/bin/python --no-deps --reinstall dist/tinyercot-0.2.2-py3-none-any.whl
uv run python tools/check_typing.py --python /tmp/tinyercot-typing-proof.fbtIin/venv/bin/python
git diff --cached --check
git diff d1daad25df42d3fff41f88b907d99ef325b970e0 -- tinyercot/__init__.py tinyercot/_client.py tinyercot/_generated.py
git check-ignore .env
```

The full suite returned **1259 passed, 1 skipped** on Python 3.14.0. The
installed PEP 561 proof verified 510 legacy methods, 1334 legacy row fields,
56 current endpoint/product facades, 498 current row fields, 847 filter fields,
live/archive/metadata contracts, and rejection of 64 invalid uses. The legacy
diff was empty. The credential file was ignored; its contents were never read
by offline validation or included in Git.

Concurrent PR #5 work added untracked fixtures while checking the second
interpreter, causing an expected fixture-inventory mismatch. Final checks used
an exact copy of the staged PR #4 files, preserving that ongoing work:

```sh
git checkout-index --all --prefix=/tmp/tinyercot-pr4-check.fjDuNo/
cd /tmp/tinyercot-pr4-check.fjDuNo
/tmp/tinyercot-locked-wheel/bin/python -m pytest -q
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m pytest -q
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m ruff check tools tinyercot/catalog.py tinyercot/public tests
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -m ruff format --check tools tinyercot/catalog.py tinyercot/public tests
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python tools/generate_client.py --check
/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python tools/generate_public.py --check
```

Both interpreter suites passed **1259 tests, 1 skipped** (Python 3.11.14 and
3.14.0); Ruff lint passed and all 62 Python files were formatted. Both
generators matched their pinned outputs. Both separate test environments
needed the optional decoder installed first with
`uv pip install --python /tmp/tinyercot-locked-wheel/bin/python openpyxl==3.1.5`
and `uv pip install --python /tmp/tinyercot-typing-proof.fbtIin/venv/bin/python openpyxl==3.1.5`.
Google-style public docstrings document access, lifecycle, source times,
iteration, and failure contracts. Generated documentation follows the same
existing model conventions; no project license-header convention was invented.

## Bounded installed evidence commands

The three authenticated registry calls used an isolated installed wheel:

```sh
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 0 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 20 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_registry.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-registry --start 40 --count 20
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_dashboards.py --live --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-dashboards.json
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_aggregate_dashboards.py --live --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-aggregate-dashboards.json
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_rt_archives.py --live --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-rt-archives --source-evidence /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence
uv run python tools/index_public_evidence.py --registry .local-evidence/installed-registry
```

All required checks passed; receipts were indexed without repeating live calls.
[The archive task note](api-archive-installed-task-note.md) records its exact
commands and the optional bundle failure. No merge or no-mistakes action ran.
The next renewable/load/RUC batch already has source samples, and further
Public Reports disclosure discovery is active. Subsequent stacked PRs continue
the public/history objective without waiting for earlier merges.

## CI smoke correction

The first CI run passed generation, tests, lint, formatting and build, then
caught stale fixed coverage counts in `tests/wheel_smoke.py`, a standalone
script outside pytest discovery. The script now reconciles installed data-path
coverage with the installed registry and checks the new product facade.
`uv run ruff check tests/wheel_smoke.py` passed; both
`/tmp/tinyercot-typing-proof.fbtIin/venv/bin/python -I tests/wheel_smoke.py` and
`/tmp/tinyercot-locked-wheel/bin/python -I tests/wheel_smoke.py` passed using
installed wheels. This correction changes only validation and documentation.
