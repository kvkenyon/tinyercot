# Public metadata and generated retrieval

The opt-in registry now has 56 typed Public Reports operations. Its 52 new
operations use the same `ReportsClient.page`, `iter_pages`, and `iter_rows`
contracts as the four previously delivered operations. Legacy runtime files
remain byte-identical. Importing metadata or generated products makes no
request and requires no credentials.

```python
from tinyercot.public import Credentials, ReportsClient, products

endpoint = products.np6_322_cd.sced_system_lambda
with ReportsClient(Credentials.from_env()) as client:
    page = client.page(endpoint, size=1, sort="SCEDTimestamp", direction="desc")
    for row in page.rows:
        print(row)
```

Use the exact field/filter names in the generated product facade. Date-time
query fields retain ERCOT's naive `yyyy-MM-ddTH24:mm:ss` format; timezone-aware
or subsecond query values are rejected. This does not infer UTC for ambiguous
market timestamps. Source numeric values use Decimal where declared numeric;
string identifiers remain strings. Explicitly observed nulls are accepted only
for source-declared fields and every field stays required. Unknown types,
unobserved nullability, missing fields, and changed schemas fail closed.

## Sources and reproduction

The current query pin is ERCOT's [Public Reports OpenAPI export](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview),
SHA-256 `b978bf35fbf9dcb8edca14025d4b5d3108582885a6c1b92a9bf445e69b08a7f8`.
The authenticated public [product root](https://api.ercot.com/api/public-reports/)
returned 116 products (97 DATA, 19 BINARY) and 242 artifact paths. Both audience
and security classification must explicitly say Public; neither authentication
nor an endpoint link grants entitlement to restricted information.

`tools/observe_catalog.py` saves bounded response/receipt pairs, with at most
20 product identities and an explicit request budget per invocation. It never
updates generation inputs. `tools/register_public_batch.py` cross-checks the
saved public product root, exact OpenAPI bytes, response receipts, field types,
and current/historical observations. It outputs reviewable projections and an
operation-state report. `tools/generate_public.py` reads only pinned local
inputs and generates models, filter TypedDicts, endpoint registry, and product
facades. Missing or ineligible evidence cannot generate a row model.

```sh
uv run python -m tools.register_public_batch --evidence .local-evidence/catalog --spec /path/to/explorer-export.json --output .local-evidence/projected
uv run python tools/generate_public.py --check
uv run python tools/generate_client.py --check
```

The checked-in current contracts retain compact field/query projections,
source hashes, public product identity, and receipts. Two one-row response
fixtures per new path support independent offline decoding. Fixtures in
`tests/fixtures/public/batch/` add one terminal newline to the exact captured
response; removing that single newline reproduces the original receipt hash.
The root fixture uses the same reversible transformation. No authorization
headers, tokens, credential values, or private responses are retained.

## Exact evidence limits

[The machine-readable installed index](evidence/installed-registry-index.json)
contains all 56 unique generated paths and their receipt references. It records
57 current requests across 56 paths (including an earlier DAM second page),
and 56 oldest-first requests across 56 paths. The new 52-path batch contributes
104 one-row requests. All have successful typed decoding through an isolated
installed wheel. The index builder is offline and makes no repeat requests.

Pagination evidence is separate: two API paths have live multiple-page
retrieval, and one RT selection completed its two pages/two rows. The new
52-path batch adds no live pagination or completeness proof. Complete page
iteration, failure budgets, and annual multi-worksheet iteration also have
offline mocked tests. No complete history or annual extraction was performed.
Oldest-first rows identify available observations within source retention and
filters; they do not establish every historical schema epoch.

Public metadata, archive documents and monthly bundles have typed identity and
file-result contracts separate from row models; see [archive evidence](api-archive-installed-task-note.md).
Public BINARY content is excluded from row generation, while public document
retrieval remains active work. Retired total-AS-offer and SASM products retain
available archive listings even when source metadata still says Active.
The 2001 hourly-load gap remains unavailable. Secure, Certified, EWS, private
telemetry/bids/COP/awards and customer/participant settlement data remain
restricted. Delayed disclosures explicitly classified Public are a separate
public coverage category.

The other 187 observed data paths and remaining public document/history
families remain active work for subsequent stacked PRs. Website fuel mix,
PRC, outage and DC-tie snapshots, RT annual files, and DME document decoding
have separate evidence; they do not increase the 243-path API numerator.
Authorized public authentication occurred. No restricted request, paid access,
forecaster computation, secret copying, or historical bulk extraction occurred.
