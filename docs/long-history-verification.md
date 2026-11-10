# Initial long-history relationship pilot

Executed 10 November 2026. This is a descriptive research pilot, not a forward-selected strategy evaluation or a trade recommendation.

## Data actually acquired

- Provider: yfinance; adjusted research paths and reconstructed share-unit OHLC under the existing provider contract.
- Requested range: 1 January 2005 through 1 January 2026 exclusive.
- Actual stock range: **3 January 2005–31 December 2025**.
- Twelve stocks, five banking/four IT/three pharmaceutical; curated names and sectors declared in `configs/long-history-universe.json`, not an audited historical Nifty universe.
- **62,197 stock observations** and **19 same-sector pair combinations**.
- Snapshot digest: `2010b92f1b18b91083889f9673c98aae3f4b0c1410edba18152efb1a5f36230a`.
- **697 observed stock sessions absent from the downloaded Nifty benchmark**, largely in its early history as well as isolated later dates. A diagnostics-only snapshot retained them; no missing benchmark values were fabricated.
- One sparse observation date, **6 February 2010**, contains only one of the twelve stocks. Its exchange-session status needs official verification. This is not automatically labeled a bad print or removed. It creates explicit missing-window test statuses for affected pair windows.

Every pair has roughly 5,183 overlapping price observations. A twenty-year session window containing the sparse date can show descriptive return correlations but fails the contiguous-window requirement for cointegration. Complete coverage and a statistically valid regular-sampling window are separate fields.

## Analysis actually run

Each pair was profiled over trailing 252/756/1,260/2,520/5,040 sessions, approximately 1/3/5/10/20 years, ending 31 December 2025. Output includes actual dates, overlap counts, descriptive level correlation, daily Pearson/Spearman return correlations, weekly return correlation, paired moving-block bootstrap intervals, available-market residual correlations, yearly-window rolling correlations and three-year rolling spread tests.

The bootstrap used 200 repetitions, 21-session circular blocks and deterministic seeds. Cointegration tests used a fixed orientation, intercept, one lag and no autolag search. **798 pair/horizon/rolling hypotheses** were jointly adjusted using conservative Holm correction. This is a descriptive family as of the analysis date, not a historical trading rule secretly using future data.

Representative daily-return correlations are below. These figures measure shared changes, not whether a deviation can be traded profitably.

| Pair | Trailing 1-year return correlation | Historical median rolling 1-year correlation | Interpretation |
| --- | --- | --- | --- |
| Infosys / TCS | About 0.729 | About 0.625 | Recent shared movement is strong; recent stable-spread support is absent under this specification |
| ICICI Bank / SBI | About 0.293 | About 0.654 | Long-run typical co-movement hides substantial recent weakening |
| Axis Bank / ICICI Bank | About 0.379 | About 0.651 | A historically correlated pair needs recent relationship reassessment |

Across this pilot, six pairs met the descriptive latest-correlation threshold of 0.6 but lacked recent stable-spread support; thirteen had weak or unstable co-movement under the diagnostic labeling. No pair qualified for the initial `STATISTICAL_REVIEW_ONLY` tier requiring supported recent one- and three-year horizons. Some older rolling intervals had statistical support, which is retained rather than generalized to today's relationship.

This does not prove that all nineteen pairs are permanently unusable. It is a result of this dataset, deterministic orientation, test specification and conservative joint family. Incomplete corporate-action/sector/membership audits, data gaps and possible economic regime changes limit inference. No thresholds were loosened to manufacture a shortlist.

## Files generated locally

`runs/long-history-final/` contains `report.html`, `pairs.csv`, `windows.csv`, `rolling_correlation.csv`, `rolling_cointegration.csv` and full `diagnostics.json`. Raw market data and these detailed vendor-derived outputs remain under ignored local paths rather than being redistributed in the public repository. Reproduce them with the README commands; a changed source download can change the snapshot and the numbers.

The code rejects this diagnostics-only snapshot in the return backtester. It must first receive a validated complete benchmark and the wider data audits required by the production plan. It produces no execution-ready recommendation, notification delivery or brokerage order.

## Next evidence to obtain

Validate the sparse date and source actions; build official point-in-time membership; complete the benchmark; add dated sector exposure and formal break diagnostics; then integrate the reviewed qualification rules into monthly forward selection. The existing 252-session trading selector remains unchanged by this additive diagnostic release.
