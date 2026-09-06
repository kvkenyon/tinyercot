# Installed archive verification

Commands run on 2026-09-06 UTC from the current shared worktree unless noted:

```bash
uv build
uv pip install --python /tmp/tinyercot-retrieval-wheel/bin/python --force-reinstall 'dist/tinyercot-0.2.2-py3-none-any.whl[files]'
```

Both passed. The probe ran with `/tmp` as its working directory:

```bash
/tmp/tinyercot-retrieval-wheel/bin/python -I /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/tools/probe_api_archives.py --live --credentials-file /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env --evidence /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/catalog --output /Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.local-evidence/installed-api-archives --retired-history --download-oldest-bundle
```

Required checks passed with Python 3.14 from installed `site-packages`:
116 root products; 278 DME documents; four typed exact-text rows per current and
oldest cached DME ZIP; 103 DAM bundles; two first-page public retired-history
listings. The optional oldest-bundle transfer returned `SourceUnavailableError`;
its exact HTTP status was not retained. No bundle download or typed bundle rows
are claimed. Original DME ZIPs were not downloaded again. Source receipts and
selected document identities are checked in separately from ignored raw files.

```bash
uv run --extra files pytest -q tests/test_probe_api_archives.py tests/test_api_archives.py tests/test_api_bundles.py tests/test_resource_dme.py tests/test_rt_archives.py
uv run ruff check tools/probe_api_archives.py tests/test_probe_api_archives.py
uv run ruff format --check tools/probe_api_archives.py tests/test_probe_api_archives.py
```

The test command passed **48 tests**. Lint and format checks passed after the
test import grouping was corrected. No legacy runtime files, exports, coverage
records, secrets, or credential contents were edited or copied in this subtask.
No commit, push, merge, or no-mistakes action was performed.
