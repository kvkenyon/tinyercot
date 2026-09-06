# Selected public API archives

`tinyercot.public.api_archives.APIArchiveClient` adds typed **document metadata**
and one selected public ZIP download. It inherits explicit public-account
credentials and bounded transport from `MetadataClient`. The generic transfer
keeps `APIArchiveFile.row_schema` as `"unknown"`; the separate, optional
`iter_resource_dme` decoder supports the verified NP3-988-ER CSV format below.

```python
from tinyercot.public import Credentials
from tinyercot.public.api_archives import APIArchiveClient

with APIArchiveClient(Credentials.from_env()) as client:
    products, root_receipt = client.products()
    page = client.archives("NP3-988-ER")
    selected = page.documents[0]
    file = client.download(selected)
    assert file.row_schema == "unknown"
```

Calling `products()` establishes this instance's source-backed access gate and
invalidates previous download selections. An archive request requires an exact
product from that fetched root with explicit Public classification. Lifecycle is
separate: inactive or audit-retired products are marked `retired-or-inactive`,
and their historical public documents remain selectable when the current listing
verifies availability. That does not reinstate a retired live service. Secure,
Certified, missing classifications, unknown products, and unlisted document IDs
cannot authorize downloads.

The source preserves publication timestamps without offsets. They remain exact
strings in `post_datetime`; the adapter does not invent UTC or market-time
semantics. Listing counts refer to documents, never decoded data rows. The source
advertised 278 NP3-988-ER archive records on one page during discovery. The adapter
returns source counters and does not follow further pages automatically.
Archive pagination remains deferred pending a verified query contract.

Downloads use the
[primary OpenAPI contract](https://apiexplorer.ercot.com/developer/apis/pubapi-apim-api?export=true&api-version=2022-04-01-preview):
`POST /archive/{emilId}/download` with JSON `{"docIds": [selected_id]}`. Selection
is limited to one unchanged document returned by this client. The response byte
budget, ZIP member count, expansion size, paths, and member integrity are checked;
members are never extracted to local paths. The returned document identity is
retained beside the receipt because a POST receipt URL alone cannot identify the
selected document.

The bounded source discovery POST selected document 1270779234 on 2026-09-06
UTC. ERCOT returned 22,983 ZIP bytes containing one CSV member (212,038 expanded
bytes). The source receipt and checked directory metadata are recorded in
`docs/evidence/api-archive-download.json`. One additional bounded historical check
selected document 1166614741, dated 2025-12-01, returning 21,892 ZIP bytes. Its
matching seven-column header and source rows are pinned alongside the current
sample in `tests/fixtures/public/resource-dme-excerpt.json`. This oldest listed
observation does not prove stable retention or complete history.

## Optional resource decision-making entity CSV rows

```python
from contextlib import closing
from tinyercot.public.resource_dme import iter_resource_dme

# file is one previously selected NP3-988-ER APIArchiveFile.
with closing(iter_resource_dme(file, max_rows=None)) as records:
    for record in records:
        process(record.row.dme_duns)  # Original string, including leading zeros.
```

The exact source columns are OWNER RE, RESOURCE NAME, TYPE, SPLIT GEN RESOURCE,
DME, DME DUNS, and RMR. Every cell remains a string: blanks, whitespace, quoting
results, flags, and identifier zeros are preserved. No string is silently parsed
as a number, boolean, or enumeration. `ResourceDmeRow` gives these observed
columns explicit field names. Receipt, source product, document/member identity,
UTF-8 decoding, ZIP expansion, header, and column checks fail explicitly on an
unknown schema epoch. `max_rows=None` iterates the complete selected CSV;
the default 1,000-row safeguard raises if more records remain.

## Explicit historical bundles

`client.bundles("NP4-190-CD")` returns a separate `APIBundlePage`. The actual
source response advertised 103 monthly bundles with signed negative document
identities, spanning the observed 2018-01 through 2026-08 labels. This is listing
evidence, not a claim of uninterrupted monthly data. Bundle metadata excerpts
and their source receipt are pinned in `tests/fixtures/public/api-bundle-excerpt.json`.

`client.download_bundle(page.documents[0])` uses only
`POST /bundle/{emilId}/download` with that one source ID. Ordinary archive
documents cannot substitute for bundle identities, and a failed route never
falls back to another service. The caller's HTTP byte budget remains in force;
bundle defaults allow 512 ZIP members and 256 MB of advertised expansion.
Bundle CSV member-row schemas remain unknown. An installed-wheel attempt to
retrieve the oldest listed monthly bundle (-593019152, 2018-01) returned
`SourceUnavailableError` within a 16 MB response ceiling and one attempt. The
initial probe did not retain the exact HTTP status; no successful bundle bytes
or decoded rows are claimed. This does not establish that every bundle is
unavailable. There is no route fallback or repeated bundle request.

## Installed-wheel evidence

`docs/evidence/installed-api-archive-receipts.json` records real installed-client
root metadata (116 products), the 278-document DME listing, the 103-document DAM
bundle listing, and four typed DME rows from each of the two original ZIP caches.
Cache decoding checks original document publication/selection identity and
receipt hashes. The installed client did not download those files again.

Two additional installed metadata requests verified public history listings for
audit-retired NP4-179-CD and NP3-990-EX: 1,000 of 4,236 and 1,000 of 2,602
document entries respectively. Their lifecycle remains `retired-or-inactive`.
No document from either retired collection was downloaded. Further listing pages
remain outside this adapter's verified pagination contract.

The explicit probe is `tools/probe_api_archives.py`. It requires an isolated
installed interpreter, `--live`, an existing mode-0600 `--credentials-file`,
`--evidence` pointing at the original ignored catalog evidence, and `--output`.
`--retired-history` adds only the two bounded listings. The separately opt-in
`--download-oldest-bundle` selects one bundle, with no monthly row extraction.
It refuses to overwrite an existing bundle output. The offline suite tests cache
binding and never executes authenticated requests.

`tests/fixtures/public/api-archive-excerpt.json` records the exact primary spec
hash, public root receipt, one source product, archive-list receipt, and the first
two unmodified archive records. Source pagination counters remain unchanged in
the fixture; tests adjust them only when constructing a synthetic two-row page.
Offline checks cover metadata drift, public access gates, known retirement,
selection invalidation, JSON POST shape, untyped generic member data, malformed
archives, and byte/ZIP budgets. The optional DME decoder has current/historical
source-cell tests, identifier preservation, malformed schema tests, and complete
iteration beyond the sampling budget. Other binary row schemas remain unsupported;
these file adapters add no count to the typed REST data-path denominator.
