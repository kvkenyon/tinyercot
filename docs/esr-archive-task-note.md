# ESR and public archive contracts

This independent contribution starts at PR #4 commit
`11e20c84b11a38186ef1fe3e05a615de2cb8571d`. Its branch is
`feat/esr-archive-contracts`. The PR base is `feat/public-metadata-expansion`.
Firstmate authorized this review-base substitution because the requested
`feat/public-coverage-batches` was unpublished and resolved locally to the
same PR #4 head, `dea83409ad8666545f518154e90722f1b42ff69c`.
Only new assigned paths change. No shared registry, generator, package import,
dependency file, or owner branch changes.

## Result and limits

`tinyercot.public.esr_api.ESRAPIClient.current(size=1)` addresses the separate
`GET /api/public-data/rptesr-m/4_sec_esr_charging_mw` operation. It returns an
explicitly raw `RawESRPage` after envelope checks. It never claims typed ESR
rows. The source schema defines generic `Report.data` and generic fields.
The adapter retains object data or a bounded field-width-checked raw matrix.
Unknown field types remain raw. An invalid envelope fails closed.

The installed wheel reached this route but received HTTP 401, 143 bytes.
A narrow same-token diagnostic returned the source message:
"Access denied due to invalid subscription key. Make sure to provide a valid
key for an active subscription." The same token and key successfully retrieved
Public Reports. Account credentials are not globally invalid. The evidence
supports a service-specific subscription boundary. The exact account-side
subscription state remains unknown. No successful ESR current rows, oldest
ESR history, or typed ESR schema are claimed.

`tinyercot.public.archive_api.ArchiveAPIClient` reuses the pinned archive
metadata and ZIP implementation. It adds media-type checks and exact public
attempt receipts, including failed transfers. It stops after a 401 or 403.
It does not reacquire a token and replay a denied operation.

| Public operation or file | Installed result | Remaining boundary |
| --- | --- | --- |
| Public Reports root | 116 Public products, including 19 BINARY products | Root metadata alone does not verify file or row access |
| NP3-988-ER archive | 278 listed documents; document 1270779234 downloaded, HTTP 200, 22,983 bytes | Four typed DME rows verified with the existing decoder; other documents remain untested |
| NP4-190-CD bundles | 103 listed bundles | Oldest listed ID -593019152, January 2018, returns HTTP 400, 174 bytes |
| NP4-188-CD bundle | 103 bundles; August 2026 ID -1257192846 downloaded, HTTP 200, 34,664 bytes | Four typed rows from one selected nested CSV; no full-month row claim |
| Retired NP4-179-CD | 1,000 first-page documents; ID 1167729099 downloaded, HTTP 200, 1,148 bytes | Four typed offer rows for December 5, 2025; other historical schemas remain unknown |
| Retired NP3-990-EX | 1,000 first-page documents | File transfers and rows remain outstanding |
| BINARY NP4-765-ER | 1,000 first-page documents | File transfers and rows remain outstanding |

The oldest DAM bundle diagnostic used POST, `application/json`, and
`{"docIds": [-593019152]}`. ERCOT returned code 400, status BAD_REQUEST, and
a generic message that the request may be malformed or the URL may not exist.
The capacity bundle succeeded with the same construction and a negative ID.
Thus negative IDs and this JSON construction can work. The evidence does not
establish the exact cause of the older document failure or prove that its
history is unavailable. There was no alternate verb, route, or request-key
fallback.

## Source contracts and provenance

The primary operation documents specify:

- GET `/archive/{emilId}` and `/bundle/{emilId}` return `application/json`.
  They declare no query parameters. This adapter fetches the first listing
  page and preserves the source counters. Further listing pages remain an
  outstanding contract; no invented pagination query is sent.
- POST `/archive/{emilId}/download` and `/bundle/{emilId}/download` accept
  `application/json` with a required `docIds` array of int64 values and return
  `application/zip`. This adapter deliberately selects one listed document
  per transfer. Multi-document collections are documented but not implemented.
- The source documents 400, 403, and 404 JSON error responses. Runtime receipts
  also preserve unexpected statuses. Transport failure before response headers
  uses status 0. A truncated response hashes only its retained decoded prefix
  and records `complete=false`.

Source links:
[ESR operation](https://apiexplorer.ercot.com/developer/apis/esrapi-apim-api/operations/getData?api-version=2022-04-01-preview),
[archive operation](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api/operations/getProductArchives?api-version=2022-04-01-preview),
[bundle operation](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api/operations/getProductBundle?api-version=2022-04-01-preview),
[authentication documentation](https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication/).
The authentication documentation requires selection of the API product before
subscription. The ESR and Public Reports API configurations both require a
subscription. Backend service URLs from those configurations were not used.

The original `export=true` URL returned API configuration, not operation
schemas. `format=openapi` returned empty paths. Bounded direct operation and
schema GET requests supplied the usable source contracts. The fixtures retain
safe projections and source receipts. They omit example subscription headers.

- `docs/evidence/esr-archive-sources.json`: primary source identities, times,
  statuses, byte counts, SHA-256 hashes, and the empty-export boundary.
- `docs/evidence/esr-archive-installed.json`: installed network retrievals,
  public product metadata, selected document identities, exact failed-transfer
  receipts, and the same-token diagnostic. Root `file_access=outstanding`
  records the state at root retrieval; later file checks add evidence.
- `docs/evidence/esr-archive-typed-samples.json`: installed typed decoding of
  exact cached live bytes. These checks made zero network requests.
- `tests/fixtures/public/archive_api/rows.json`: two source CSV excerpts with
  original outer receipts and inner CSV hashes. Tests rebuild synthetic ZIPs.
  Synthetic ZIPs are not installed live evidence.

The new `archive_rows` module samples only two observed formats. It validates
the outer receipt and both ZIP layers. It requires exact CSV headers and row
widths. Dates and finite decimals are typed. Hour-ending and DST text remain
source values. No UTC market interval, correction priority, or full historical
schema claim is inferred. The DME check uses the existing seven-column decoder.

## Bounds and credentials

Each live run used at most 12 public-client HTTP attempts, one attempt per
operation, a 4,000,000-byte decoded response ceiling, a 30-second timeout, and
2.1-second pacing. ESR used a separate three-attempt total budget with one
attempt per operation. Successful archive and bundle transfers underwent ZIP
path, member-count, advertised expansion, and CRC checks. No files were
extracted. The new CSV samplers cap input at 4,000,000 bytes, each ZIP layer at
4,000,000 expanded bytes, and samples at 1,000 rows. Live sample proofs use four
rows. The diagnostic capped each error body at 4,096 bytes and omitted auth
headers. It retained only public error fields after checking local secrets.

The vault CLI is `/Applications/Automic Vault.app/Contents/MacOS/av`, also
available as `/usr/local/bin/av`. `av --help`, `av inject --help`, and
`av list --help` supplied CLI syntax. No unfiltered vault list was run.
The attempted three-name injection stopped because `ERCOT_PASSWORD` is not
a saved vault entry. The actual vault password and subscription key names
remain unconfirmed; the captain was asked for names only.

Live checks instead used the already authorized local vault export at
`/Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env`. Metadata checks proved
it was a regular mode-0600 file. `git -C` on that worktree with
`check-ignore -q .env` returned zero. No credential file was copied or created.
The probe reads only the three ERCOT environment names from that export.
No values, tokens, auth responses, or request headers appear in retained
evidence. No unrelated vault entry, restricted data source, EWS request,
private telemetry, paid source, or bulk history download was used.

## Commands and verification

Commands ran from this worktree unless specified otherwise:

```sh
git switch -c feat/esr-archive-contracts 11e20c84b11a38186ef1fe3e05a615de2cb8571d
uv sync --frozen --group dev --extra files
uv run python tools/generate_client.py --check
uv run python tools/generate_public.py --check
uv run pytest -q
uv run ruff check tools tinyercot/catalog.py tinyercot/public tests
uv run ruff format --check tools tinyercot/catalog.py tinyercot/public tests
uv build --quiet
uv venv /tmp/tinyercot-esr-archive-wheel
uv pip install --python /tmp/tinyercot-esr-archive-wheel/bin/python dist/tinyercot-0.2.2-py3-none-any.whl
uv pip install --python /tmp/tinyercot-esr-archive-wheel/bin/python --reinstall --no-deps dist/tinyercot-0.2.2-py3-none-any.whl
uv pip install --python /tmp/tinyercot-esr-archive-wheel/bin/python pandas-stubs
uv run python tools/check_typing.py --python /tmp/tinyercot-esr-archive-wheel/bin/python
```

Final offline result: 1,318 passed and one installed integration test skipped.
The 59 dedicated tests cover status/media failures, request and retry budgets,
response-prefix receipts, ZIP traversal, symlinks, CRC and expansion failures,
unknown/restricted access, retired BINARY file access, CSV schema drift, invalid
values, and raw ESR unknown handling. Generation, full scoped lint, and format
checks passed. The installed PEP 561 check initially needed `pandas-stubs` in
the isolated environment. It passed after that test dependency was installed.
No repository dependency changed.

Installed commands used these exact path bindings:

```sh
ESR_TASK=/Users/kevin/.treehouse/tinyercot-1bad13/2/tinyercot
ESR_PY=/tmp/tinyercot-esr-archive-wheel/bin/python
ESR_CREDS=/Users/kevin/.treehouse/tinyercot-1bad13/1/tinyercot/.env
"$ESR_PY" -I "$ESR_TASK/tools/probe_esr_archive.py" --live --credentials-file "$ESR_CREDS" --output "$ESR_TASK/.local-evidence/installed-final" --bundle-transfer
"$ESR_PY" -I "$ESR_TASK/tools/probe_esr_archive.py" --live --credentials-file "$ESR_CREDS" --output "$ESR_TASK/.local-evidence/installed-followup" --followup
"$ESR_PY" -I "$ESR_TASK/tools/probe_esr_archive.py" --sample-cache "$ESR_TASK/.local-evidence/installed-final" --output "$ESR_TASK/.local-evidence/typed-dme"
"$ESR_PY" -I "$ESR_TASK/tools/probe_esr_archive.py" --sample-cache "$ESR_TASK/.local-evidence/installed-followup" --output "$ESR_TASK/.local-evidence/typed-followup"
cd /tmp
"$ESR_TASK/.venv/bin/mypy" --strict --no-incremental --follow-imports=silent --python-executable "$ESR_PY" "$ESR_TASK/tests/fixtures/public/esr_api/typing_contract.py"
```

Direct installed-module typing passed. Installed module hashes are in the
receipts. Earlier bounded discovery and `installed-v1` checks preceded the
final run. A separate `python -I -` HTTPX diagnostic used the two exact public
requests and error-body bounds recorded in the installed evidence. It reused
the token from its successful public-root request and did not inspect tokens.

## Integration handoff and task status

Use direct imports from `tinyercot.public.esr_api`,
`tinyercot.public.archive_api`, and `tinyercot.public.archive_rows`.
No package-data registration is required for these Python modules. An optional
future shared-package export can expose `ESRAPIClient`, `RawESRPage`,
`ArchiveAPIClient`, `sample_capacity_bundle`, and `sample_retired_offers`.
The registry owner must make that change separately if desired.

Keep ESR `row_schema=unknown` and service subscription access unverified.
Keep the old DAM bundle transfer unresolved, with HTTP 400 and its document
identity. Mark the sampled capacity bundle and retired NP4-179-CD document as
supported file access with observed typed samples. Keep NP3-990-EX and other
unretrieved products outstanding. Never translate `binary-row-schema-unsupported`
or `retired-or-inactive` into unavailable history. Restricted and unknown access
classifications remain fail-closed gates, independent of retirement and format.

The contribution remains incomplete for successful ESR current retrieval.
It needs an authorized ESR-product subscription key through the local/vault
flow and actual live schema evidence. No merge or no-mistakes action ran.
The task status will record the PR URL and pushed commit after publication.
