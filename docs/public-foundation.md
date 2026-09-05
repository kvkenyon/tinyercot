# Public data foundation

This milestone freezes the Python contract at
`d1daad25df42d3fff41f88b907d99ef325b970e0`. It adds offline metadata under
`tinyercot.catalog`. It adds no current data client, raw fetch, MIS download,
archive adapter, live polling, authentication flow, or historical backfill.
No authenticated ERCOT request or historical bulk extraction occurred.

## Compatibility boundary

`tinyercot/__init__.py`, `_client.py`, and `_generated.py` keep their exact base
bytes. The 35 product exports, `configure`, 510 method signatures, 102 Row models,
102 Response models, and base envelope remain fixed. Numeric suffixes retain
their leading underscores. Tests check function categories, module and nested
model identities, field order, requiredness, aliases, defaults, model settings,
and JSON schema digests. The fixture was checked against the independent audit.

All 102 method families have mocked sync/async path, filter, pagination, and
DataFrame tests. Other tests preserve exception propagation, token cache rules,
None filter omission, cached positional field order, extra-value truncation,
missing-page-count behavior, and DataFrame dtypes. A JSON 401 still produces an
empty legacy response. This is a compatibility test, not the intended policy
for a future client. Legacy token and DataFrame behavior is unchanged.

Python compatibility cannot undo a server-side change. The audit found 39
changed legacy query contracts and one order-only change. The new catalog
records these states separately. None of the 102 legacy paths establishes
successful current decoding. Retirement does not remove Python symbols.

## Pinned inputs

`tools/inputs/legacy-provenance.json` records source URL, capture time, original
source SHA-256, projected input SHA-256, cache SHA-256, and output SHA-256.
The original OpenAPI export is ERCOT's
[legacy GitHub specification](https://raw.githubusercontent.com/ercot/api-specs/main/pubapi/pubapi-apim-api.json),
captured on 2026-09-05. The URL is provenance, not a generator input.
The original file hash identifies its content even though the URL moves.
Its version label is `1.0`; that label does not identify a revision.
No upstream Git revision was established, so the manifest stores null.

`legacy-openapi.json` is a compact projection, with one path per line.
It retains `openapi`, `info.version`, `tags`, and data GET summaries and query
parameter `name`, `in`, and `schema`, in source order. It excludes root, version,
and templated paths. It omits unused response examples and repeated envelope
definitions. The generator reads no network resource and imports no HTTP client.

The existing `api_response_fields.json` remains unchanged. It is evidence for
legacy reproduction only. Its original capture time, current field nullability,
and current schema validity are unknown. It must not authorize current typed
models. Generation checks exact pinned metadata, ordered fields and queries,
valid Python names, member collisions, supported legacy types/formats, and the
final output digest. It cannot emit an empty Row model from missing evidence.
Unknown formats and response types fail. The old `mm:ss` string policy remains
explicit. Changed inputs need a separate reviewed contract; editing the moving
URL or refreshing this cache cannot upgrade the legacy API.

`tests/fixtures/legacy-contract.json` stores all method identities and signature
digests, ordered field essentials, model identities/settings, and full JSON
schema digests. Signature digests hash `str(inspect.signature(function))`.
Schema digests hash UTF-8 JSON with sorted keys and compact separators.
This avoids repeating each long signature five times and nested schemas in
every response. The source projection and legacy code retain readable contracts.
The locked Pydantic version defines the baseline schema serialization.

Do not update these pins to accept unexplained drift. A later refresh tool must
write separate candidate metadata with source hashes, explicit validation, and
bounded requests. It must not overwrite a valid cache after a failed request.
The legacy generator deliberately has no refresh command.

## Offline catalog contract

`operations()` returns immutable observations of 257 operations: 249 under
`public-reports` and eight under `public-data` (ESR). Of these, 242 and one,
respectively, are data GET paths. Each API also has seven generic operations,
including separate archive and bundle POST downloads. The catalog preserves
verbs and request/success media types. It does not implement request bodies,
path substitution, pagination, decoding, or transport.

The catalog derives from the public ERCOT
[Public Reports export](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview)
and [ESR export](https://apiexplorer.ercot.com/developer/apis/esrapi-apim-api?export=true&api-version=2022-04-01-preview).
`tools/inputs/public-provenance.json` records their capture times and hashes,
the catalog hash, audit input hashes, and the projection recipe. These are audit
observations from 2026-09-05, not a rolling inventory. The date does not establish
publication time, first available history, or present source availability.

Every operation has `support="metadata_only"`. `legacy_path` means only that a
legacy method exposes that path. For data endpoints, `row_schema` is either
`cached_unverified` (203 paths) or `missing` (40 paths). Generic operations use
`not_applicable` because they do not describe data rows. **No state grants typed
or raw current retrieval.** `query_drift` is `contract`, `order_only`, `unchanged`,
or None when no legacy comparison applies.

`sources()` returns eight selected delivery and access boundaries. It is not the
full EMIL catalog. `classify_access()` recognizes only Public, Secure, and
Certified labels, ignoring case and surrounding whitespace. Unknown, absent,
and conflicting labels remain unknown. Active and Greybox do not establish
public access. `Access.UNAVAILABLE` records explicit source unavailability,
such as the [2001 hourly load gap](https://www.ercot.com/gridinfo/load/load_hist).

Public does not mean anonymous API access. ERCOT's
[authentication guide](https://developer.ercot.com/applications/pubapi/user-guide/registration-and-authentication/)
requires an account, ID token, and subscription key for API data requests.
Offline metadata does not read credentials, authenticate, or make requests.
Restricted entries describe exclusions; they do not route through public auth.
These include [Secure network products](https://www.ercot.com/mp/data-products/data-product-details?id=np4-500-sg),
[Certified settlements](https://www.ercot.com/mp/data-products/data-product-details?id=np9-170-sg),
and [EWS participant services](https://developer.ercot.com/applications/ews/Services%20Organization/).
Private telemetry, bids, COP, awards, settlements, and customer records remain
excluded. Public aggregates and delayed disclosures are separate products.

## Additive adapter path and deferred evidence

A future current API client needs a separate opt-in namespace and runtime.
It must bind current query and source-backed response contracts together.
All current row schemas still need validation; missing ones stay unsupported.
It must add status checks and error types without changing legacy exceptions.

MIS/archive and live sources need separate adapters. The selected public
[MIS price archive](https://www.ercot.com/mp/data-products/data-product-details?id=np4-180-er)
and [dashboard](https://www.ercot.com/gridmktinfo/dashboards) references identify
delivery paths only. Listing years do not prove complete interval history.
Rolling feeds do not establish historical access. File receipts, bounded
transfers, archive validation, temporal/DST rules, freshness, and revision/as-of
semantics are deferred. No adapters or placeholder clients are added here.

Full EMIL enumeration, current row fixtures, authenticated probes, a dependency
compatibility matrix, installed-wheel typing, and `py.typed` are also deferred.
There are no authenticated tests in this milestone. Any future authenticated
tests must be opt-in and skipped by default. No forecaster work is included.
