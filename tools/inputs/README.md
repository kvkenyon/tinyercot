# Generator inputs and test fixtures

Keep these files versioned with the code so a checkout can generate and test the
client offline, without ERCOT credentials or a separately initialized submodule.

- `operations.json` and the root `api_response_fields.json` describe the API used
  by the generator. Overrides and field mappings record deliberate corrections.
- `samples/` contains captured report responses, exercised against every generated
  endpoint's typed row model and mocked HTTP retrieval.
- `dashboards/` and catalog/archive/bundle samples exercise public dashboard and
  metadata models, pagination and download requests.
- On the history branch, `history-formats.json` supplies generated reader mappings;
  `history/` contains CSV, workbook, PDF and ZIP regression fixtures. Evidence files
  record source URLs, observed periods and comparisons; some also parameterize tests.

Fixtures and generator inputs belong in the source archive. The installed wheel
contains only the `tinyercot` package, typing marker and distribution metadata.
Neither tests nor downloads from these directories are needed at runtime.

Captured responses and generated Python are marked in `.gitattributes` so GitHub
collapses their diffs by default. Hand-maintained mappings, overrides and evidence
remain visible. Preserve original source bytes for binary fixtures; add examples
when a new layout or behavior needs a regression test, rather than refreshing
snapshots on every live check. For large repetitive profile files,
`history/generation-profiles.zip` retains original CSV rows and workbook XML cells
for first/last dates, leap day and daylight-saving transitions in representative
files, plus initial rows from each additional workbook. These are explicitly
derived samples, not full original downloads; XLSX metadata and retained cells are
unchanged. `public-profile-fixtures.json` records source and sample hashes and row
counts. Full-source comparisons are recorded separately in the profile evidence.
Do not store credentials or private responses here.
