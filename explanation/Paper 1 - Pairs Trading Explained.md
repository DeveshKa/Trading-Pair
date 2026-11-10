# Paper 1 explained: Pairs trading
## A detailed guide in everyday language

Based on “Pairs Trading: Performance of a Relative Value Arbitrage Rule” by Evan Gatev, William N. Goetzmann and K. Geert Rouwenhorst. Source: the supplied 2573.pdf, February 2006 version; cover label: Yale ICF Working Paper No. 08-03; first draft: June 1998. Prepared 10 November 2026.

This guide explains the supplied paper. It does not add new market data or reproduce the authors’ backtest. Numerical examples marked “illustration” are invented to teach the ideas. Source references use the paper’s printed page numbers, which differ from PDF viewer page numbers because of the cover.

## Contents

1. The main idea and research question
2. Essential concepts
3. Why the strategy might work
4. The data and complete trading procedure
5. Worked examples and simple mathematics
6. How returns are measured
7. Main findings and how to read them
8. Trading costs and execution
9. Risk, statistical tests and alternative explanations
10. Results over time and borrowing constraints
11. A guide to every table and figure
12. Strengths, limitations and modern research extensions
13. Reproduction checklist
14. Glossary, questions and source map

## 1. The main idea and research question

Imagine two companies whose investments have followed very similar paths for a year. One suddenly becomes more expensive relative to the other. A pairs trader buys the relative laggard and sells short the relative leader. The trader hopes their relationship returns toward its earlier pattern.

The important word is “relative.” The strategy does not need both stocks to rise. Both could fall and the trade could still make money if the stock bought falls less than the stock sold short. Conversely, both could rise and the trade could lose money if the shorted stock rises more.

The paper asks whether a simple, clearly specified version of this idea earned profits in historical US stock data, and whether those profits survive more realistic execution assumptions and explanations based on familiar investment risks.

The answer is encouraging within the historical study: matched pairs generated positive average excess returns, including under a one-day trading delay. The authors find that ordinary market factors and simple short-term reversal do not fully explain the results. However, execution costs reduce profits substantially, losing periods occur, and the authors identify evidence of a shared source of risk that their conventional models do not capture.

The often-quoted result of roughly 11% a year refers to historical annualized excess returns for a particular portfolio and accounting convention. It is not a promised return, and it is not the same as a present-day investor’s return after all expenses. Sections 6–8 explain the distinction.

Source: Abstract, Introduction and conclusion, printed pp. 1–3 and 30–31.

## 2. Essential concepts

**Long position.** You buy a stock. If its price rises, the position gains value; if its price falls, it loses value.

**Short position.** You borrow shares, sell them, and later buy shares to return to the lender. A fall in price helps you; a rise hurts you. Borrowing fees, availability and forced returns of borrowed shares matter.

**A pair.** Two stocks chosen because their past normalized investment paths were close. The paper does not simply choose companies with similar names, industries or raw share prices.

**Spread.** The gap between the two normalized paths. Here, spread means a difference between the investment indices. Later, “bid–ask spread” means a trading cost; these are different concepts.

**Convergence.** The gap closes. **Divergence** means it widens. A stock being cheap relative to its partner does not prove it is cheap relative to its true business value.

**Market neutral.** The long and short legs aim to offset broad market movements. Equal dollar positions do not guarantee perfect cancellation of risk: the companies may react differently to news or market shocks.

**Statistical arbitrage.** A trade based on a statistical tendency. Unlike textbook riskless arbitrage, its success is uncertain. The relationship can change permanently.

**Formation period versus trading period.** The formation period is the past data used to select a pair. The trading period is the later period in which that already selected pair is traded. Keeping them separate is essential to a fair test.

## 3. Why the strategy might work

The authors connect pairs trading to relative pricing. The Law of One Price says investments with identical future payoffs should have the same current value. Stocks in different companies are not identical investments. The paper therefore draws on a weaker idea: close substitutes may have closely related values.

Temporary buying pressure, selling pressure or overreaction could push their relative prices apart. Traders betting on convergence may help bring them closer. Earning a return for doing this could reflect correcting temporary mispricing, bearing risks, or both.

The paper also discusses cointegration. In everyday language, two series can wander over time while a suitable combination of them stays comparatively stable. Think of two walkers moving along the same route: each travels far, but the distance between them may remain bounded. Two walkers that happen to walk together for a short time may later head in different directions.

This distinction matters. Similar historical paths are not proof of a lasting relationship. The paper’s implemented selection method is a minimum-distance rule. It does not require every selected pair to pass a formal modern cointegration test. Calling it simply a “cointegration-tested strategy” would misdescribe the procedure.

The theoretical equation in the paper represents each stock price as exposure to common price components plus a stock-specific error. If the common components cancel in a combination of assets, the remaining component may be temporary. This motivates the trade; it does not establish that every actual pair has this property.

Source: Sections 1.3–1.5, printed pp. 6–10.

## 4. The data and complete trading procedure

### 4.1 Data and eligible stocks

The study uses daily US stock data from CRSP over 1962–2002. Initial observations are needed to form pairs. The main table reports 474 monthly observations, July 1963–December 2002. The data window and the reported strategy-return window are therefore different.

During each 12-month formation period, the authors remove stocks with one or more days without a trade. This seeks relatively liquid stocks and makes comparison of daily paths easier. It does not guarantee low trading costs or that stock borrowing is available.

### 4.2 Put investment paths on the same scale

For each eligible stock, construct a cumulative total-return index, including reinvested dividends, starting from a common value. This makes a $20 share and a $200 share comparable by investment performance rather than nominal share price.

For example, investments starting at an index value of 1 become 1.10 and 1.12 after gains of 10% and 12%. Their normalized gap is 0.02. Buying the lower raw-priced share is not the rule.

### 4.3 Match and rank stocks

For each stock, find the partner with the smallest sum of squared differences between their daily normalized paths during formation. Smaller distance means a closer past match. The authors examine the best five pairs, best twenty pairs, pairs ranked 101–120, and the broader all-pairs portfolio. “Best” here means smallest historical distance, not highest future profit.

In the unrestricted version, partners need not share an industry. Additional tests restrict matching to Utilities, Transportation, Financials or Industrials.

### 4.4 Trade for six months

Keep the selected pairs for a subsequent six-month trading period. Enter when the normalized price gap exceeds two historical standard deviations, estimated during formation. Buy the lower normalized path and short the higher one, using equal initial dollar amounts.

Close at the next crossing of the normalized paths. If no crossing occurs before the trading period ends, close at the end and recognize the gain or loss. If a stock is delisted, the authors close the pair using the delisting return or last available price. Pairs can reopen after they have closed if a new signal appears.

The original same-day version acts at the close associated with the signal. The more conservative version delays opening and closing until the following day. Unless stated otherwise, later tests generally use this delayed version. These versions must not be mixed when comparing results.

### 4.5 Start a new group every month

The researchers do not form just one set of pairs and keep it forever. A new six-month trading group begins every month after sufficient history is available. Six groups are therefore active at different stages once the process is running. Monthly strategy returns are averaged across these staggered groups.

This resembles six trading teams, each following its own formation and trading schedule. Overlapping observations affect statistical uncertainty, so the authors also use methods that adjust their standard errors for dependence.

Source: Sections 2.1–2.3, printed pp. 10–14.

## 5. Worked examples and simple mathematics

### 5.1 Comparing two potential partners — illustration

Suppose stock A’s normalized values on three sample dates are 1.00, 1.02 and 1.04. Candidate B has values 1.00, 1.01 and 1.03. Candidate C has values 1.00, 1.07 and 0.98.

Distance between A and B = 0² + 0.01² + 0.01² = 0.0002.

Distance between A and C = 0² + (−0.05)² + 0.06² = 0.0061.

B is the closer match. The actual study compares daily observations over a year rather than three selected dates. Squaring makes negative and positive differences both count and gives more weight to large mismatches.

### 5.2 Entry threshold — illustration

Suppose the formation-period standard deviation of the normalized gap is 0.025. Twice that is 0.05. A gap of 0.06 exceeds this simplified entry threshold. The higher path might be 1.12 and the lower path 1.06.

Two standard deviations means “large relative to the pair’s past fluctuations.” It does not mean a 95% chance of profit. The spread need not have a normal distribution, and the relationship can change.

### 5.3 Profit and loss — illustration

For simple arithmetic, assume both shares originally started at $100. Their normalized values of 1.06 and 1.12 correspond to prices of $106 and $112. Invest $1,000 in the lower stock and sell short $1,000 of the higher stock. This buys about 9.434 shares and shorts about 8.929 shares.

If both later reach $110, the long gains about $37.74 and the short gains about $17.86. Combined profit is about $55.60 before costs. Their normalized paths meet at 1.10.

If instead the long falls to $100 and the short rises to $120, the long loses about $56.60 and the short loses about $71.43. Combined loss is about $128.03 before costs. A wider gap does not automatically offer a safer trade.

The successful example’s profit is 5.56% of the $1,000 long-leg amount, or 2.78% of the $2,000 gross initial exposure. Actual brokerage equity and margin requirements create another denominator. Always state which capital amount a return uses.

### 5.4 The basic formulas

Normalized total-return index: N(t) = N(t−1) × [1 + r(t)], starting from N(0) = 1. Here r(t) includes the relevant dividend-adjusted return.

Pair distance: D(A,B) = sum over formation days of [N_A(t) − N_B(t)]².

Pair gap: S(t) = N_A(t) − N_B(t). The paper triggers a trade when the normalized divergence exceeds twice its historical standard deviation and exits at crossing. This should not silently be replaced by a rolling z-score, an estimated hedge ratio or a different exit threshold; those are different specifications.

For a single simplified holding period, equal-dollar profit is approximately L × r_long − L × r_short, where L is the initial amount of each leg. The full study marks positions to market daily and compounds returns rather than using this shortcut for all portfolio accounting.

## 6. How returns are measured

A long–short position initially buys one dollar of one stock while selling one dollar of another. Its net initial purchase cost is zero in the simplified accounting. This is why the paper describes the portfolio as self-financing and its payoffs as excess returns. Real trading still requires capital, margin and financing arrangements.

The paper uses two portfolio measures. **Committed-capital return** spreads payoffs across all pairs selected for trading, including pairs that do not open. **Fully invested return** scales payoffs by the pairs that actually open during the trading interval. The first allows for money committed to opportunities that may remain unused and is generally lower.

Illustration: if twenty pairs are selected but only ten ever trade, $100 of total profit divided by twenty $100 allocations is 5%. Dividing by ten $100 allocations is 10%. The trades have not become more profitable; only the denominator changed. This is an explanation of the distinction, not a replication of the paper’s daily weighting.

The authors mark long and short positions to market each day. Their portfolio calculations use evolving value weights with a buy-and-hold interpretation and compound daily returns into monthly returns. Uninvested cash is assumed to earn zero in the calculation discussed in Section 2.3.

Annualization also requires care. Multiplying a monthly average by twelve gives a simple annualized rate. It is not the realized compound annual growth rate. In particular, 0.895% × 12 = 10.74%, approximately the headline 11%, before the additional cost analysis discussed below.

Source: Section 2.3 and Table 1, printed pp. 12–14 and 34.

## 7. Main findings and how to read them

The following values refer to the unrestricted top-twenty portfolio in Table 1. They are historical sample statistics under the paper’s accounting, rather than a fully costed brokerage account result.

| Measure | Same-day version | One-day-delay version |
| --- | --- | --- |
| Average monthly excess return, fully invested | 1.436% | 0.895% |
| Average monthly excess return, committed capital | 0.805% | 0.520% |
| Monthly standard deviation, fully invested | 1.688% | 1.527% |
| Months with negative excess returns | 15% | 23% |
| Worst monthly excess return | −6.629% | −8.218% |

Delaying execution reduces the average return substantially. This tells us that the exact timing and prices used by a backtest matter. The delayed portfolio still has a positive average, but nearly one in four months is negative.

Diversification helps in this sample. Under the delayed rule, the top-five portfolio has a monthly standard deviation of 2.101%, compared with 1.527% for the top-twenty portfolio. More pairs can reduce company-specific risk. They do not necessarily remove common exposure or the risk that many relationships fail together.

The strategy is not restricted to utilities. Table 3 reports delayed top-twenty average monthly excess returns of about 1.084% for Utilities, 0.577% for Transportation, 0.775% for Financials and 0.607% for Industrials. These are separate sector portfolios, not components whose returns should be added together.

Portfolio composition matters: 71% of the stocks in unrestricted top-twenty pairs are utilities, and 74% are in the largest three size deciles. Their close historical paths partly reflect the kinds of stocks selected by the distance rule.

Table 2 reports about 19.30 of the twenty pairs trading during a six-month period, about 1.96 round trips per pair, and about 3.76 months of time open. Treat the last figure as reported open-time information over the interval, rather than automatically assuming each individual round trip lasts 3.76 months. The strategy studied is based on daily data, but it is not simply rapid intraday trading.

## 8. Trading costs and execution

The bid is the price at which someone is willing to buy; the ask is the price at which someone is willing to sell. An investor seeking immediate execution generally buys at the ask and sells at the bid. A recorded closing trade does not always represent a price available on both sides.

This creates bid–ask bounce. A stock may appear to have fallen simply because its most recent trade occurred at the bid rather than the ask. A backtest buying that recorded low and later selling a recorded high can show an apparent gain that is difficult to capture.

The one-day delay is an attempt to reduce this distortion. It may also miss genuine quick convergence. Therefore, the difference between same-day and delayed results is not a perfectly isolated measure of trading costs.

The authors use the drop in returns to infer a conservative trading-cost estimate. Their discussion implies approximately 162 basis points per pair per round trip, or 1.62%, and approximately 324 basis points for about two round trips over six months. The denominator is the paper’s pair-return convention, not an unspecified brokerage account balance.

They compare this with six-month profits of about 437–549 basis points and estimate about 113–225 basis points remaining after those costs, or 1.13%–2.25% per six months. A simple doubling would be about 2.26%–4.50% per year, but this is only an arithmetic translation of that discussion, not a separately measured annual performance result.

This is why “11% a year after all costs” would be an inaccurate summary. The delayed result is not an all-expenses-paid return. Commissions, market impact, stock borrowing, financing and practical margin terms need their own treatment in a deployable strategy.

The authors also identify two reasons the simple rule may trade too much. Selecting unusually close pairs may underestimate their future spread variability, causing entry too early. Entering near the end of the six-month interval also leaves little time for convergence before forced liquidation. They avoid optimizing these choices extensively because searching for the best historical settings risks overfitting.

Source: Sections 3.1 and 3.3, printed pp. 14–19.

## 9. Risk, statistical tests and alternative explanations

### 9.1 Market risk and other familiar factors

The authors compare strategy returns with market, size, value, momentum and short-term reversal factors. A factor is a return pattern that many investments may share. A regression asks how much of the strategy’s movement is associated with these patterns.

The regression intercept, often called alpha, is the average return left unexplained by that particular model. Positive alpha does not prove that every risk has disappeared. It says the included factors do not fully account for the results.

The paper finds positive risk-adjusted returns and generally modest exposure to conventional factors. It also tests an alternative set including stock and bond-related premiums. The results support the view that this is more than a simple broad-market bet.

### 9.2 Statistical significance

A t-statistic compares an estimated mean or coefficient with its estimated uncertainty. Newey–West standard errors with six lags are used in key tables because investment returns can be dependent over time and have changing variability. A large t-statistic supports evidence of a nonzero historical average under the statistical assumptions. It does not establish guaranteed future profit or solve implementation costs.

### 9.3 Is it just buying recent losers?

To investigate simple reversal, the authors replace real pairs with random stocks having similar previous-month returns. They repeat the exercise 200 times, using historical signal timing. These simulated pairs generally earn slightly negative average excess returns and have more variability.

The implication is that matching the two stocks matters. Merely buying a recent loser and shorting a recent winner does not reproduce the result in this experiment. This test does not rule out every possible alternative explanation.

### 9.4 Which leg contributes abnormal returns?

Separate analysis finds much of the risk-adjusted profitability on the short side. This is inconsistent with a simple story in which nearly all the reward comes from buying distressed companies that survive.

Do not confuse returns on the stocks that were shorted with the sign of the short position’s profit. If a shorted stock underperforms its factor benchmark, that can help a trader who is short even if the stock’s raw return is positive. Likewise, this result does not mean the long leg is useless: it is part of the relative trade and hedge.

### 9.5 Losses and historical value at risk

For the delayed top-twenty portfolio, Table 5 gives a worst month of about −8.218% and a worst day of about −6.723%. Its 1% monthly return percentile is about −1.943%, while the 1% daily percentile is about −0.647%.

These percentiles describe the observed distribution: roughly 1% of observations fall below that level. They are not maximum possible losses. An unfamiliar crisis or a permanent relationship break can be worse. The historical worst monthly return is also not the maximum peak-to-trough drawdown, which can span several months.

### 9.6 A shared source of risk remains

The top-twenty portfolio and pairs 101–120 move together even though the authors treat these portfolios as disjoint. Their full-sample raw return correlation is about 0.48; residual correlation after the five-factor adjustment is about 0.41.

This suggests a common influence missing from the standard factors. Its identity is not established. The authors interpret the evidence as consistent with compensation for risk involved in enforcing relative pricing. Possible modern stories about liquidity or crowding are useful research hypotheses, but should not be presented as causes proved by this paper.

Source: Sections 3.5–3.8 and Tables 4–8, printed pp. 20–28 and 37–41.

## 10. Results over time and borrowing constraints

The strategy does not earn the same amount in every era. In Table 8, delayed top-twenty average monthly excess returns fall from 1.181% in July 1963–December 1988 to 0.375% in January 1989–December 2002. Corresponding five-factor intercepts fall from about 0.670% to 0.417% per month and remain statistically significant in both subperiods.

Competition, lower transaction costs and more arbitrage capital could reduce opportunities. The authors also find that the shared factor between pairs portfolios is weaker in the later period. They do not establish one unique causal explanation for the decline.

The 1999–2002 holdout period is particularly useful because the strategy had already been developed and circulated. The introduction reports 10.4% annualized excess return for the fully invested top-twenty portfolio, with 3.8% annual standard deviation and a Newey–West-adjusted t-statistic of 4.82. A favorable four-year holdout can coexist with a weaker average over the broader 1989–2002 period.

Short selling raises two separate issues. Some shares are expensive or difficult to borrow. A lender can also recall borrowed shares before a trade is complete. The authors test pairs formed from the largest three size deciles and simulate recalls on unusually high-volume days. Profits remain positive under these checks; the simulated-recall top-twenty portfolio averages about 0.854% monthly excess return.

These are robustness tests, not a complete historical reconstruction of every borrow fee and recall. Large institutional investors may have access and terms that individual investors do not. Shorting feasibility is central to this strategy, particularly because the short side contributes much of its abnormal return.

Source: Section 1.2, Sections 3.8–3.9 and Tables 8–9, printed pp. 5–6, 26–30 and 41–42.

## 11. A guide to every table and figure

| Exhibit | What to look for | Why it matters |
| --- | --- | --- |
| Table 1 | Same-day versus delayed returns; fully invested versus committed capital | Shows how execution timing and denominators change performance |
| Table 2 | Trading activity, opening gaps, size and industry composition | Explains what the selection rule actually chooses |
| Table 3 | Separate portfolios within four broad sectors | Tests whether results extend beyond utilities |
| Table 4 | Sharpe ratios and risk-factor regressions | Tests familiar explanations of the average returns |
| Table 5 | Daily and monthly return percentiles and extremes | Makes historical losses visible |
| Table 6 | Random replacement pairs in 200 bootstrap replications | Tests whether simple reversal explains the effect |
| Table 7 | Long and short components separately | Identifies where risk-adjusted profitability arises |
| Table 8 | Earlier and later sample periods | Shows that performance and exposures change over time |
| Table 9 | Large-stock and simulated-recall checks | Examines selected short-selling constraints |
| Figure 1 | An example pair’s normalized paths and position changes | Makes divergence, crossing and repeated entry concrete |
| Figure 2 | Monthly top-twenty excess returns over time | Shows good and bad periods rather than only an average |
| Figure 3 | Cumulative pairs and S&P 500 excess returns | Illustrates historical relative performance under the paper’s accounting |
| Figure 4 | Rolling correlation of risk-adjusted pairs portfolios | Supports the discussion of a common unexplained component |

Read tables together with the text. The supplied draft contains apparent editorial inconsistencies: Section 2.2 dates the example interval to August 1962, whereas Figure 1 captions it August 1963–January 1964; some figure captions start the return series in May 1963, while the main tables specify July 1963. The main numerical summary here follows the tables’ stated 474-month window. These small discrepancies are a reason to verify exact implementation details rather than silently fill them in.

## 12. Strengths, limitations and modern research extensions

The paper’s strengths are its simple pre-specified strategy, long daily dataset, separation of formation and trading, multiple return denominators, delayed execution check, cost discussion, sector tests, risk-factor tests and later holdout sample. Together, these provide more evidence than a single attractive historical return chart.

Its limits are equally useful to understand. The data end in 2002. Market structure, competition, borrowing arrangements and execution technology have changed. Minimum historical distance does not guarantee a stable future relationship. The study’s cost estimates are indirect and its short-sale checks use proxies. The choice of benchmark factors cannot exclude unknown risks. Industry concentration and common exposure can limit diversification.

Some replication choices need additional specification. For example, one should explicitly document duplicate-pair handling, normalizing the trading-period paths, crossing detection, missing data, daily weights and the handling of signals immediately before the final liquidation date. A high-level description should not be treated as executable code with every edge case settled.

For a new study, first reproduce the distance-based baseline as faithfully as possible. Only then test changes such as formal cointegration screening, a fitted hedge ratio, different entry rules, limits on late-period entry or alternative exits. Label them as extensions. Mixing improvements into the baseline makes it impossible to tell whether you reproduced the paper or created a new strategy.

A modern evaluation would also need current point-in-time data, realistic tradeable prices, stock-borrow records, commissions, financing, market impact, concentration limits and truly unseen evaluation periods. These are recommendations for further work, not procedures all demonstrated in the supplied paper.

## 13. Reproduction checklist

1. Obtain a historical stock universe that includes firms that later disappeared. Using only current survivors can bias results upward.
2. Build daily total-return series with dividend and corporate-action treatment documented. Apply the paper’s no-missed-trade formation filter.
3. Use only the prior twelve months to normalize paths, compute distances, choose partners and estimate the gap variability.
4. Fix the pair list and formation estimates for the next six months. Record rankings and any duplicate handling.
5. Implement entry, next-crossing exit, re-entry, delisting and end-of-window liquidation explicitly. Keep same-day and delayed versions separate.
6. Track both legs each day. Record entries, share quantities, dividends, exits, unrealized gains, realized gains and borrowing assumptions.
7. Launch a new group each month and combine the staggered groups using a documented method consistent with the paper.
8. Report fully invested and committed-capital measures separately. State the return denominator and how annualization works.
9. Show results before and after a transparent cost model. Include losing months, daily losses, drawdowns and turnover.
10. Perform factor, sector, random-pair and subperiod tests. Use appropriate uncertainty estimates and reserve unseen data before tuning any extensions.

This is a research checklist, not a claim that the code or data needed to reproduce the paper have been supplied with this guide.

## 14. Glossary, questions and source map

### Quick glossary

**Basis point:** 0.01 percentage points. One hundred basis points equal 1%.

**Total return:** Price change plus investment income such as dividends, under the stated reinvestment convention.

**Normalized price:** An investment path put on a common starting scale.

**Mean reversion:** A tendency to move back toward a usual level or relationship.

**Correlation:** A measure of how series move together. It does not prove a lasting equilibrium relationship.

**Cointegration:** A property in which a combination of nonstationary series is stationary under the relevant statistical definition.

**Standard deviation:** A measure of variability; it does not describe every type of risk.

**Sharpe ratio:** Average excess return relative to return variability. It depends on measurement choices and can miss important features of losses.

**Alpha:** Return left unexplained by a selected risk model.

**Bootstrap:** Repeated resampling or simulated replacement used to study a comparison or uncertainty. Here the random-pair experiment preserves prior-return categories and trading timing.

**Delisting:** Removal of a security from an exchange or dataset listing; the associated loss or payment must be handled rather than ignored.

**Short recall:** A lender asks for borrowed shares back, potentially forcing an early exit.

**Data snooping:** Searching many historical rules and highlighting winners that may have succeeded by chance.

**Out-of-sample test:** Evaluation on data not used to develop the rule.

**Latent factor:** A shared influence inferred from the data but not directly identified in the model.

### Common questions

**Must partners be in the same industry?** No in the unrestricted strategy; yes in the separate sector-restricted tests.

**Does convergence require both stocks to rise?** No. Relative movement matters. Their paths can meet through rises, falls or a combination.

**Can a historically close pair lose money?** Yes. The gap can widen, remain open until forced liquidation, or reflect a permanent business change.

**Does the paper prove today’s profitability?** No. It evaluates historical data ending in 2002. No current-data backtest was performed for this explanation.

**Is the headline 11% a guaranteed net annual return?** No. It is an approximate historical annualized excess return under a specified portfolio convention, before the paper’s additional trading-cost discussion.

**What is the strongest practical lesson?** Evaluate the pair relationship, execution, cost assumptions and capital denominator together. An attractive spread chart alone is insufficient evidence.

### Source map

The sole primary source used for this guide is the supplied 2573.pdf. Its authors cite earlier work on relative pricing, cointegration, reversal, momentum and stock borrowing; this guide explains those connections as presented in the paper and does not claim independent verification of every cited study.

| Topic | Location in source, printed pages |
| --- | --- |
| Research question and headline result | Abstract and Introduction, 1–3 |
| History, data snooping and holdout | Sections 1.1–1.2, 4–6 |
| Relative pricing, cointegration and bankruptcy hypothesis | Sections 1.3–1.5, 6–10 |
| Pair formation and trading | Sections 2.1–2.2, 10–12 |
| Return accounting and staggered portfolios | Section 2.3, 12–14 |
| Profitability, composition and trading costs | Sections 3.1–3.3, 14–19; Tables 1–2, 34–35 |
| Sectors and conventional risk | Sections 3.4–3.5, 19–24; Tables 3–5, 36–38 |
| Random pairs and long/short attribution | Sections 3.6–3.7, 24–26; Tables 6–7, 39–40 |
| Subperiods, latent factor and short-sale tests | Sections 3.8–3.9, 26–30; Tables 8–9, 41–42 |
| Conclusion and figures | 30–31 and 43–46 |

The paper’s central contribution is evidence that carefully matched relative-price trades produced historical profits beyond simple reversal and familiar risk-factor explanations, while leaving substantial questions about costs, changing opportunities and common risk. Understanding those qualifications is part of understanding the result.
