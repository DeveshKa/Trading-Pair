# Snapshot contract

One immutable directory contains:

- `bars.csv`: date,symbol,open,high,low,close,adj_close,volume,dividend,split,sector.
- `benchmark.csv`: date,close.
- `manifest.json`: source,price_basis,benchmark_kind plus provenance/quality metadata.
- `membership.csv`: symbol,effective_from,effective_to, required unless explicitly exploratory.

Dates are ISO session dates. `effective_from` is inclusive and `effective_to` exclusive; blank end means still active. Overlapping intervals are rejected. Preserve former members' prices; do not restrict the files to today's constituent list. Source-specific identity resolution is upstream; ticker strings in this release must be stable within a snapshot.

Execution OHLC are **raw share-unit prices** in INR. `adj_close` is a dividend-reinvested, split-adjusted research index or equivalent consistently scaled series. It never determines a fill price. `dividend` is the cash entitlement per post-split share on the event date. `split` is new shares per old share, with **1 for no event**. Long dividends add cash; short dividends deduct cash. Future action transformations must not be applied twice. Unresolved mergers, rights or demergers need upstream treatment or exclusion and an explicit limitations record.

All prices, ratios and numeric fields must be finite; prices/ratios positive; volume/dividend nonnegative. Duplicate date-symbol rows and invalid OHLC relationships are errors. Do not impute a missing execution bar. Holidays should have no rows, rather than fabricated flat rows. A price with zero traded volume cannot fill a position.

Example manifest:

```json
{
  "source": "audited_nse_snapshot_v1",
  "price_basis": "raw_execution",
  "benchmark_kind": "NIFTY_50_TRI",
  "membership_audited": true,
  "actions_complete": true,
  "synthetic": false,
  "notes": "Set audit flags only after a documented review; flags are declarations, not certifications."
}
```

For provider smoke tests use `membership_audited:false` and `actions_complete:false` and retain exact download/correction details. The default CLI requires an audited-membership declaration or `--exploratory` for non-synthetic runs; it cannot independently certify a declaration's truth.

Benchmark values must cover every stock session. Use a TRI level series for a dividend-inclusive Nifty comparison. Mark a price index as `PRICE_INDEX`; do not relabel it as TRI. Benchmark and portfolio NAV start from the same capital on the first evaluated formation-complete session, not the start of warm-up.

The loader hashes each file and the snapshot. Downloads stage into a temporary sibling directory, validate, then rename to the final destination. An existing destination is not overwritten. Local runs consume snapshots, not live provider calls, so a test can be reproduced offline after data acquisition.

This version validates schemas and chronology but does not reconstruct announcement timestamps or prove issuer lineage. Those upstream audits remain required for a production point-in-time dataset.
