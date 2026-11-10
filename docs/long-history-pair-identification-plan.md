# Long-history pair identification: research and development plan

Version 1 • 10 November 2026 • Extension to the production plan and v0.1 engine

## The objective

Identify stocks whose relationship has been economically plausible, statistically stable and sufficiently tradeable across time. Answer three separate questions: have their investments moved together, does a tradable weighted spread revert, and can that behavior produce acceptable net returns in later unseen data?

A single correlation value cannot answer all three. Two rising price charts can have high price-level correlation despite weak correlation between daily changes. Two stocks can have highly correlated returns while their relative price drifts for years. A stationary fitted spread can still offer too little movement to cover costs or can stop reverting after a merger.

The next system should produce an evidence file for every candidate, including rejected pairs, rather than force a list of attractive-looking trades. A result of no qualifying pairs is valid.

## 1. Longer data, with a hierarchy of time horizons

Target daily history from January 2005 through December 2025, about twenty-one calendar years. Use earlier data where validated and available; do not require a newer listing to have existed in 2005. Keep 2026 and later observations separate for forward monitoring. Source start dates and valid common observations determine what can actually be claimed.

Separate three time scales:

| Role | Proposed horizon | Purpose |
| --- | --- | --- |
| Structural context | All available history and trailing 10/20-year windows | Detect old breaks, changing exposures and deceptively close charts |
| Qualification | Trailing 3/5 years, with 1-year and rolling checks | Establish a relationship relevant to the current market |
| Trade calibration | A predeclared trailing 1/3-year model, compared on validation only | Set hedge ratio and spread behavior without assuming a 2005 coefficient remains valid |

Use 252, 756, 1,260, 2,520 and 5,040 sessions as approximate 1/3/5/10/20-year windows; report actual dates as well. Twenty calendar years need not equal exactly 5,040 sessions. Display requested horizon, valid levels, valid returns, missing sessions and whether the entire horizon is present. Never print a 20-year correlation when only seven years exist without explicitly labeling it partial.

Longer history is evidence about change, not necessarily a better single regression. A pair that worked before a restructuring but broke afterward should not qualify because its full-sample average still looks strong.

## 2. Universe and data foundation

Production target: historical Nifty 50 membership at every selection date, including names later removed, merged or delisted. Expand to Nifty 100/200 only after data coverage and multiple-testing controls are operational. Preserve issuer identity and symbol history, not just today's tickers. Current constituents can seed a clearly labeled exploratory analysis but cannot establish an unbiased historical Nifty result.

The first long-history pilot uses twelve manually selected banking, IT and pharmaceutical names in `configs/long-history-universe.json`. This is a connector and diagnostic sample; it is not an audit of Nifty membership or dated industry classification. Its nineteen same-sector combinations exercise the pipeline. Cross-sector candidates require separate economic justification and a separately declared experiment.

Require adjusted total-return research paths plus raw execution prices and corporate actions. Reconcile dividends, splits, bonuses, rights, mergers and demergers against exchange records. In particular, mark major business-combination events as possible relationship breaks instead of joining them into a visually smooth chart and assuming equivalence.

Retain missing observations on a common session grid. Calculate daily returns only when both adjacent observations exist; do not bridge over an absent session and call the result a one-day return. Do not invent observations for a pre-listing period. For cointegration and half-life, require a complete contiguous window or explicitly reject the test, because dropping gaps changes the assumed sampling interval.

The library benchmark has gaps, including some stock corporate-action sessions. A `--diagnostics-only` snapshot preserves every observed stock session and records benchmark gaps. It may be analyzed for relationships but cannot enter the return backtester. Completing the official benchmark calendar is a separate release gate. This is preferable to throwing away corporate-action evidence or silently forward-filling Nifty.

## 3. Stage A: economic and eligibility screening

Start with economic plausibility: comparable business drivers, sector, regulation, revenue exposures and reasonable common influences. Examples are screening categories, not a recommendation to trade any named pair. Document sector classifications with effective dates and flag unknown or changed classifications.

Check liquidity over formation data, traded-day coverage, available history, corporate-event discontinuities and execution route. Reject securities that cannot be traded in the intended size, whose shorts are unavailable or whose futures contracts do not fit the capital budget. Keep the statistical and execution decisions separate so a pair can be statistically interesting but not tradeable.

Use deterministic unordered pair IDs and regression orientation. The full Nifty 50 contains at most 1,225 pair combinations before screening. Record the universe, exclusions and number of hypotheses. Do not choose whichever regression direction gives the most favorable p-value unless both directions are part of a declared, corrected experiment.

## 4. Stage B: measure past movement together

For each horizon, calculate the following with explicit overlap counts:

- Normalized total-return paths and descriptive log-price/price-level correlation, prominently marked as insufficient for selection.
- Daily log-return Pearson correlation for linear co-movement.
- Daily return Spearman correlation for rank co-movement and sensitivity to extreme observations.
- Weekly-return correlation using synchronized week endpoints, with partial-week and missing-data handling stated.
- A paired moving-block bootstrap interval for return correlation, preserving within-block serial dependence and the pairing of observations. A provisional block is 21 sessions and 200 repetitions for screening; final research uses more repetitions and a predeclared block-length sensitivity.
- Rolling return correlations: 63/126/252/756-session windows in the full specification. Initial diagnostic code implements the 252-session version sampled monthly plus the latest point.
- Down-market, high-volatility and named-period diagnostics, using fixed definitions rather than cherry-picked dates.
- Return correlation after removing an intercept and Nifty/sector exposure, to distinguish shared broad-market movement from a closer relationship. The initial code removes the available market factor only; sector-adjusted analysis is an extension.

Store rolling median, tenth percentile, latest value, changes from previous periods and the fraction of observations above a provisional 0.6 threshold. Those fractions describe overlapping windows, not independent success probabilities. Correlation intervals and thresholds are diagnostic evidence, not probabilities that a trade will win.

Rank direction matters. Positive correlation is the initial economic screen for conventional long–short stock pairs; negative relationships can require different exposures and belong to a separately specified strategy. Avoid choosing a pair just because a sample correlation is closest to one.

## 5. Stage C: test whether a spread is stable

Fit a hedge relationship on log research prices, checking whether the integration assumptions are plausible. A level ADF test that fails to reject a unit root is not proof of a unit root; preserve the diagnostic and its uncertainty. Use residual-based Engle–Granger testing with suitable critical values and predeclared lags. A regression slope's ordinary significance is not a cointegration test.

For each pair, report hedge beta, intercept, residual distribution, p-value, adjusted p-value, AR(1) persistence and half-life where defined. Use half-life = −ln(2)/ln(phi) only for 0 < phi < 1. Otherwise report undefined rather than inventing a positive estimate. Perfectly identical paths yield no useful spread and should be marked degenerate, not celebrated as a trade.

Long-window cointegration alone is insufficient. Compare recent 1/3/5-year fits and rolling 3-year fits stepped every six months. Inspect parameter changes, residual variance changes and current residual behavior. Long-window failure can coexist with a newer relationship; that belongs in a separate short-history or regime-specific research tier, not a false assertion of twenty-year stability.

Control multiple testing across the declared family. The initial diagnostic uses one conservative joint Holm family containing all reported pair/horizon and rolling cointegration attempts. It does not take the smallest p-value and ignore the other attempts. A future production formation process must predeclare its qualification family and treat historical stability tests as diagnostics, not endlessly add ways to pass. Alternative FDR procedures are research comparisons rather than a silent relaxation when Holm returns few candidates.

Add formal break detection in the next phase: rolling-beta variation, CUSUM or equivalent residual instability checks, known corporate-event boundaries and out-of-window residual diagnostics. Compare pre-event and post-event segments without using post-event knowledge in earlier trading decisions. A genuine economic break should invalidate the old relationship, not simply trigger a bigger position.

## 6. Stage D: qualification categories and ranking

Use separate categories, with reasons and missing evidence:

1. Insufficient or untrusted history.
2. Similar-looking price charts without robust return co-movement.
3. Correlated returns without evidence of a recent stable spread.
4. Statistically interesting relationship requiring review.
5. Forward-validated trading candidate.
6. Currently execution-eligible setup.

The initial diagnostic reaches category 4 at most. Every result has `execution_ready:false`. It cannot infer category 5 from in-sample correlations or category 6 without current contracts, borrowing, quotes, costs and capital.

Provisional qualification questions: does a pair have at least five years of validated overlap, strong recent co-movement, acceptable rolling deterioration, recent adjusted cointegration evidence, a reasonable positive hedge beta, estimated half-life compatible with the holding horizon and spread movement large enough after costs? A 20-year history enriches its evidence, but absence of 20 years must be labeled rather than automatically treated as failure.

Avoid a single arbitrary score hiding hard failures. First apply required gates; then rank survivors on separate stability, cost-adjusted convergence, liquidity and diversification dimensions. A statistical p-value is not a quality score. Ranking by fastest half-life alone can favor noisy or expensive turnover.

The initial code deliberately sorts the diagnostic table by rolling correlation, with the label visible, and preserves unsupported cointegration results. That ordering is a display choice, not the production allocation algorithm.

## 7. Stage E: establish out-of-sample usefulness

Full-history profiles are descriptive. They must not select a pair for a trade ten years earlier. In the eventual walk-forward selector, each monthly formation date uses only the history then available and the membership then effective. It freezes the selected coefficients for the following trading interval.

Separate development, validation and a sealed evaluation before comparing new selector variants. The prior four-stock 2021–2024 smoke-test outcomes have already been inspected; they cannot be described as an untouched holdout for this new research. Reserve independent evidence through an outcome-access-controlled evaluation and future paper observations. Historical retrospective comparisons remain useful but are labeled as such.

Compare the current 252-session selector, multi-horizon correlation screening, cointegration qualification and structural-break filters as distinct variants. Record all attempts. Keep entry, exit, costs and capital equal when measuring the incremental effect of better pair selection.

Evaluate per-pair and portfolio convergence rate, nonconvergence losses, time to convergence, adverse excursions, net trade expectancy, turnover and parameter survival. Report robustness to doubled execution costs, delayed entry and alternative market periods. A selected pair must contribute net out-of-sample value or diversification; a strong historical correlation alone does not qualify it.

Compare the portfolio with Nifty 50 TRI on matched dates and starting capital after completing official TRI coverage. Keep Nifty price-index results distinct. Include idle cash, borrowing or futures financing, dated statutory fees, integer lots and capital limits. Never derive profit from the absolute return gap.

## 8. Pair evidence card and alert integration

Each card should show:

- Names, IDs, dated sector classification, common-history dates, source and quality flags.
- Normalized paths; daily and weekly co-movement; the horizon table and confidence intervals.
- Rolling-correlation chart, regime table, raw and market/sector-residual correlations.
- Hedge ratio, residual/z-score chart, adjusted cointegration evidence and half-life.
- Break warnings, event annotations, expected holding horizon and model validity.
- Forward-validation outcomes, cost assumptions and capital feasibility when available.
- Current relationship state: insufficient, rejected, watch, under review, candidate or blocked.

The live system should alert on deterioration as well as widening: correlation collapse, hedge-ratio instability, residual breaks and a new corporate event. New entries stop when a relationship is invalidated; open positions follow their frozen risk/exit policy and operator runbook. Updating a model must not erase evidence that an existing trade failed.

## 9. Implementation sequence and acceptance

| Step | Deliverable | Acceptance |
| --- | --- | --- |
| 1 | Diagnostic-only long-history snapshot | Source hashes, real coverage and missing benchmark sessions recorded; backtesting blocked |
| 2 | Multi-horizon correlation evidence | Correct overlap, no gap-bridging returns, intervals and incomplete-horizon labels |
| 3 | Recent and rolling spread tests | Deterministic orientation, explicit assumptions, complete windows and joint multiplicity control |
| 4 | Regime/break and expanded visuals | Fixed regimes and known events; parameter deterioration visible |
| 5 | Monthly forward selector integration | Future-data poisoning does not alter earlier selections; membership as-of honored |
| 6 | Trading evaluation | Same accounting/costs versus baseline and TRI; all negative results retained |
| 7 | Live shadow monitor | Source freshness, model validity and relationship-break alerts before any order activation |

Steps 1–3 are the current additive diagnostic increment. The existing trading selector is not silently replaced. Remaining steps require explicit implementation and review. Initial engineering estimate: one iteration for diagnostics and data gaps, one for break/regime evidence, and one for forward-selector comparisons; actual delivery depends on official data reconstruction.

Test requirements include high price-level/low return correlation, correlated random walks without a stable spread, known cointegrated synthetic series, structural breaks, shorter listings, missing sessions, constant/duplicate series, as-of invariance, Holm family accounting and block-bootstrap reproducibility. Backtest regression tests must remain unchanged unless the strategy version explicitly changes.

## 10. Method references

The three supplied papers remain the primary research basis. Statistical API assumptions were checked against the official documentation on 10 November 2026:

- Engle–Granger cointegration test and its assumptions: https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html
- Pearson correlation and assumptions behind its conventional p-value: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html

This design uses paired block-bootstrap intervals for descriptive financial-return correlations rather than interpreting the default independent-normal-sample p-value as a trading probability. Data rights, historical corporate actions and membership still follow the original production-system plan.
