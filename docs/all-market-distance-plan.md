# Return to the original pairs-trading idea: NSE and BSE

Direction updated 11 November 2026. This document supersedes correlation-based qualification as the active discovery direction. Earlier diagnostics remain archived for reproducibility; no correlation or cointegration threshold is applied by `discover` or `distance-study`.

## Method

Use the original minimum-distance idea from Paper 1. At each formation date, build complete normalized total-return paths for eligible stocks and calculate the sum of squared differences between every pair. Rank by the smallest distance. Then observe the selected pairs in a subsequent trading window: open a long/short setup when their paths diverge by two formation-period standard deviations, and observe whether they cross again.

Finding the pair and observing its later behavior are separate operations. Later convergence or profit does not alter the earlier ranking. A visually close pair can still diverge permanently. A zero-distance pair with no spread variability has no usable divergence signal.

Initial formation horizon is 252 trading sessions, followed by 126 trading sessions, corresponding approximately to the paper's twelve-month/six-month sequence. Repeat formation monthly across the available 2005–2025 history. Add 756- and 1,260-session formation studies as separately reported sensitivity experiments; do not pick the best lookback after seeing final evaluation outcomes. Twenty-one years of evaluation does not mean forcing one twenty-one-year fit onto today's stocks.

There is no sector restriction in the active minimum-distance search. Liquidity, complete observations, ordinary-equity classification, identity and execution constraints remain necessary. They are data/trading requirements, not disguised correlation tests.

## Universe: catalog, history and executable subset

Keep three counts distinct: securities listed in source catalogs; securities with usable history in an audited snapshot; and securities that pass formation/execution checks on a specific date. None implies the other two.

The official NSE equity list retrieved in this work contained 2,633 rows. It is a current listing snapshot, not historical coverage of all companies. BSE's list and daily archive endpoints returned HTTP 403 from this environment. Their routes are supported through official local exports and the UDiFF parser, but BSE-wide data has not been downloaded or backtested. No bypass of those access restrictions is attempted.

Production history should be built from dated daily exchange archives, including securities later removed or delisted. Current NSE/BSE lists are discovery aids and reconciliation sources; applying them retrospectively creates survivorship bias. Listings, renamings, migrations and suspensions require dated records. A corporate-action-adjusted history is mandatory before raw bhavcopy prices become research total-return paths.

The current implementation accepts ordinary-equity exports. Funds, preference shares, warrants, debt and SME/microcap subsets require explicit classification and separate tradeability rules. Broad ingestion can retain them, but it must not silently mix different instrument types into ordinary-stock research.

## NSE/BSE identity and venue handling

Match security identity using verified ISIN records and dated exchange codes, not similar company names. Two venues quoting the same security are one economic instrument in this stock-pair search. Do not rank an NSE listing against the identical BSE listing as a new company pair.

Within each formation period, select the venue with higher observed median turnover among valid complete listings; use a deterministic tie break. Freeze that venue for the resulting cohort. Do not switch each day to whichever exchange later provided the better price. Different share classes or changed ISINs require review rather than automatic joining. Unknown identities are quarantined with reasons.

The new catalog normalizer accepts NSE equity-list CSVs and BSE exports with Security Code/ISIN No/Security Name, or canonical code/isin/name fields. The current CSV mapping is a snapshot interface. Fully historical identity resolution remains a production data task.

## Data acquisition

Prefer bulk daily files to thousands of separate full-history website requests for full-market operation. Store raw files immutably with source URL, session date, checksum, retrieval time and parser version. Parse legacy NSE and UDiFF NSE/BSE schemas into canonical raw records. Legacy BSE files lacking ISIN require a dated master join; the parser refuses to invent identities.

Build adjusted paths from confirmed dividends, split/bonus events and other corporate changes. Preserve raw prices for eventual fills. Track exchange holidays and exceptional sessions against official evidence. A missing archive does not automatically mean a holiday, and a zero-volume library row does not automatically mean an active trading session.

The existing library connector remains useful for a bounded pilot. `bulk-download` caches each successful instrument, records failed and unattempted instruments, supports resuming the same request and stops on a provider rate-limit error. It does not claim that downloaded current survivors are an all-market historical dataset. Keep vendor data and detailed derived outputs local unless redistribution terms permit publication.

For zero library volume, `repair-volumes` can apply an official NSE overlay only if date, exact symbol, EQ series, positive official volume and compatible raw close agree. Every repair and unresolved case is recorded in a new immutable snapshot. It does not rewrite incompatible prices, discard bad dates or certify every corporate action. A broad source anomaly must not be hidden by relaxing eligibility.

## Scaling the distance search

For N distinct eligible securities there are N(N−1)/2 candidate pairs. With 5,000 securities that is 12,497,500 pairs per formation date. The implemented exact blocked calculation avoids a full pair-by-day tensor. It retains the best candidates using bounded distance blocks and direct distance recomputation for exported results.

All pairs use the same complete formation sessions. Mean SSD and sum SSD therefore have identical rankings; exports contain both. Do not compare distances computed on different overlaps or silently fill missing history. Missing, untraded, identity-unresolved and low-turnover instruments have reason-coded exclusions.

A measured synthetic scale test searched 5,000 paths of 252 sessions, returning the top twenty in approximately 3.24 seconds in this workspace with one BLAS thread. The temporary distance block was approximately 5.12 MB; this is not total process memory, an exchange-data benchmark or an operational SLA. At full scale the historical data audit and repeated cohort loading can dominate the numerical search.

## Forward research and return accounting

`distance-study` forms pairs monthly, uses no later observations for formation, renormalizes once at trading-window start, observes two-standard-deviation openings and subsequent crossings, and retains incomplete/nonconverging outcomes. Its counts are descriptive convergence evidence, not fills, annual returns or an investable portfolio.

Overlapping six-month cohorts are not independent observations. Report the number of formation months, selected pair-cohorts, complete forward windows, opening events, crossings and unresolved positions. Missing data is a separate failure category, not a losing/winning trade assumption. Preserve cohorts with no eligible pairs instead of silently dropping their months.

The capital backtester remains separate. Before promoting this method as a faithful GGR portfolio replication, implement six overlapping capital-accounted cohorts with the original crossing exit, next-session executable fills, end-of-period liquidation, delisting outcomes and committed/employed-capital denominators. The existing cash-share backtester is a risk-controlled distance variant, not that exact replication. Do not infer returns from crossing counts or multiply a z-score by an absolute daily return gap.

An executable Indian portfolio additionally requires historical futures or confirmed borrowing, lot sizes, margin, roll rules, dividends on both legs, financing and dated fees. Every later benchmark result must use complete Nifty TRI on matching dates and the same starting equity. Diagnostic-only snapshots with incomplete benchmark coverage remain barred from portfolio return backtests.

## Validation and release sequence

1. Verify catalogs, parser schemas and source access; publish exact coverage/failure counts.
2. Acquire a larger bounded history sample to validate the original distance pipeline.
3. Reconcile source anomalies and retain exclusions rather than manufacturing a full universe.
4. Run monthly formation/forward studies across 2005–2025, with 1/3/5-year formation experiments labeled separately.
5. Complete dated all-market identity, corporate-action and exchange-calendar history, including former listings.
6. Add exact cohort-capital accounting and realistic execution, then compare with TRI on an outcome-controlled evaluation.
7. Run live paper monitoring; produce entry/exit alerts only after current execution eligibility checks.

The previous correlation diagnostic code and tests are retained as historical research tools, not dependencies of the active selector. Cointegration remains an explicit legacy option in the earlier engine; the default strategy is now distance and the default sector restriction is off.

## Source access checked in this work

- NSE current listings: https://www.nseindia.com/static/market-data/securities-available-for-trading ; downloaded CSV: https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
- NSE dated archives: https://www.nseindia.com/all-reports ; verified UDiFF samples for 18 March and 8 September 2025 were used for conservative volume reconciliation.
- BSE listing page: https://www.bseindia.com/corporates/List_Scrips.html ; bhavcopy page: https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx . Both pages and tested direct download/API endpoints were inaccessible with HTTP 403 here.

Public availability and production-use entitlements are separate from technical access. The source audit and acquisition ledger, not the size of a current catalog, determine what historical coverage may be claimed.
