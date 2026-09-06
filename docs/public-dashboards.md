# Anonymous dashboard snapshots

`tinyercot.public.dashboards.DashboardClient` adds two opt-in website captures:
fuel mix and Daily PRC with the current grid-condition status. Imports and
offline decoding require no credentials. Each method makes one logical GET
with the existing bounded retry, response-size, pacing, and request budgets.
There is no timer, date selection, or historical download operation.

```python
from tinyercot.public.dashboards import DashboardClient

with DashboardClient() as client:
    fuel = client.fuel_mix()
    grid = client.grid_conditions()

print(fuel.rows[-1].generation.natural_gas)  # Decimal MW
print(grid.current_condition.state)  # Original ERCOT status label
print(grid.source_last_updated, grid.is_stale())
```

Fuel mix exposes all eight observed fuel categories and keeps `monthlyCapacity`
separate from interval generation. Original signed storage values and numeric
precision remain intact. Day keys and offset-bearing timestamp keys are retained.
Daily PRC retains condition text, status, EEA/energy values, display PRC text,
source index, source epoch, and every returned PRC observation. It does not turn
source labels into a client-defined emergency-state classification.

The decoder checks explicit offsets against America/Chicago. PRC epoch
milliseconds and local interval labels must agree with their timestamp, and
the condition epoch seconds must agree with the source update time. Both feeds
require strictly increasing observation instants, allowing distinct offsets
during the repeated fall hour. Source DST flags remain uninterpreted.

Original bytes, source timestamps, retrieval timestamps, public URLs, HTTP
status, and response hashes remain available. `is_stale()` compares source
update time with capture time; its default ten-minute threshold is caller
policy, not an ERCOT update guarantee. Future timestamps are stale. Unknown
fields, missing fuel categories, nulls, numeric strings, booleans in number
fields, nonfinite values, and conflicting time evidence fail closed. New status
*strings* are retained without guessing their meaning.

These are website source-family subsets, separate from the 243 observed Public
API data paths. They do not establish historical retention, complete-day
coverage, a latency SLA, historical condition-state schemas, generation outage
coverage, private resource telemetry, or the four-second ESR Public Data API.
The source may change or deny anonymous access; errors use the new public
exception hierarchy. Restricted and unavailable source families remain explicit
in the coverage inventory.

## Source evidence and reproduction

ERCOT's [fuel-mix page](https://www.ercot.com/gridmktinfo/dashboards/fuelmix)
directly configures
[`fuel-mix.json`](https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json).
ERCOT's [grid-conditions page](https://www.ercot.com/gridmktinfo/dashboards/gridconditions)
directly configures
[`daily-prc.json`](https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json).
The latter page explains PRC as responsive resource capability available online
in real time. The adapter preserves this source series without calculating a
forecast or interpreting future reserve sufficiency.

Two anonymous source captures on 2026-09-06 UTC established the explicit row
models. [Fixture provenance](evidence/dashboard-fixture-provenance.json) records
full-response hashes, retrieval times, public source URLs, fixture hashes, and
exact excerpt transformations. The compact fuel fixture retains first/last two
observations per day; the PRC fixture retains first/last two observations and
all current-condition fields. Numbers are serialized losslessly. Full snapshots
are not checked in. Offline tests mutate these fixtures to exercise type drift,
source-time conflicts, freshness, DST, access denial, and anonymous transport.

For a deliberately small real installed-wheel validation:

```bash
/absolute/venv/bin/python -I tools/probe_dashboards.py --live --output /tmp/dashboard-receipts.json
```

The probe rejects source-tree imports, requires an isolated venv interpreter,
limits the total budget to two attempts, disables retries, and saves receipts
and typed row counts. It neither loads `.env` nor uses ERCOT authentication.
It does not run in the default offline test suite.
