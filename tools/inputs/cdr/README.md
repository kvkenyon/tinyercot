# Historical CDR summary fixtures

`summaries.zip` contains nine unmodified original XLS/XLSX report workbooks.
`sources.json` records each download URL, title, SHA-256, byte length, and ZIP
member. The selected vintages cover entity-based and system summaries, old XLS
errors, short winter periods, cumulative installed ratings, and newer peak-load /
peak-net-load / difference columns across all four seasons.

`tests/test_cdr.py` compares typed values and located notes with these originals
and checks the distinctions above. Additional live-source validation opened all
53 report workbooks; its compact results are in `evidence.json`. Full downloads
used for that wider check are not regression fixtures.

Fixtures are development inputs, excluded from the wheel. Nothing here contains
credentials. XLSX warnings about unsupported charts or formatting arise during
read-only loading; the stored original workbook bytes are unchanged.

`county-tables.zip` adds three unmodified originals for county forecasts, source
load-basis changes, and an unlabelled numeric row. County tests also reuse the
2007 original in `summaries.zip` for missing cells. `county-sources.json` records
fixture hashes; `county-evidence.json` records the complete 10-workbook,
74-table source comparison. These are planning forecasts and illustrative
balances, not measured county demand or physical power flows.
