# Public RT annual archives

`tinyercot.public.archive_reports` adds anonymous listing, receipt-verified ZIP
downloads, and typed streaming rows for **NP6-785-ER / report 13061**. ERCOT
identifies this product as public in its
[primary product metadata](https://www.ercot.com/mp/data-products/data-product-details?id=np6-785-er).
The adapter uses the website's public `IceDocListJsonWS` listing and
`mirDownload` routes. It never uses EWS or credential headers.

```python
from contextlib import closing
from pathlib import Path
from tinyercot.public.archive_reports import RTArchiveClient, iter_rt_archive

with RTArchiveClient() as client:
    documents, receipt = client.archives()
    document = next(d for d in documents if d.friendly_name == "RTMLZHBSPP_2010")
    download = client.download(document, cache=Path(".ercot-cache"))
    with closing(iter_rt_archive(download, max_rows=None, max_scan_rows=None)) as rows:
        for record in rows:
            process(record.row)  # Caller-defined consumer.
```

The default row limit is 1,000. Reaching a row or scan budget raises explicitly;
None enables complete iteration through the selected file, including all its
worksheets. Source duplicates and ordering are retained. This does not establish
complete annual interval coverage or historical revisions. Source dates, hours,
quarter-hour intervals, and repeated-hour flags remain separate; UTC intervals
are not inferred. A changed header or unsupported cell type fails explicitly.
Empty worksheets must still carry the verified header.

On 2026-09-06 UTC, anonymous discovery fetched one listing and exactly two
selected files: the 1,292,145-byte 2010 archive and the 9,091,870-byte 2026
archive. Both have the same seven-column schema. Only the first few rows and
worksheet metadata were inspected; no full-year row extraction ran. The checked-in
`tests/fixtures/public/rt-archive-excerpt.json` contains the source receipts,
listing records, member/sheet names, exact headers, and three source rows per
file. Full ZIPs remain ignored local evidence. Other years are listed but were
not retrieved or separately validated. Matching schema is required on every
selected worksheet; older or future incompatible schema epochs remain unsupported.

Offline tests build tiny workbooks from those recorded cells and cover complete
two-sheet iteration, cache reuse/mutation, nonpublic listings, unlisted documents,
schema drift, invalid cell types/ranges, requested-sheet absence, and budgets.
The independent installed-wheel probe is explicitly opt-in:

```bash
/absolute/wheel-venv/bin/python -I tools/probe_rt_archives.py --live --output /absolute/evidence/rt-archives --source-evidence /absolute/discovery-evidence
```

That command fetches a fresh public listing, seeds the isolated cache from the
two existing discovery ZIPs and original receipts after checking hashes and byte
counts, decodes four typed rows per file, and verifies cache reuse. The installed
client validates each receipt against the new listing before decoding. This proves
installed typed decoding and cache reuse, not a repeated installed file download.
It is never invoked by the offline suite.

This adapter adds one narrow MIS/archive source, not REST endpoint coverage.
Restricted, retired, unavailable, and unknown products remain outside this
adapter. It makes no authenticated request and performs no bulk history traversal.
