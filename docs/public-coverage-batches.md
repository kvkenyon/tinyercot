# Public Reports coverage batches

This batch adds 64 source-backed Public Reports contracts to the prior 56,
for 120 generated data operations in 87 product namespaces. It uses the same
registry, product facades, typed filters, and bounded iteration. Imports and
offline metadata require no credentials. Legacy runtime files remain unchanged.

The additions cover published renewable/load outlooks, RUC factors and actions,
DC-tie schedules and state-estimator aggregates, public scarcity/price reports,
and explicitly Public delayed disclosures. These are source publications;
TinyERCOT does not compute forecasts or access private bids, COP, awards,
telemetry, customer data, Secure, Certified, or participant EWS services.

```python
from decimal import Decimal
from tinyercot.public import Credentials, ReportsClient, products

endpoint = products.np3_916_ex._3d_highest_price_offer_sced
with ReportsClient(Credentials.from_env()) as client:
    page = client.page(endpoint, size=1, sort="SCEDTimestamp", direction="desc")
    if page.rows:
        price: Decimal = page.rows[0].LMP
```

The source-declared `DECIMAL` type is represented by Decimal, preserving JSON
number text. Booleans and numeric-looking strings are rejected. Source DATE,
DATETIME, numeric, string, and boolean fields keep their prior interpretation.
Only explicitly observed nullability is accepted, with every field required.
Each page reads its contract once before validating rows, avoiding repeated
parsing for every null cell during a large requested iteration.

The field descriptors and two bounded source observations for every new
operation are pinned in `tools/inputs/current/` and
`tests/fixtures/public/batch/`. Fixtures add one terminal newline; remove that
newline to reconstruct each original response hash. Source schemas and query
contracts are independently checked against the pinned ERCOT OpenAPI export
and the authenticated public product/artifact metadata.

## Evidence boundaries

The [installed receipt index](evidence/installed-registry-index.json) separates
generated contracts from current and oldest-first typed retrieval, unsuccessful
operations, and complete-query evidence. Successful response counts exclude
authentication and unsuccessful retry attempts. An unsuccessful request does
not establish that a public product is permanently unavailable or restricted.
No already successful request is repeated merely to assemble this index.

All 120 generated paths have installed attempts. **118 paths decoded both
current and oldest-first rows**, with 119 current and 118 historical successful
response receipts (the prior DAM second page accounts for the extra current
receipt). NP4-442-CD and NP4-443-CD model reports retain verified source schemas
and offline fixtures, but their installed requests failed in both directions.
One bounded retry per failed direction also returned `SourceUnavailableError`.
The index preserves all eight failed operations across those two rounds;
authentication and transport retry totals are not inferred from these records.
No successful installed retrieval is claimed for these two generated paths.
`pending_generated_paths=[]` means every generated path was attempted; it is
not a success count. `pending_generated_both_period_paths` explicitly lists
the two paths above, while `both_period_typed_unique_paths=118` counts success.

Pagination and completeness remain separate from a one-row observation. The
existing two-page RT selection completed two rows; the new registry batches
do not add a full-history claim. Complete page and annual worksheet iteration
remain opt-in and bounded, with offline regression tests. Retired publication,
public archive access, and unknown row schemas remain separate categories.

NP3-763-CD system adequacy currently declares a numeric hour-ending field but
returns an hour string. Discovery retains the declared/observed contradiction
and leaves the endpoint untyped. Source transport failures and missing row
observations also remain explicit. No placeholder model is generated.

The [two additional anonymous dashboards](additional-dashboards.md) expose
system-wide price and supply/demand snapshots with their published outlook
sections. Their installed receipts are separate from Public Reports coverage;
an observed stale price snapshot remains explicitly stale. They do not increase
the 243-path API denominator or compute a forecaster.

The separate ESR/archive worker delivered Public Data access receipts and
installed archive row samplers in PR #5. Its uncommitted reference work in this
checkout is preserved separately from this batch. Public Reports generation,
registry, and integration continue here, followed by remaining public binary
and retired historical content. ESR service/auth analysis and those delivered
samplers stay with their owner; no existing PR is modified or merged.
