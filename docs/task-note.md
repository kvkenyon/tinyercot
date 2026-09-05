# Stage 0 task note

Status: Implementation complete; direct PR handoff. Do not merge.
Base and reviewed remote main: `d1daad25df42d3fff41f88b907d99ef325b970e0`.
Branch: `feat/public-foundation`.

## Delivered scope

- Preserve the three legacy runtime files byte for byte, including 35 product
  exports, 510 methods, 204 nested models, and the base response model.
- Reproduce the legacy generator offline from a compact pinned OpenAPI
  projection and the unchanged row cache. Check hashes, ordered contracts,
  names, collisions, types, formats, missing schemas, and generated output.
  Remove the unsafe authenticated developer refresh commands.
- Add an opt-in offline catalog with 257 observed public API operations,
  including 243 data paths. Record 39 changed legacy query contracts and one
  order-only change. All current typed/raw retrieval remains unsupported.
  Forty data paths lack cached fields; 203 have unverified cached fields.
- Record selected public API/MIS/live sources, restricted Secure/Certified/EWS
  and private records, unavailable 2001 hourly load data, and unknown access.
  Package catalog data in the wheel. Include offline inputs/tests in the sdist.
- Add offline CI for Python 3.11 and 3.14, generation, tests, scoped lint/format,
  build, and installed-wheel imports/catalog use.

No ERCOT credentials were read or used. No paid data access, secret copying,
authenticated ERCOT request, historical bulk extraction, or forecaster work
occurred. Public ERCOT documentation and saved public audit metadata supplied
evidence. Tests use synthetic credentials and mocked transport only.
No no-mistakes workflow ran. No merge is authorized.

## Exact local validation

These commands passed after the final code changes:

```bash
uv sync --frozen --group dev
uv run python tools/generate_client.py --check
uv run pytest -q
UV_PROJECT_ENVIRONMENT=/tmp/tinyercot-py311 uv run --frozen --python 3.11 pytest -q
uv run ruff check tools/generate_client.py tinyercot/catalog.py tests
uv run ruff format --check tools/generate_client.py tinyercot/catalog.py tests
uv build
uv export --frozen --no-dev --no-emit-project --output-file /tmp/tinyercot-requirements.txt
uv venv /tmp/tinyercot-wheel --python 3.14
uv pip sync --python /tmp/tinyercot-wheel/bin/python /tmp/tinyercot-requirements.txt
uv pip install --python /tmp/tinyercot-wheel/bin/python --no-deps dist/tinyercot-0.2.2-py3-none-any.whl
/tmp/tinyercot-wheel/bin/python -I tests/wheel_smoke.py
git diff --check
```

Results: 873 tests passed on Python 3.14.0 and 3.11.14. The generator reproduced
SHA-256 `aaf91cb373b7557113e5343e4366e0d331566d82327ffabe4b9562937f3c2b5c`.
Scoped Ruff checks passed for nine Python files. Build produced the sdist and
wheel. The isolated installed-wheel smoke check passed with socket access
blocked. Runtime dependencies retain their prior locked versions; the lock
also corrects its stale local project version from 0.1.0 to 0.2.2.

Exploratory `uv run ruff check .` found existing `RUF013` and `DTZ011` findings in
`examples/streaming_stats.py` and `RUF100` in the frozen `tinyercot/__init__.py`.
`uv run ruff format --check .` found existing formatting in the example and
frozen `_client.py`. Scoped checks and CI exclude those unchanged files.
No unrelated runtime or example code was changed to resolve these findings.
The first test run exposed a missing order-only drift classification; it was
fixed. The first wheel omitted catalog JSON; package data was fixed and retested.

Documentation review used Google-style summaries and applicable Args, Returns,
Raises, Yields, and Attributes sections. Generated legacy documentation remains
frozen. The repository has no source license-header convention; none was
invented. No project type-check command or `py.typed` contract existed.

## Deferred gaps and blockers

No implementation blocker remains. Current row schemas still need source-backed
verification, including all missing fields and stale cached schemas. Full EMIL
metadata, current clients/status/error handling, raw transport, MIS/archive
retrieval, live polling, lifecycle metadata, bounded history, temporal/DST,
revision/as-of semantics, and installed-wheel typing remain deferred.
Restricted participant and customer records remain outside public scope.
CI results, PR URL, and commit SHA belong in the PR handoff and final task status.
