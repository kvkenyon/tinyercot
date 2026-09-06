# Current iteration and typing task note

Status: Implementation and local checks complete on feat/public-rt-load, stacked
on PR #2 at 01d8b69c4378040ca14d9683e9693e65cc3f93a8. PR #1 and #2 remain open
and unmerged. The new installed-client proof establishes 4/243 typed paths in
4/98 observed product namespaces. Direct PR handoff follows these checks.

Active scope from inbox 005: reusable schema discovery/generation; complete
filtered API page/row iteration; full worksheet/row iteration for one requested
public annual file; and package-wide static typing with installed-wheel proof.
Real validation stays bounded. Synthetic fixtures prove long iteration without
extracting real bulk history. Legacy runtime files stay byte-identical.

## NumPy audit (inbox 006)

`git show d1daad25df42d3fff41f88b907d99ef325b970e0:uv.lock` already pins NumPy
2.4.0 (line 212). PR #1 and #2 retain that pin. This work did not introduce it.
The pre-correction local environment used NumPy 2.4.0 with pandas 2.3.3. PR #2's
941 tests passed on Python 3.11 and 3.14 with that locked dependency set.

[PyPI's 2.4.0 metadata](https://pypi.org/pypi/numpy/2.4.0/json) reports all 72
release files yanked for "Backward compatibility bug". The corresponding
[2.4.1 metadata](https://pypi.org/pypi/numpy/2.4.1/json) reports 72 non-yanked
files and the same Python >=3.11 requirement. Both were checked on 2026-09-05.

The narrow correction is `uv lock --upgrade-package numpy==2.4.1`. This changes
the locked NumPy patch release only. It does not add a new runtime dependency
constraint or broadly upgrade runtime packages. New mypy/pandas-stubs packages
are development tooling for the requested static typing proof. Normal package
installs were not pinned to the yanked version; the repository lock was.
The corrected lock passes the full suite on Python 3.11.14 and 3.14.0 with
NumPy 2.4.1/pandas 2.3.3. Isolated wheel installs also pass import, nonempty
legacy DataFrame conversion, mocked typed RT decoding, and PEP 561 checks with
Python 3.11.14/NumPy 1.24.0/pandas 2.0.0/Pydantic 2.10.0 and Python 3.14.0/
NumPy 2.5.2/pandas 3.0.5/Pydantic 2.13.5. These are practical boundary samples,
not an exhaustive dependency Cartesian product. No runtime dependency constraint
changed. Only NumPy changed among pre-existing locked runtime package versions.

## Delivered scope and evidence

- Shared offline schema projection from the hash-pinned primary Public Reports
  OpenAPI export and exact public response/receipt pairs. Missing, null-only,
  mistyped, and unknown schema evidence cannot become a typed adapter. Generation
  rejects unsupported formats, conflicting names, missing status, and pin drift.
- Registered row models, TypedDict filters, and endpoint constants for DAM
  settlement and capacity prices, RT settlement prices, and weather-zone load.
  `ReportsClient` supports every pinned query filter and streams pages/rows with
  configurable total budgets, bounded response memory, and consistency checks.
- `iter_dam_archive` visits all requested worksheets/rows of one public annual
  report-13060 ZIP, retaining member/sheet/row/hash provenance. Existing sampling
  defaults remain intact. Synthetic tests exhaust 2,010 rows across two sheets;
  API tests exhaust 125 pages without network access.
- PEP 561 marker and companion legacy stubs. The real installed-wheel proof
  checks all 510 legacy methods, all 1,334 row fields, public typed filters and
  adapters, and four rejected invalid uses. Assertions run from a temporary
  directory with PYTHONPATH/MYPYPATH removed and a separate installed interpreter.
  No source-tree substitute or ignore-missing-imports fallback is used.
- All 39 audited families, 257 API operations, and two web subsets retain
  explicit scope states. Four API operations and the two narrow web subsets are
  covered; no broad source family is marked complete. The other 239 data paths,
  API archive/bundle routes, additional MIS/live formats, async current clients,
  schema epochs, historical completeness, and as-of/revision reconstruction
  remain deferred. Secure/Certified/EWS/private records remain restricted;
  retired AS/SASM and the missing 2001 load year remain unavailable.

On 2026-09-06 at 00:11 UTC the actual installed wheel made six bounded public
data requests: two current rows and one oldest-first row for each new endpoint,
plus two one-row pages for a complete filtered RT selection. Both oldest rows
were dated 2023-12-11. Receipts are in
`docs/evidence/installed-reports-receipts.json`; source fixtures and transformations
are in `docs/evidence/fixture-provenance.json`. Prior installed DAM, annual-file,
and ESR evidence is preserved in `docs/evidence/installed-receipts.json`.

Inbox 001 explicitly authorized existing Public API credentials for these public
requests, superseding the initial audit's unauthenticated-only validation scope.
Authorized authentication occurred; no restricted request, secret copying, paid
access, all-history extraction, forecaster work, no-mistakes, or merge occurred.
The local `.env` remains ignored and mode 0600. No values were printed or committed.

## Exact local validation

Commands ran from the repository root unless an isolated interpreter is shown.

```text
uv sync --frozen --group dev --extra files
uv run --extra files pytest -q
  976 passed, 1 skipped (Python 3.14.0; network blocked)
UV_PROJECT_ENVIRONMENT=/tmp/tinyercot-py311 uv sync --python 3.11 --frozen --group dev --extra files
/tmp/tinyercot-py311/bin/python -m pytest -q
  976 passed, 1 skipped (Python 3.11.14; network blocked)
uv run python tools/generate_client.py --check
  Legacy generation matches the pinned baseline
uv run python tools/generate_public.py --check
  Current models match pinned response metadata
uv run ruff check tools tinyercot/catalog.py tinyercot/public tests
  All checks passed
uv run ruff format --check tools tinyercot/catalog.py tinyercot/public tests
  36 files already formatted
uv build
  Built wheel and sdist; log /tmp/tinyercot-iteration-build.log
uv pip install --python /tmp/tinyercot-retrieval-wheel/bin/python --no-deps --reinstall dist/tinyercot-0.2.2-py3-none-any.whl
uv pip install --python /tmp/tinyercot-lower-wheel/bin/python --no-deps --reinstall dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-retrieval-wheel/bin/python -I tests/wheel_smoke.py
/tmp/tinyercot-lower-wheel/bin/python -I tests/wheel_smoke.py
  Both passed imports, legacy DataFrame conversion and mocked typed RT decoding
uv run python tools/check_typing.py --python /tmp/tinyercot-retrieval-wheel/bin/python
uv run python tools/check_typing.py --python /tmp/tinyercot-lower-wheel/bin/python
  Both passed: 510 methods, 1334 fields, public contracts, four invalid uses rejected
/tmp/tinyercot-retrieval-wheel/bin/python -I tools/probe_public.py --live --reports-only --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-reports
  Six bounded public data requests passed; eight total rows; no archive download
git diff d1daad25df42d3fff41f88b907d99ef325b970e0 -- tinyercot/__init__.py tinyercot/_client.py tinyercot/_generated.py
  Empty: all three legacy runtime files remain byte-identical
git diff --check
  Passed
```

Lower-install preparation used `uv venv --python 3.11 /tmp/tinyercot-lower-wheel`
and `uv pip install --python /tmp/tinyercot-lower-wheel/bin/python 'pandas==2.0.0'
'numpy==1.24.0' 'pydantic==2.10.0' 'tinyercot[files] @
file:///Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/dist/tinyercot-0.2.2-py3-none-any.whl'`.
The type consumer additionally installed `pandas-stubs==3.0.5.260730 --no-deps`.
CI now exports locked development typing dependencies, installs a separate wheel,
and runs the same proof on Python 3.11 and 3.14 without ERCOT credentials.
The CI preparation was also reproduced locally and passed:

```text
uv export --frozen --no-emit-project --output-file /tmp/tinyercot-iteration-requirements.txt
uv venv --python 3.11 /tmp/tinyercot-locked-wheel
uv pip sync --python /tmp/tinyercot-locked-wheel/bin/python /tmp/tinyercot-iteration-requirements.txt
uv pip install --python /tmp/tinyercot-locked-wheel/bin/python --no-deps dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-locked-wheel/bin/python -I tests/wheel_smoke.py
uv run python tools/check_typing.py --python /tmp/tinyercot-locked-wheel/bin/python
  Both installed-wheel checks passed with the corrected frozen dependency set
```

Documentation review: authored public functions document applicable Args,
Returns/Yields, and caller-visible Raises in Google style; generated models
describe source fields. Test helpers follow existing test conventions. The
repository has no approved per-file license boilerplate; none was invented.
The resumed proof initially failed because generated assertions used unqualified
nested model names; the proof was corrected, preserving legacy runtime bytes.
The initial full test run exposed missing fixture provenance; that evidence is
now included. Neither failure was suppressed.
