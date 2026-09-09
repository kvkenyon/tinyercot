# Market scope

Tinyercot supplies typed source data for energy trading, retail exposure, battery
operation, demand and price forecasting, and ML research. A dataset belongs here
when it provides a market target, an explanatory input, or settlement/reference
information needed to use those inputs correctly.

| Keep | Use |
| --- | --- |
| DAM/RT prices, SCED LMPs, adders and ancillary prices | Energy and ancillary-service targets and settlement exposure |
| Load, wind/solar, weather and their forecast vintages | Demand/supply features and historical forecast evaluation |
| Outages, constraints, offers, awards and delayed disclosures | Availability, congestion and market behavior |
| Storage observations and ancillary requirements | Battery and ancillary-service analysis |
| Retail load profiles, losses, 4CP, territory/class energy totals | Retail demand, settlement and peak exposure |
| Resource changes, capacity outlooks and weather-year scenarios | Forward supply/demand analysis and scenario research |
| Historical observations and source metadata | Backfills, revisions and information availability |

Keep source timestamps, units, geography, intervals, correction identity, and
missing values. Forecasts and modeled scenarios remain distinct from realized
observations. Fully typed generated methods are part of the core interface;
shortening them must not replace named filters or row models with dictionaries.

Exclude administrative transaction-message counts, compliance narratives, and
general document/table extraction. County planning illustrations are not observed
power flows and do not belong in the core market SDK. Further CDR workbook
expansion is outside this release's scope. A hypothetical research use alone is
not enough to justify another parser and maintenance burden.

This cleanup removes `Client.retail_transactions`, `RetailTransactionDay`, and
`RetailTransactionMonth`, including their dedicated fixtures and tests. They
count retail process messages, not metered energy or market trades. Retail
profiles, losses and territory/class energy totals remain available. The removed
implementation remains recoverable from Git history.

Release work should prioritize usable end-to-end market workflows, reliable
historical retrieval, precise typing, and source-specific limitations. Dataset
counts and complete-file comparisons establish access and decoding; they do not
establish predictive accuracy or trading returns.
