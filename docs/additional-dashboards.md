# Public price and supply/demand snapshots

`tinyercot.public.additional_dashboards.AdditionalDashboardClient` adds two
anonymous captures: `system_prices()` and `supply_demand()`. It inherits the
existing dashboard transport budgets and connection lifetime. Each method
makes one logical capture with bounded retries. It does not request historical
dates, poll continuously, interpolate missing observations, or compute forecasts.

```python
from tinyercot.public.additional_dashboards import AdditionalDashboardClient

with AdditionalDashboardClient() as client:
    prices = client.system_prices()
    supply = client.supply_demand()

print(prices.real_time[-1].hbHouston)
print(supply.data[-1].forecast, supply.source_last_updated)
```

Website prices preserve every source hub/load-zone price as a Decimal, keeping
real-time and day-ahead rows in separate tuples. Day-ahead rows can describe
future intervals; those intervals are not confused with source publication or
retrieval time. The source hour-ending value 24 remains 24, alongside the
following midnight's explicit offset-bearing timestamp and epoch.

Supply/demand has three observed shapes. Actual data rows carry integer
`forecast=0` and have no `available` field. Same-day forecast rows carry
`forecast=1` and require the source `available` value. The separate multi-day
`forecast` section preserves published capacity/demand, local begin/end text,
operating-day text, hour-ending labels, and offset-bearing end-time evidence.
No `available=None` is manufactured for actual rows. Published forecasts remain
source values; this client does not predict reserve sufficiency or demand.

The decoders reject unknown fields, missing columns, numeric strings, booleans
in integer fields, nulls, nonfinite prices, unknown forecast discriminators,
conflicting epoch/time evidence, and repeated or reversed rows. Offset checks
use America/Chicago. Repeated fall-hour observations remain distinct by their
explicit offsets; DST flags are retained without interpretation. The local
outlook start text has no offset, so no UTC start instant is invented.

Original response bytes and receipt hashes remain available. Freshness uses
the source update time and retrieval time, separately from forecast intervals.
The caller-selected ten-minute default is not an ERCOT service guarantee.
These snapshots do not prove complete-day coverage, historical availability,
stable publication latency, or equivalence with Public Reports API rows.

## Primary evidence

ERCOT's [System-Wide Prices page](https://www.ercot.com/gridmktinfo/dashboards/systemwideprices)
declares the
[`system-wide-prices.json` route](https://www.ercot.com/api/1/services/read/dashboards/system-wide-prices.json).
It describes real-time/day-ahead hub and load-zone prices and cautions that
related API reports may differ from the display. This adapter does not replace
NP6-905-CD or NP4-190-CD query contracts.
The audit's public product catalog identifies this display as GEN-542-UI.

ERCOT's [Supply and Demand page](https://www.ercot.com/gridmktinfo/dashboards/supplyanddemand)
declares
[`supply-demand.json`](https://www.ercot.com/api/1/services/read/dashboards/supply-demand.json).
Only its public aggregate payload is decoded; private planning inputs and
resource telemetry remain outside the adapter.
The audit identifies this supply/demand display as GEN-530-UI; it is distinct
from the GEN-543-UI Grid Conditions display.

[Fixture provenance](evidence/additional-dashboard-fixture-provenance.json)
records two anonymous source captures, exact response hashes, source timestamps,
and compact lossless excerpt transformations. The observed response contained
80 RT price rows, 24 DAM price rows, 241 actual supply/demand rows, 48 same-day
forecast rows, and 144 published outlook rows. Those counts describe one capture,
not retention or a guaranteed feed size. No source nulls were observed.

Run the explicit installed-wheel probe with an isolated virtual environment:

```bash
/absolute/venv/bin/python -I tools/probe_additional_dashboards.py --live --output /tmp/additional-dashboard-receipts.json
```

It makes at most two anonymous attempts with retries disabled and records typed
row counts and source receipts. It never loads `.env` or performs authentication.

The [installed-wheel receipts](evidence/installed-additional-dashboard-receipts.json)
record a successful isolated Python 3.14 proof on 2026-09-06 UTC: 80 RT and
24 DAM price rows, plus 289 supply/demand and 144 outlook rows. The price source
was just over ten minutes old at retrieval and correctly reported stale;
supply/demand was fresh under the same caller policy. Successful decoding does
not imply a fresh publication. No retry or second capture was made to replace
that observation.
