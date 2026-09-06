# Anonymous outage and DC-tie aggregates

The opt-in `tinyercot.public.aggregate_dashboards.AggregateDashboardClient`
adds `generation_outages()` and `dc_tie_flows()`. It inherits the existing
dashboard client's bounded transport, connection lifetime, and fuel-mix and
grid-condition methods. Each new method makes one logical anonymous capture
with bounded retries. It never requests historical dates or starts polling.

```python
from tinyercot.public.aggregate_dashboards import AggregateDashboardClient

with AggregateDashboardClient() as client:
    outages = client.generation_outages()
    ties = client.dc_tie_flows()

print(outages.current[-1].row.dispatchable.unplanned)
print(ties.rows[-1].dcN, ties.rows[-1].currentFrequency)
```

Generation outages retain the original current/previous sections, day and
resource-type labels, source epoch keys, delivery timestamps, DST flags, and
Combined/Dispatchable/Renewable planned, unplanned, and total values. Source
totals and the `currentOutages` display value are retained without recalculation.
One captured response includes a rolling previous-six-day section; this is not
a date-selection adapter or a guarantee of retained history or complete days.

DC-tie observations retain all four signed source flows and the public
aggregate frequency and inertia values returned alongside them. Negative flow
means import to ERCOT; positive flow means export. `currentFrequency` preserves
JSON numeric precision as Decimal. The observed integer fields remain strict
integers. Original offset-bearing timestamp, epoch, interval, and DST labels
remain available.

Both decoders verify Texas offsets and epoch evidence, reject future rows
relative to source update time, and require increasing instants within each
section. Outage observations must belong to the source section's day labels.
Distinct fall-back offsets remain separate observations. They preserve source
DST labels without interpreting their meaning. No source nulls were observed
in these captures; nulls, missing fields, unknown categories, type drift, and
nonfinite values fail closed instead of being silently replaced or guessed.

Snapshots expose the same original bytes, source update timestamp, UTC receipt,
HTTP status, hash, and caller-selected freshness check as other dashboards.
These website subsets cover GEN-546-UI and GEN-538-UI separately from Public
API data paths. They do not implement private telemetry, outage submissions,
individual-unit details, DC-tie schedules, or state-estimator APIs. Source
schemas outside the observed aggregate payloads remain unknown.

## Primary source evidence

ERCOT's [generation-outage dashboard](https://www.ercot.com/gridmktinfo/dashboards/generationoutages)
configures [`generation-outages.json`](https://www.ercot.com/api/1/services/read/dashboards/generation-outages.json).
Its description says the MW reductions include partial and full outages,
including storage, relative to seasonal maximum capability. It also explains
that submitted outage information can arrive after an event, and that extended
planned outages can become forced outages. A capture therefore does not prove
the information available at an earlier point in time. The page warns that
NP1-346-ER can differ; this adapter does not substitute for that report.

ERCOT's [DC-tie dashboard](https://www.ercot.com/gridmktinfo/dashboards/dctieflows)
configures [`dc-tie-flows.json`](https://www.ercot.com/api/1/services/read/dashboards/dc-tie-flows.json).
The page supplies the import/export sign convention. Its chart labels identify
the East, Laredo VFT, North, and Railroad series.

Two bounded anonymous captures on 2026-09-06 UTC established these models.
[Provenance](evidence/aggregate-dashboard-fixture-provenance.json) records the
full response hashes, retrieval timestamps, source URLs, compact fixture hashes,
and exact excerpt transformations. The outage fixture retains first/last two
rows per section plus all metadata. The DC-tie fixture retains first/last two
rows. Full response snapshots are not checked in. Offline tests cover strict
types, source drift, time/section contradictions, repeated DST hours, original
totals, and anonymous transport.

An explicit installed-wheel probe is available:

```bash
/absolute/venv/bin/python -I tools/probe_aggregate_dashboards.py --live --output /tmp/aggregate-receipts.json
```

It requires an isolated venv import, performs at most two anonymous attempts
with retries disabled, and saves only receipts, source update times, and typed
row counts. It does not load `.env`, authenticate, poll, or extract history.
