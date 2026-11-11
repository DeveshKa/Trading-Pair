# Original distance method: larger-universe verification

Executed 11 November 2026. No correlation or cointegration threshold was used for candidate ranking in this increment. This record separates software checks, acquired history, valid formation windows and forward observations.

## Access and acquisition

The official current NSE equity export contained **2,633 rows and 2,633 distinct ISINs**. Current BSE list/API and bhavcopy attempts returned **HTTP 403**; the code supports official export ingestion, but no BSE-wide historical acquisition or result is claimed. Endpoint evidence is in `marketwide-source-checks.json`.

For the larger library pilot, 300 currently listed NSE stocks were requested. They were chosen from stocks with pre-2005 listing dates using end-2025 traded value, not selected by subsequent pair outcomes. That creates a **current-survivor/liquidity-selected exploratory sample**, not a point-in-time all-NSE backtest.

**285 passed snapshot validation; 15 failed with invalid OHLC relationships.** Every failure remains recorded in the acquisition ledger; none was converted into an empty success. The successful snapshots contain **1,473,437 stock-date observations**, spanning **3 January 2005–31 December 2025**. Acquisition uses resumable per-instrument snapshots, with a fixed request specification and a separate failure/unattempted ledger.

The provider has concrete quality issues. Zero-volume rows occur on several common dates, including 18 March 2025. Official NSE UDiFF files for that date and 8 September 2025 were fetched. Comparing official closes showed that the issue was not safely repairable as volume alone: a strict price-precision match permitted **zero volume repairs**, with **286 cases retained as unresolved**. Prices were not overwritten, dates were not silently discarded, and the original dataset remains immutable.

This quality failure prevents a usable latest-2025 formation shortlist under strict daily-trading requirements. The reported historical discovery cutoff is therefore **31 December 2024**, rather than pretending that the full downloaded range is equally reliable.

## Historical formation searches

At 31 December 2024, using 252 formation sessions and a ₹1,000,000 median daily traded-value floor:

- 285 observed securities were considered.
- **268 passed formation checks**, giving **35,778 distinct candidate pairs**.
- Sixteen failed complete/traded formation checks and one failed the turnover floor.
- The top twenty were ranked using exact mean/sum squared distance between normalized research paths, across sectors.

The first five historical candidates were Bajaj Finance/Kotak Bank, Kotak Bank/Procter & Gamble Hygiene and Health Care, Cyient/Tata Elxsi, Karnataka Bank/Titan, and BirlaNu/Procter & Gamble Hygiene and Health Care. These are **distance-ranking results at a past date**, not recommendations or evidence of current tradeability. Cross-sector combinations are deliberately allowed by the original unrestricted approach; closeness does not establish an economic equilibrium.

The separately labeled 756-session formation search at the same cutoff admitted **261 securities and 33,930 candidate pairs**. It is a sensitivity experiment, not a claim that the longer window is better. Data gaps and eligibility are evaluated independently for each formation window.

## Subsequent convergence observations

The rolling study used 252-session formation windows, monthly reselection and subsequent 126-session observation windows across the acquired history:

| Count | Observed value |
| --- | ---: |
| Formation months retained | 234 |
| Months with a nonempty selected set | 175 |
| Selected pair-cohorts | 3,500 |
| Forward windows passing observation/traded-data checks | 3,090 |
| Forward windows rejected for invalid observations | 410 |
| Two-standard-deviation opening events in valid windows | 5,598 |
| Subsequent crossings observed | 2,992 |
| Openings unresolved at their window boundary | 2,606 |

No-pair formation months and invalid forward windows remain visible. Overlapping cohorts and repeated pairs are not independent observations. The crossing/opening ratio is **not** a profit rate, capital return or annualized performance estimate. The forward observer does not simulate fills, borrowing, slippage or the six-cohort capital ledger. Portfolio returns and a complete TRI comparison remain separate qualification work.

These are conditional historical observations from an unaudited survivor sample. They must not be presented as historical all-exchange investment results. Library corporate-action treatment, dated identities and calendars still need exchange reconciliation.

## Scale and correctness

An independent **synthetic** scale test searched 5,000 complete 252-session paths, representing **12,497,500 candidate pairs**, and retained the best twenty in about **3.24 seconds** with a single BLAS thread. The temporary distance block occupied about **5.12 MB**, excluding input arrays and process overhead. This demonstrates numerical-search scalability, not full-market data availability or a production latency guarantee.

Automated checks cover exact agreement with a brute-force SSD calculation at multiple block sizes, absence of correlation/sector gates in discovery, ISIN-based duplicate-venue exclusion, formation-time-only venue choice, future-data invariance, missing/zero-volume rejection, disappearance after formation, separate subsequent windows, identical-path handling, NSE/BSE export normalization, raw BSE UDiFF identity and conservative official-volume overlays.

The active defaults are distance selection with no sector restriction. Earlier correlation and cointegration tools are retained as explicit historical research options and are not called by this discovery path. All generated detailed market-data outputs remain under ignored local `data/` and `runs/` directories.

## Reproduction and remaining gates

Use the root README commands for catalog normalization, bounded bulk acquisition, `discover` and `distance-study`. The pilot requested-symbol file is part of the local acquisition request. A new library download can differ because providers revise histories.

Full NSE/BSE support requires dated daily archives, adjusted total-return construction, former listings, issuer/security history, official session calendars and BSE source access. Before deploying any selected pair, also complete exact cohort-capital simulation, Indian costs, short/futures eligibility, margin/lot constraints and current quote validation.
