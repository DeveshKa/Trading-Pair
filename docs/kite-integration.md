# Later Kite Connect integration

The research engine has no Kite dependency. Historical acquisition implements `data.HistoricalProvider`; streaming acquisition will implement `providers.QuoteProvider`. CSV imports and downloaded library data exercise the same validated snapshot and strategy paths.

Integration sequence:

1. Add a provider package that authenticates through the documented broker flow; secrets live outside Git and logs. Obtain the appropriate market-data and API entitlements.
2. Map instrument tokens to exchange, durable security ID, dated lot size and expiry. Never treat tokens or today's instrument dump as timeless historical identities.
3. Normalize historical candles into the existing snapshot contract. Establish adjustment conventions and add corporate-action/membership inputs independently; candle availability does not prove action completeness.
4. Convert streaming observations into timezone-aware `Quote` events. Validate bid/ask, stale data, event ordering, disconnects, resubscriptions and clock skew.
5. Aggregate/finalize observations at the approved daily signal boundary. Compare replayed decisions with the historical engine. The current diagnostic `scan` refit is not a replacement for the monthly strategy's state.
6. Add a persisted paper-position service and measure simulated versus observed fills. Use live quotes to check execution feasibility; keep a statistical setup blocked until actual contracts, quantities and capital qualify.
7. Add opted-in external alert delivery from the outbox, with retries, expiry, provider acknowledgments and duplicate handling. Do not send the historical backtest outbox to real recipients.
8. Implement broker orders only as a separate release with explicit enablement, dated costs/margins, idempotent submission, ambiguous-order reconciliation, partial/unmatched-leg handling, audit storage and kill-switch drills. Confirm current broker/exchange API and algo requirements.

Do not pass Kite's continuous futures chart to the cash-equity ledger and call it a futures backtest. Real contracts require a separate margin/settlement ledger, lot rounding and explicit rolls. The quote protocol is a boundary, not a claim that these facilities are already implemented.
