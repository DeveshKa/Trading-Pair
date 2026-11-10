# Paper 2 explained: Statistical Arbitrage in Pairs Trading
## A detailed guide in everyday language

Primary source: the supplied “Statistical Arbitrage in Pairs Trading,” file 67b7ae41ce55b1bf141b9f37_pairs.pdf, 10 pages. The supplied paper does not display author names or a publication date in its main text. PDF creation metadata indicate February 2023; this is not independent confirmation of publication. Prepared 10 November 2026.

This guide explains the paper and evaluates the clarity of its methods. It does not reproduce the backtest, train a model or verify the underlying Bloomberg data. All numerical teaching examples are explicitly marked as illustrations. Page references refer to the paper’s printed pages, which run from 1 to 10.

## Contents

1. What the paper investigates
2. The essential trading idea
3. Data and pair selection
4. Understanding the statistical screening tests
5. Copulas explained simply
6. The LSTM volatility model
7. How signals become trades
8. Worked trading and signal examples
9. Reported performance
10. What needs clarification before trusting a replication
11. Comparison with Paper 1
12. A guide to all thirteen figures
13. A practical research checklist
14. Glossary, common questions and source map

## 1. What the paper investigates

The paper studies a pairs trading strategy using the Dow Jones U.S. Health Care Index, abbreviated HC or DJUSHC, and the Dow Jones U.S. Pharmaceuticals Index, abbreviated Pharm or DJUSPR. It combines a statistical dependence model called a copula with a neural network called an LSTM.

The copula-related simulation asks whether the difference between the indices’ returns looks unusually large. The LSTM estimates volatility, meaning how much the indices’ returns might fluctuate. A second test compares their estimated variances. The strategy attempts to trade when both conditions point to divergence and exit when the relationship looks normal again.

The authors use 2005–2017 as training data and 2018–2022 as testing data. For their preferred configuration, they report a five-year cumulative return of 17.96%, an annualized return of about 3.36%, an annualized Sharpe ratio of 0.473 and a maximum drawdown of 13.8%.

These are the paper’s reported results. Important implementation details are missing or ambiguous, and some printed formulas need correction or explanation. In particular, its described return construction could introduce a favorable bias if implemented literally. Understanding that issue is as important as understanding the reported return.

Source: Sections 1–2, 4–6; pp. 1 and 3–9.

## 2. The essential trading idea

A pair trade combines two positions. The trader buys one asset, called the long leg, and sells short another, called the short leg. Short selling means borrowing an asset, selling it and later buying it back to return to the lender. A fall in the shorted asset’s price helps the position; a rise hurts it.

The goal is to benefit from relative movement. A trader might buy HC and short Pharm if HC appears temporarily cheap relative to Pharm. The trade can make money even if both indices decline, provided the long leg declines less than the short leg. It can lose money even if both rise, if the short leg rises more.

An index is a calculated measure, not a security that can be purchased directly. A practical implementation needs a suitable fund, derivative or basket of stocks. Its trading costs, tracking differences and shorting arrangements may differ from the index data. The paper models index-based trading without specifying a complete executable instrument arrangement.

The relationship is a tendency, not a contract. A pharmaceuticals-specific event may change the indices’ relative values permanently. Since broad healthcare and pharmaceuticals cover related businesses, their overlap and economic exposure also deserve examination. High correlation alone does not guarantee that a deviation is a mispricing.

The name “statistical arbitrage” can sound safer than it is. This strategy depends on a model being useful often enough to compensate for losses and expenses. It is not riskless arbitrage.

## 3. Data and pair selection

The paper says its dataset covers January 1, 2005 through December 31, 2022. It uses daily closing prices, rolling 200-day simple moving averages and daily volumes sourced from Bloomberg Terminal. Candidate indices include U.S. sector indices and Chinese-market equity indices. The complete candidate list and number of pair comparisons are not supplied.

The selected pair passes a four-stage process: normalize prices, test for cointegration, examine Hurst exponents and estimate mean-reversion half-lives. The reported screening statistics are:

| Measure | HC | Pharm |
| --- | --- | --- |
| Hurst exponent | 0.26 | 0.27 |
| Estimated half-life | 46.7 days | 52.8 days |
| Cointegration p-value for the pair | 4.21 × 10⁻⁵ | Same pair-level test |

The reported half-lives lie between the paper’s desired limits of one week and one year. The Hurst exponents are below 0.5, which the authors interpret as evidence of mean-reverting behavior. The small reported cointegration p-value supports rejecting a no-cointegration null if the correct residual-based test and assumptions were used.

A crucial timing question remains: did this screening use only the training period, or did it use the entire 2005–2022 history? The paper does not clearly settle that question. If later testing data influenced selection, the results would not represent a fully untouched out-of-sample evaluation.

Source: Section 3; pp. 1–3.

## 4. Understanding the statistical screening tests

### 4.1 Price divided by its moving average

The paper normalizes an index by dividing its daily price by its 200-day simple moving average, or SMA200. The moving average is the average of the relevant 200 daily prices.

Illustration: if the index is 1,050 and its SMA200 is 1,000, its normalized value is 1.05. If another index is 630 and its SMA200 is 600, its value is also 1.05. Both are 5% above their own recent averages, despite having different index levels.

This differs from starting both price series at one and accumulating total returns, as in Paper 1. Here the denominator changes each day. A normalized value can move because today’s price changes, because the moving average changes, or because both change.

Dividing by a moving average does not automatically prove statistical stationarity. Stationarity roughly means that a series’ statistical behavior remains stable over time. Tests and assumptions are still needed. It is also necessary to distinguish actual index returns from returns calculated on the normalized ratio. The latter are useful model inputs, but are not automatically the returns an investor earns on a traded asset.

### 4.2 Cointegration

Cointegration concerns series that individually wander but have a combination that remains stable. An everyday analogy is two people walking along a route while remaining linked by a loose rope. Their distance can fluctuate without drifting indefinitely apart.

The paper writes a relationship of the form S_HC(t) = beta × S_Pharm(t) + residual(t). It estimates beta by ordinary least squares and tests the residual for stationarity using an Engle–Granger approach.

The printed text refers to a “p-value of the regression.” For cointegration, the relevant evidence is the residual-based stationarity test with appropriate critical values, not merely whether the regression slope is statistically significant. Also, if both normalized series are already stationary, the usual interpretation of cointegration between nonstationary series needs reconsideration. An implementer should establish the series’ properties first.

### 4.3 Hurst exponent

The Hurst exponent, H, summarizes persistence patterns at different time scales. In common interpretations, H below 0.5 suggests anti-persistence; H above 0.5 suggests persistence. Values near 0.5 are often compared with a random-walk reference, depending on the estimator and the type of series.

The reported 0.26 and 0.27 are consistent with the authors’ mean-reversion interpretation. They do not guarantee convergence, prove that a pair spread is stationary or establish a profitable trading rule. The estimate depends on the method, sample and preprocessing.

### 4.4 Half-life

Half-life is the estimated time needed for a deviation from equilibrium to shrink by half. Illustration: a gap of 8 units would be expected to shrink to 4 after one half-life and to 2 after two half-lives under a stable exponential-reversion model. This is an average model tendency, not a deadline for any individual trade.

The paper prints a regression with lagged price on the left and its change on the right, followed by half-life = ln(2)/beta. This is not the standard mean-reversion regression and should not be copied without clarification.

A common discrete-time formulation is change in x(t) = a + b × x(t−1) + error(t), so the persistence parameter is phi = 1 + b. When 0 < phi < 1, half-life = −ln(2)/ln(phi). For b negative and close to zero, the approximation is −ln(2)/b. This is explanatory context, not a claim about the authors’ actual code. Their reported half-lives cannot be independently reconstructed from the information supplied.

Source: Sections 3.1–3.5; pp. 2–3.

## 5. Copulas explained simply

### 5.1 Separate individual behavior from joint behavior

Suppose two weather stations each have a distribution of temperatures. Knowing each distribution separately does not tell us whether hot days at one station coincide with hot days at the other. A copula describes how observations are linked after accounting for their separate distributions.

In the paper, the separate distributions are called marginals. The authors fit Student’s t-distributions to capture heavier tails than a normal distribution. A heavy tail means unusually large moves occur more often than a thin-tailed model would suggest.

Each observation is transformed through its cumulative distribution function, or CDF. A CDF value of 0.95 means the observation lies above about 95% of values under that fitted marginal model. The copula connects these probability-scale values into a joint distribution.

### 5.2 Gaussian copula and conditional probabilities

The paper says it uses a Gaussian copula fitted with Python’s statsmodels and copulas packages. It describes conditional probabilities: for example, how unusual an HC return is given the observed Pharm return. For suitable continuous distributions, partial derivatives of the copula give the relevant conditional CDFs, with careful attention to which variable is conditioned on.

However, the paper then states that it could not obtain the exact joint distribution and copula function through its tools and used an alternative simulation procedure. It generates simulated return distributions and takes their difference to create simulated spreads. This matters: the operational signal is described through simulated spreads rather than a fully specified conditional-probability trading rule.

A Gaussian copula with t-shaped marginals is not automatically a Student’s t-copula. Marginal tail thickness and joint tail dependence are different properties. A Gaussian copula does not capture the same asymptotic joint tail dependence as a typical t-copula with finite degrees of freedom. The paper’s general discussion of nonlinear or extreme dependence should therefore be read alongside its actual chosen model.

The reference to degrees of freedom produced by the copula is also unclear: a Gaussian copula itself does not have a t-distribution degrees-of-freedom parameter. Such a parameter may refer to the fitted marginals. A reproduction needs the exact simulation code and parameter definitions.

### 5.3 The simulated-spread z-score

The strategy compares the observed spread with the simulated spread distribution:

z = [observed spread − mean simulated spread] / standard deviation of simulated spread.

It treats a z-score outside approximately −2.58 to +2.58 as an extreme divergence under its 99% rule. This is a standard-normal cutoff. If the simulated distribution is heavy-tailed or asymmetric, actual simulated quantiles can differ from that cutoff. The claimed tail probability should be checked rather than assumed.

Source: Sections 4.1 and 4.3; pp. 3–4 and 6.

## 6. The LSTM volatility model

An LSTM, or long short-term memory network, processes sequences. It can preserve selected information from earlier observations while discarding other information. The input gate controls what is added to memory, the forget gate controls what is retained and the output gate controls what is passed onward.

Here, the intended prediction is volatility, not a direct prediction that an index will rise or fall. Predicting turbulence is different from predicting direction. A useful volatility forecast can still fail to produce a profitable trading strategy.

The paper describes an input matrix with five days and twelve features. Features include lagged volatility, volume and quantities derived from a regression. The complete twelve-feature list and all calculation windows are not specified.

The described processing chain is a one-dimensional convolution layer, an LSTM layer, dropout, another LSTM layer, a second dropout layer and a dense output layer. The model is applied to each index separately. The convolution extracts local patterns; the LSTM processes sequence information; dropout randomly suppresses some activations during training to discourage memorization; the dense layer produces the forecast.

Before fitting, the authors remove outliers, replace missing values with means and normalize features. Each operation must be learned using training data only and then applied to validation or testing data. Recomputing a mean, outlier boundary or scaling factor using the entire history would leak future information.

Mean squared error, or MSE, averages squared forecast mistakes. Large mistakes receive extra weight. The reported loss is about 64, but its meaning depends on the volatility definition, units and scaling. It cannot be called good or bad without a comparable baseline and held-out forecast errors. A falling training-loss curve alone does not establish predictive accuracy on unseen data.

The paper identifies regression alpha with drift and beta with volatility. In a general return-on-volatility regression, these coefficients are not automatically the parameters of a stochastic price process. Their role needs a precise mathematical specification. The volatility target, forecast horizon, layer sizes, training settings and output constraints also require clarification for reproduction.

Source: Section 4.2; pp. 4–5.

## 7. How signals become trades

The described workflow has two entry checks. First, the simulated-spread z-score must be outside the 99% interval. Second, a variance-comparison F-test must have a p-value below 0.05. If the checks support entry, the paper assigns signal 1; otherwise it assigns signal 0.

The variance ratio is written F = variance(HC) / variance(Pharm), using estimated volatilities from the LSTM. Under a classical F-test, the reference distribution depends on sample sizes, independence and distributional assumptions. A ratio of two neural-network forecasts does not automatically have that reference distribution. The paper does not supply enough detail to validate the p-values.

After entry, the intended trade buys the relatively low asset and shorts the relatively high asset. The text determines direction by comparing normalized price levels but also describes buying the low-return index. Relative normalized level and today’s return are not interchangeable. A precise rule must settle which information controls the position.

The copula is described as re-estimated daily during the testing period. Updating a model with newly available observations is a legitimate approach, but the execution must occur after the information used in that update becomes available. If the closing return at day t creates the signal, earning that same return with the resulting position would use future information relative to the trade decision.

The stated convergence exit requires the z-score to return inside its interval and the F-test p-value to become greater than 0.05. This raises an unresolved case: if only one entry condition stops holding, does the strategy exit or wait until both reversal conditions hold? The paper’s general signal-0 description and its explicit convergence description do not fully resolve that distinction.

The stop-loss discussion contains a likely inequality error. It says to close when cumulative return is “larger than −25%.” Taken literally, that would trigger at a small positive return or a small loss. A conventional 25% loss threshold would instead trigger at or below −25%. The intended implementation needs confirmation from code.

The stop-loss formula combines daily volatility, half-life and a risk-aversion constant of 2. The paper quotes annual S&P 500 volatility of 17.17% but does not adequately show how the time units and chosen half-life lead to 25%. Multiplying volatility directly by days is not the usual square-root-of-time approximation. The formula should not be treated as a validated universal rule.

A stop-loss can limit some losses, but cannot immunize a strategy against gaps, unavailable liquidity, borrowing recalls or execution delays. Source: Sections 4.3–4.4; pp. 6–7.

## 8. Worked trading and signal examples

### 8.1 An extreme spread — illustration

Suppose the observed return spread is 0.009, the simulated mean is 0.001 and its simulated standard deviation is 0.002. Then z = (0.009 − 0.001)/0.002 = 4. This exceeds 2.58 and passes the paper’s first screening rule. It does not by itself tell us which index to buy or guarantee convergence.

Suppose separately that the variance test returns p = 0.03 under a properly specified procedure. That would pass the second entry rule. If p = 0.20, it would not pass. These numbers illustrate the decision logic; they are not estimates for the paper’s pair.

### 8.2 Correct accounting for the two legs — illustration

Assume yesterday’s information says to buy HC and short Pharm today. Start each leg with $1,000 of exposure. If HC gains 1% and Pharm gains 0.4%, the long gains $10 and the short loses $4. Profit is $6 before expenses.

That is 0.6% of the $1,000 long-leg amount, or 0.3% of the $2,000 gross initial exposure. Return on actual posted equity depends on margin and financing. The denominator must be stated when comparing strategies.

If HC instead falls 2% and Pharm rises 1%, the long loses $20 and the short loses $10. The pair loses $30. A valid return calculation preserves this possibility.

### 8.3 Why absolute differences are dangerous

The paper describes absolute spread = |HC daily return − Pharm daily return| and multiplies this by a direction indicator derived from normalized prices. If an implementer also multiplies the same-day signed return difference by a position chosen from those same realized returns, it can become its own absolute value: sign(x) × x = |x|. This manufactures a nonnegative payoff before costs.

Even the paper’s stated absolute-spread-times-level-direction expression does not generally equal the profit of a fixed long–short holding. Valid daily profit must use the position established before the returns being earned, actual signed leg returns and the relevant quantities or weights. A return should not be forced positive merely because a divergence was observed.

This is a concern about the printed procedure, not proof that undisclosed code definitely contains the error. The reported backtest needs a trade ledger or code to settle it.

## 9. Reported performance

| Measure | Preferred configuration reported by the paper |
| --- | --- |
| Training period | 2005–2017 |
| Testing period | 2018–2022 |
| Spread screening | 99% interval, approximately ±2.58 |
| Variance screening | 95% F-test criterion |
| Trading signals | 208 |
| Five-year cumulative return | 17.96% |
| Annualized return | Approximately 3.36% |
| Daily Sharpe ratio, zero risk-free rate | 0.0298 |
| Annualized Sharpe ratio | 0.473 |
| Maximum drawdown | 13.8%, reported in 2022 |
| Correlation with S&P 500 returns | −0.1761 |

The annual return is consistent with compounding: (1 + 0.1796)^(1/5) − 1 is about 3.36%. Simply dividing 17.96% by five gives a different measure. Annualizing the daily Sharpe ratio using about 252 trading days gives 0.0298 × square root of 252, approximately 0.473. This standard scaling assumes conditions that may be imperfect for dependent returns.

Drawdown measures a fall from an earlier portfolio peak. Illustration: a peak value of $100 followed by $86.20 is a 13.8% drawdown. It is not the same as the worst daily loss or the probability of losing money.

The paper compares its 3.36% annual return with a reported S&P 500 average annual price return of 8.18%. The benchmark number is quoted as provided, not independently checked. A fair comparison should align dates, dividend treatment, compounding, exposure, costs and return denominators. The pair strategy’s lower headline return does not automatically imply worse diversification value, but diversification needs portfolio-level evidence.

The negative sample correlation suggests possible diversification benefits. It does not promise protection in every market decline. The discussion attributes market drops to 2019 and 2020; that date description should be checked against the benchmark series rather than repeated as a verified market chronology.

The authors also test 90% and 95% spread intervals, producing 412 and 320 signals respectively. The preferred 99% setting produces 208. Fewer extreme signals can reduce trading, but 208 signal observations are not necessarily 208 distinct completed round trips. Consecutive signal days may belong to one position.

The 99% configuration has the highest reported cumulative return, while 90% outperforms 95%. This is not a monotonic proof that greater confidence always produces better trades. Choosing among thresholds after looking at test performance also means that period has served partly as a validation set. A fresh holdout is needed to evaluate the final choice without this selection effect.

Source: Sections 5–6; pp. 8–9.

## 10. What needs clarification before trusting a replication

**Trading costs and executable instruments.** The paper does not provide a complete accounting of commissions, bid–ask spreads, borrowing, financing, market impact or the securities actually traded. It is therefore unsafe to describe 17.96% as verified profit after all practical costs.

**Information timing.** Pair selection, normalization, imputation, volatility features, daily refitting and execution must all use only information available at the decision time. The training/testing split alone does not ensure this.

**Return construction.** The absolute-spread expression must be reconciled with signed profits on lagged holdings. The equity denominator, compounding, cash treatment and trading frequency also need specification.

**Statistical foundations.** The normalization does not establish stationarity by itself. Cointegration needs the correct residual test. The half-life equation and forecast-based F-test need mathematical clarification. The normal z-cutoff needs checking against the simulated distribution.

**Model usefulness.** A training loss of 64 is not enough evidence. The LSTM should be compared with simple forecasts such as rolling historical volatility or another clearly defined baseline, using held-out errors. An ablation test should compare the full system with versions that omit the LSTM or copula. Without it, we do not know whether the added complexity improves trading.

**Scope of evidence.** This is one selected pair and a five-year testing window. It does not establish effectiveness across markets or future periods. Multiple screening and threshold choices add selection risk. Model complexity creates extra opportunities to fit historical noise.

These limitations do not make the research idea uninteresting. They identify the evidence required to move from a described experiment to a reproducible trading study.

## 11. Comparison with Paper 1

| Topic | Paper 1: Gatev, Goetzmann and Rouwenhorst | Paper 2: Statistical Arbitrage in Pairs Trading |
| --- | --- | --- |
| Main assets | Many individual U.S. stocks | One selected pair of U.S. sector indices |
| Main historical window | 1962–2002 data | 2005–2022 data |
| Normalization | Common-base cumulative total-return paths | Price divided by rolling SMA200 |
| Selection | Minimum historical squared distance | Cointegration, Hurst and half-life screening |
| Main signal | Two historical standard deviations of divergence | Simulated-spread z-score plus volatility test |
| Machine learning | None in the baseline | LSTM volatility forecasts |
| Exit | Crossing, delisting or end of six-month period | Convergence criteria and stated stop-loss |
| Cost analysis | Explicit discussion and robustness checks | No complete executable cost accounting provided |

The return numbers are not directly comparable. The studies differ in assets, dates, denominators, execution assumptions and expenses. Paper 2’s more complex model should not be assumed better simply because it uses neural networks. Paper 1’s larger historical result should not be assumed achievable in the later period either.

## 12. A guide to all thirteen figures

| Figure | What it shows | How to interpret it |
| --- | --- | --- |
| 1 | Pair selection procedure | Follow the filtering stages; check their training-period timing |
| 2 | Prices divided by SMA200 | Shows relative-to-trend behavior, not a proof of stationarity |
| 3 | HC fitted t-distribution | Illustrates marginal fitting; tail accuracy needs checking |
| 4 | Pharm fitted t-distribution | Same marginal-fitting question for the other index |
| 5 | Copula simulation and spreads | Visual fit does not establish predictive profitability |
| 6 | Simulated and observed spreads | Ask whether the comparison uses held-out observations |
| 7 | LSTM processing flow | Helps explain architecture, but is not a full training specification |
| 8 | Model loss | A decreasing loss curve alone does not establish test accuracy |
| 9 | Time-varying test-period correlation | Shows changing dependence; small variation does not prove only one asset moves |
| 10 | Cumulative performance at different confidence intervals | Compare settings while recognizing threshold-selection risk |
| 11 | Drawdowns across confidence settings | Shows losses relative to previous peaks |
| 12 | Drawdown for the 99% configuration | Contains the reported maximum drawdown of 13.8% |
| 13 | Cumulative return and normalized prices | Connects reported performance with index behavior; it is not an audit of P&L |

## 13. A practical research checklist

1. Fix a chronological training, validation and final holdout split before selecting pairs or thresholds. Record the candidate universe and every selection rule.
2. Obtain exact Bloomberg identifiers and document whether prices include distributions. Specify what “volume” means for each index and how an actual trading instrument maps to it.
3. Calculate SMA200 causally and define the initial warm-up period. Preserve separate series for actual asset returns and normalized modeling inputs.
4. Fit preprocessing on training data only. State the exact residual stationarity test, Hurst estimator and corrected half-life regression.
5. Document marginal distributions, Gaussian-copula correlation fitting, simulation method, random seed and tail cutoffs. Explain whether refitting uses an expanding or rolling window.
6. Specify all twelve features, forecast target, horizon, scaling, missing-value treatment, network settings and validation procedure. Compare against a simple volatility forecast.
7. Justify the variance-test reference distribution or replace it with a defensible comparison procedure. Set unambiguous entry, exit and stop-loss rules.
8. Use signals based on available information to establish holdings for later returns. Track signed positions and quantities, rather than treating an absolute return gap as profit.
9. Include executable prices, costs, borrowing, financing, capital requirements and forced exits. Reconcile daily P&L with every completed trade.
10. Report turnover, time in the market, completed trades, costs, annual returns, drawdown and uncertainty. Evaluate the final specification on untouched data and separate any modern extensions from the original method.

The paper proposes Bayesian hyperparameter optimization and alternative nonlinear copulas as future research. Both may be useful experiments. Neither replaces correct accounting, causal timing or an independent evaluation period.

## 14. Glossary, common questions and source map

### Quick glossary

**Mean reversion:** A tendency for a variable or relationship to move back toward a typical level.

**SMA200:** A simple moving average over 200 daily observations.

**Residual:** The part of an observation not explained by a fitted relationship.

**Cointegration:** A stable combination of otherwise nonstationary series under the relevant assumptions.

**Hurst exponent:** An estimate describing persistence patterns across time scales.

**Half-life:** Estimated time for a modeled deviation to shrink by half.

**Marginal distribution:** The distribution of one variable considered separately.

**Copula:** A function connecting marginal distributions into a joint distribution.

**Tail dependence:** The tendency for extreme observations to occur together.

**Volatility:** Variability of returns. Variance is volatility squared when both use the same units and definition.

**LSTM:** A neural network designed to process sequences with selective memory.

**Dropout:** A training technique that suppresses some activations to discourage memorization.

**MSE:** Mean squared error, a forecast-loss measure whose magnitude depends on units and scaling.

**p-value:** A measure of how surprising a statistic would be under a specified null model. It is not the probability a trade will fail.

**Z-score:** Distance from a mean measured in standard-deviation units.

**Drawdown:** Decline from a previous portfolio peak.

**Sharpe ratio:** Mean excess return divided by return variability under the chosen sampling convention.

**Look-ahead bias:** Using information in a historical decision that would not yet have been available.

### Common questions

**Does the LSTM predict which index to buy?** Its stated purpose is estimating volatility. Trading direction is assigned separately.

**Does a 99% threshold mean 99% of trades win?** No. It is a modeled statistical screening threshold, not a trade-success probability.

**Does a negative market correlation eliminate losses?** No. It is a sample association and can change; the strategy itself reports a substantial drawdown.

**Are the reported results independently confirmed here?** No. This guide checks the paper’s description and explains its numbers, but has not reproduced its data, models or trades.

**What should be verified first?** Establish signed, lagged-position P&L and causal information timing before adding model complexity or optimizing thresholds.

### Source map

| Topic | Source location |
| --- | --- |
| Research aim and index pair | Sections 1–2, p. 1 |
| Data, normalization and screening equations | Sections 3.1–3.4, p. 2 |
| Selected-pair statistics | Section 3.5, p. 3 |
| Copula and simulation method | Section 4.1, pp. 3–4 |
| LSTM architecture and preprocessing | Section 4.2, pp. 4–5 |
| Z-score and F-test | Section 4.3, p. 6 |
| Trading split, direction, exits and stop-loss | Section 4.4, pp. 6–7 |
| Reported returns and risk | Section 5, p. 8 |
| Threshold comparison and diversification discussion | Section 6, pp. 8–9 |
| Suggested extensions | Section 7, p. 9 |
| Bibliography | pp. 9–10 |

The supplied PDF is the sole primary source for the Paper 2 discussion. The comparison with Paper 1 refers to the previously supplied Gatev, Goetzmann and Rouwenhorst paper. General statistical explanations and the clearly labeled teaching examples are added for understanding; they are not new empirical findings.
