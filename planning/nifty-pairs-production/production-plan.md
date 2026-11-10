# Nifty pairs trading: production system plan
## Data, research, backtesting, opportunity alerts and operating design

Version 1.0 • 10 November 2026 • Target repository: DeveshKa/Trading-Pair

This is an implementation-ready planning specification. Data-source pages and four sample archive URLs were checked during preparation. No complete historical dataset has been assembled, no pairs have been statistically selected, no performance has been backtested and no notifications or orders have been activated. All thresholds, budgets and service objectives below are proposed engineering or research choices, not empirical findings or promises of returns.

## 1. Recommendation and initial scope

Build a daily-frequency research and alert platform for historical Nifty 50 constituents, using official NSE equity archives, corporate actions and point-in-time membership. Compare strategies against the official Nifty 50 Total Return Index (TRI). Preserve a separate, clearly labeled comparison with the familiar Nifty price index.

Use the distance rule from Paper 1 as a transparent reference, then test a cointegration strategy informed by Paper 3. Add copula and LSTM experiments from Paper 2 only after the data, signed profit accounting and simple baseline are independently validated. Complexity must demonstrate incremental benefit on unseen data.

Separate statistical discovery from execution feasibility. A historically attractive pair is not automatically tradeable. For overnight trading, evaluate single-stock futures first and cash equities with confirmed securities lending and borrowing (SLB) as an alternative. Intraday-only cash shorts constitute a separate strategy requiring intraday data and a new backtest. Do not quietly convert the multi-day paper strategies into intraday signals.

The default delivery sequence is research → historical replay → live alerts → paper trading → a separately enabled, limited live pilot. The initial system supports read-only opportunities and simulated positions. The architecture includes a future broker adapter, but planning this adapter does not enable trading or authorize any orders.

Provisional scope: Nifty 50, India market hours, INR accounting, one portfolio, internal users, daily confirmed entry signals, live risk monitoring when a feed exists, and in-app plus configurable email/Telegram delivery. Nifty 100/200/500 are configuration extensions after source coverage and capacity are demonstrated. User preferences can revise these assumptions without invalidating the core design.

## 2. Requirements derived from the three papers

| Research lesson | System requirement | Evidence of completion |
| --- | --- | --- |
| Paper 1 separates twelve-month formation and six-month trading | Enforce a causal formation/trading boundary; version every cohort | A run can be replayed from frozen data and configuration |
| Paper 1 uses normalized total-return paths | Keep raw execution prices separate from corporate-action-adjusted research indices | Known split, dividend and merger fixtures reconcile |
| Paper 1 reports employed and committed capital | Track gross notional, equity, margin and capital reservation independently | Reports show denominators and reproduce the ledger |
| Paper 1 shows execution-delay and cost sensitivity | Next-session execution baseline and complete expense scenarios | No same-close fill from an after-close signal |
| Paper 3 critiques minimum distance alone | Test stable residual relationships, convergence and economic tradeability | Pair cards show statistical and execution rejection reasons |
| Paper 3 identifies multiple-testing and overfitting risk | Record every trial and apply a predeclared correction and walk-forward protocol | Final holdout never participates in selection |
| Paper 2 combines dependence and volatility forecasts | Optional copula/LSTM modules with causal features and simple-model comparisons | Ablations prove incremental out-of-sample usefulness |
| Paper 2 has ambiguous absolute-spread P&L and stopping rules | Signed holdings, explicit state machines and unambiguous stop conditions | Losing trades and partial fills are represented correctly |

The source papers motivate a method; they do not establish that it works for Indian stocks. Local market rules, taxes, contract sizes, borrowing and historical coverage are independent requirements.

## 3. Data-source decision

### 3.1 Recommended source stack

| Dataset | Preferred source | Use | Qualification still required |
| --- | --- | --- | --- |
| Daily equity OHLC, quantity, value, trade count, ISIN | NSE capital-market bhavcopy archives | Primary research price history | Full date coverage, schema changes, symbol/series history |
| Splits, bonus, dividends, rights, mergers and demergers | NSE corporate-action filings and issuer notices | Adjustments and event risk | Completeness, event interpretation and historical announcement times |
| Nifty membership | Official change records, reconstitution releases and archived snapshots | Point-in-time universe | Complete effective-date reconstruction; retrieved old XLS is not assumed current |
| Current Nifty 50 constituents | Official constituent CSV | Bootstrap and reconciliation | Current list cannot replace historical membership |
| Nifty 50 TRI and price index | NSE Indices historical-data reports | Primary and secondary benchmark | Date-range export, missing dates and TRI revision checks |
| Daily derivatives and contract metadata | NSE F&O reports, dated contract masters | Executable futures simulation | Expiry, lot sizes, eligibility, settlement, OI and historical margin coverage |
| Streaming quotes and bid/ask | Authenticated broker feed or authorized NSE vendor | Live opportunity validation and risk | Entitlements, latency, depth, disconnect behavior and display rights |
| Broker historical candles | Upstox or Kite, subject to account entitlement | Cross-checks and intraday expansion | Exact coverage and adjustment conventions per instrument |

Start with official exchange files rather than a single convenience CSV. Keep provider interfaces interchangeable. Public availability, stable automated access and permission for redistribution are separate questions. Confirm intended storage, internal use, non-display calculations and alert content against provider terms before production. Do not put downloaded market-data archives into the public GitHub repository by default. NSE describes a data-use policy and authorized real-time subscriptions [S1–S8, S12].

### 3.2 What was actually checked

The accompanying source_probe.json records URLs, UTC retrieval times, SHA-256 values, content types and observed schemas. It contains metadata rather than the downloaded data itself.

| Probe | Observation on 10 November 2026 | What this establishes |
| --- | --- | --- |
| Legacy equity archive, 5 July 2024 | HTTP 200; valid ZIP; 2,775 CSV records | Old-format archive is accessible and parseable |
| UDiFF equity archive, 8 July 2024 | HTTP 200; valid ZIP; 2,815 CSV records | New-format archive is accessible and parseable |
| Current Nifty 50 CSV | HTTP 200; 50 records | A current symbol/industry/ISIN reference is available |
| Official IndexInclExcl.xls candidate | HTTP 200; 820,736-byte Excel response | File retrieval works; content completeness and date coverage are not yet verified |

These counts include the source file’s wider equity universe, not just Nifty stocks. A successful two-date sample is not a certification of a twenty-year history. The membership workbook was not parsed or audited in this planning pass. Reconstruct later changes from official releases and reconcile daily/monthly snapshots; do not infer completeness from HTTP 200.

Observed schema mapping: legacy SYMBOL → symbol, SERIES → series, OPEN/HIGH/LOW/CLOSE → OHLC, TOTTRDQTY → traded quantity, TOTTRDVAL → traded value, TOTALTRADES → trade count. UDiFF uses TckrSymb, SctySrs, OpnPric, HghPric, LwPric, ClsPric, TtlTradgVol, TtlTrfVal and TtlNbOfTxsExctd. Both sample schemas contain ISIN. Preserve TradDt and BizDt separately in UDiFF and verify currency/unit definitions rather than relying only on column names. NSE lists the old-to-UDiFF transition in its reports [S1].

### 3.3 Sources to treat as secondary

The publicly listed Kaggle NIFTY-50 Stock Market Data (2000–2021) is a possible educational bootstrap [S11]. Its landing page was reachable but did not expose readable dataset content in this check. Its constituent history, adjustment method, completeness, update process and license have not been audited here. It cannot be accepted as the production source merely because its title says Nifty 50.

Unofficial wrappers and Yahoo-style downloads can help prototype connectors, but require provenance checks and are not an operational contract. Upstox documents daily V3 candles from January 2000 and minute/hour history from January 2022, with retrieval limits; these are provider claims to test per instrument, not guaranteed full-universe coverage. Its expired-instrument APIs are separately documented and may require a different plan. Kite documents historical candles and a continuous-futures facility; a continuous chart is not a substitute for individual contracts in P&L [S6–S7].

### 3.4 The minimum historical package

Target 2005–2025 complete calendar years, with optional 2000–2004 warm-up and a separate 2026 forward-replay period. Actual start date must be the earliest date for which prices, corporate actions and membership jointly pass audit. Shorten and label the sample if coverage is incomplete; do not silently fill missing companies with today’s constituents.

Required coverage includes former constituents, delisted or merged firms, symbol changes, event histories, trading calendars, Nifty TRI, and period-appropriate execution eligibility. For futures, add each expired contract, actual prices and settlements, lot sizes, rolls, corporate adjustments and dated rules. Daily equity data can support a research result, but cannot prove historical bid/ask execution, intraday stops or borrow availability.

## 4. Data model and quality controls

Use immutable source objects and three derived layers: raw downloads, canonical validated tables and frozen research snapshots. Every snapshot has a manifest containing source hashes, download times, parser versions, adjustment versions and coverage results. A correction creates a new version; past backtests never change silently.

Store at least these entities:

| Entity | Key fields and semantics |
| --- | --- |
| Security | Internal security_id, listing_id, ISIN history, symbol aliases, issuer lineage, exchange, segment, currency |
| Membership | Index, security_id, effective_from/to, announcement_at, known_at, provenance, confidence |
| Daily bar | Listing, session date, raw OHLC, volume, value, trade count, availability_at, source version |
| Corporate action | Type, ratio/cash amount, announcement and ex/record/payment dates, known_at, status, source |
| Adjustment | Security, date, price/share/total-return factors, algorithm version and source events |
| Contract | Underlying, expiry, lot size history, tick size, settlement method, trading status and effective dates |
| Quote/bar event | Instrument, event time, receipt time, sequence, bid/ask, quantities, interval and finalization status |
| Borrow/margin | Instrument, availability, fee or margin, expiry, observation time, validity and source |
| Model/pair | Pair_id, leg IDs, formation dates, coefficients, stationarity results, half-life, validity, artifact hash |
| Signal/trade | State, timestamps, holdings, fills, costs, model ID, reason codes, idempotency key |

ISIN is helpful but can change during restructuring. Do not make it the sole permanent identity. Preserve economic lineage without automatically joining pre- and post-merger businesses into one continuous tradeable stock.

Maintain raw prices for execution and an explicitly constructed total-return research index. Apply split/bonus events to quantities and prices consistently; include long dividend receipts and short dividend obligations. Cash payment and economic accrual dates are distinct. Validate rights, special distributions, demergers and mergers individually. Do not double-count dividends through both adjusted execution prices and cash flows.

For each daily batch, validate session calendar, file type and checksum, schema, uniqueness, EQ-series eligibility, positive prices, nonnegative volume, OHLC relationships, missing instruments and event reconciliation. Out-of-range changes create review cases, not automatic winsorization. Never forward-fill a missing price into a simulated fill. A stale mark can be retained for valuation only with a stale flag and a conservative exit assumption.

Required quality gates: zero duplicate canonical keys; zero unresolved price discontinuities for selected pairs; all selected bars have provenance; complete membership evidence for every formation date; all expected source files accounted for as received, exchange holiday or explicit exception. Cross-source checks use known adjustment differences, not a blanket price-equality rule.

Represent both economic event time and when information became available. A formation query must be an as-of query. Existing later corrections may be used in a corrected-data sensitivity run but cannot be confused with the original information set.

## 5. Strategy specifications

### 5.1 Baseline A: paper-inspired distance rule

Monthly formation; prior twelve months of total-return observations; exclude instruments lacking a valid traded observation on required formation sessions. Normalize each path to one at formation start, rank all eligible pair distances by SSD and retain top 5 and top 20 reference portfolios. Model six-month trading cohorts starting one month apart. Record duplicate handling explicitly: canonical unordered pairs, deterministic tie breaks, and aggregate security exposure across cohorts.

Keep two named variants. A0 replicates the paper’s economic idealization for comparison, clearly marking assumed short access. A1 applies the Indian executable universe and contract/borrow constraints. A0 performance cannot justify live deployment of A1.

Use a fixed two-formation-standard-deviation divergence threshold and crossing exit. Specify normalization at trading start consistently with the chosen GGR implementation; freeze its definition and test it against a hand-worked fixture. Close remaining positions at the six-month boundary or a required corporate/eligibility event. No same-day close execution from an after-close signal. The simulator executes no earlier than the next valid session’s open, with costs. Where a complete execution price is unavailable, label the run an idealized economic test.

### 5.2 Candidate B: cointegration with fixed residual model

At each monthly formation date, start from members effective on that date, use a sector-aware prefilter and liquidity/capacity filters, and exclude known corporate-event hazards. Announced future additions become eligible only on their effective date. At most 1,225 unordered pairs exist for fifty members before filtering. Deterministically choose a regression orientation so two directions cannot become two unreported attempts.

Fit log P_A = alpha + beta log P_B + residual on the trailing 252 valid sessions. Verify integration assumptions; run residual-based Engle–Granger with appropriate critical values. Predeclare lag/intercept settings and apply Holm familywise correction at 5% across the actual tested candidate family. Store raw and adjusted p-values, test statistics and every rejection. Diagnostic stationarity tests and alternative settings are not additional hidden ways to qualify a pair.

Estimate residual AR(1) persistence phi. For 0 < phi < 1, half-life = −ln(2)/ln(phi). Initial research acceptance band: 5–60 sessions; require positive beta, adequate residual variability after costs, and stable coefficients across predeclared formation subwindows. Do not optimize thousands of half-life/lag/window combinations on the holdout.

Freeze alpha, beta, residual mean and standard deviation during each trading cohort. Compute z = (residual − formation mean) / formation standard deviation. Proposed baseline entry: an outward crossing of +2 or −2 on a finalized daily bar. If z > +2, short A and long B; if z < −2, long A and short B. An existing candidate beyond the catastrophic-gap threshold is a rejection, not an invitation to enter at any magnitude.

Proposed exit: |z| ≤ 0.5, adverse spread |z| ≥ 4, maximum 60 sessions, pair-level loss limit, corporate-action invalidation or loss of execution eligibility. The loss stop triggers when P&L is at or below its negative limit, not above it. Gap-through stops fill at the next available executable price, not at the desired stop level. Freeze these as initial research parameters; alter them only through a recorded validation experiment.

Rank qualifying pairs by stable reversion, net convergence reward relative to forecast cost, and liquidity; then allocate through portfolio constraints. Do not rank solely by the smallest p-value or by the highest in-sample return. If no pair qualifies, remain in cash and explicitly report NO_QUALIFIED_PAIRS.

### 5.3 Optional experiments

OU thresholds can replace fixed boundaries after validation. Copulas can test conditional dependence with distributions fitted on training data and proper time structure. LSTM volatility models require targets, horizons, twelve-or-other explicitly defined features, causal normalization, time-ordered validation and calibration against rolling volatility or EWMA. Do not reuse Paper 2’s ambiguous forecast-based F-test or absolute-spread return construction.

Compare B versus B+OU, B+copula and B+LSTM separately. Add a combination only if its incremental net benefit remains stable after costs, trials accounting and fresh-data testing. These are research candidates, not the initial production dependency chain.

## 6. Indian execution and portfolio construction

An overnight cash short needs confirmed, term-appropriate borrowing and an executable lending arrangement; SLB eligibility is not evidence of availability or an acceptable fee. Broker documentation distinguishes intraday cash shorts, futures and SLB [S8–S9]. Missing historical borrow records imply a modeled-cost sensitivity study, not a verified executable cash result.

The preferred production candidate is a futures pair among historically eligible underlyings, subject to contract liquidity and capital. Discover pairs on adjusted underlying series but calculate returns on actual futures holdings. This introduces basis risk; a spot signal and a futures spread can diverge. Require both underlying validity and executable-contract price checks before eligibility.

Use matched expiry contracts where available. A proposed roll rule is to exit or roll five trading sessions before the actual expiry, using contemporaneously valid calendars and broker delivery cutoffs, whichever requires earlier action. Test two- and seven-session alternatives only in validation. Rolling closes old contracts and opens new ones with four leg fills and all costs; it is not a free price-series splice. NSE and broker contract and settlement rules are versioned inputs, particularly around stock-derivative delivery and expiry changes [S10].

For log-price beta, a local dollar hedge approximately uses rupee notional B = beta × rupee notional A. Convert into signed shares/contracts using current executable prices and actual lot sizes. Round to feasible integer lots, then recompute residual risk, market beta, margin and costs. Reject when the minimum lots breach the portfolio limit; do not assume fractional futures. Market-beta neutrality, cointegration neutrality and dollar neutrality are different constraints.

Initial illustrative limits: gross exposure ≤100% of starting equity; net rupee exposure ≤10%; one pair ≤15% gross; one underlying ≤15% gross across all pairs/cohorts; one sector ≤35% gross; daily portfolio loss pause at 1%; peak-to-trough pause at 8%; pair stop-risk budget ≤0.25% of equity; liquid cash buffer ≥30% of equity after modeled margin. Resolve all constraints simultaneously; they are not promised feasible for a small account. A sizing study must report the minimum viable capital per proposed portfolio using dated margins and stress losses.

Capacity: order size no more than a predeclared fraction of observed tradeable volume; initial daily-equity screening cap 1% of median twenty-session traded quantity, with stricter intraday participation and displayed-depth checks for execution. The 1% threshold is a ceiling for research sensitivity, not a guarantee of negligible impact. Exclude banned/restricted instruments using dated rules. No averaging down, doubling or automatic leverage increase in v1.

Pretrade checks include permissions, quote freshness, contract lifecycle, margin, borrow when applicable, event blackout, liquidity, portfolio exposure, conflicting signals and kill switch. Existing positions remain subject to exit/risk monitoring even when new entries are blocked.

## 7. Backtest and benchmark protocol

### 7.1 Evaluation design

Proposed periods: 2005–2015 development, 2016–2020 walk-forward validation, 2021–2025 sealed final evaluation. Each month selects on trailing information and trades prospectively within that partition. Features may use earlier history, but no training target or trade outcome from a later partition is permitted into fitting. Purge training outcomes crossing a validation boundary and embargo overlapping labels by at least the maximum label horizon. A 252-day formation lookback is not itself a future-label embargo.

Parameter choices are frozen after validation. The final period is run once per signed specification, with all later changes labeled new research requiring new unseen data. Because these are already historical years, an independent reviewer controls access to outcome reports where possible. 2026 forward replay and subsequent live paper observations supply further evidence; they are not invented here.

Report yearly and regime results, including high-volatility years, low-volatility years and major trend reversals. Exact regime definitions are fixed from training or public event dates rather than selected from favorable results. Store all variants, including failures.

### 7.2 Event-driven accounting

Signals use only finalized bars available at decision time. Fill at the next session’s raw open plus estimated slippage, or the next eligible intraday interval when that data exists. Daily OHLC cannot tell whether a stop and target were hit first; use a conservative worst-order convention or finer data, and label the assumption.

For equities: equity = cash + signed market value + accrued receivables/liabilities. Cash flows include purchases/sales, fees, dividends, borrowing and financing. For futures: posted margin is collateral, not the purchase price; book variation margin and fees without double-counting unrealized settlement gains. Reconcile cash, collateral, fills and NAV each day. Position chosen before interval t earns interval t’s signed returns; absolute differences never substitute for P&L.

Multiple signals compete for one capital pool. The simulator checks available funds and lot feasibility and can reject or resize trades. Include partial fills and an exposed single-leg scenario in executable testing. A missing fill does not become an assumed matched trade.

### 7.3 Costs

Keep a dated, instrument- and side-specific fee schedule for brokerage, exchange charges, SEBI charges, STT, stamp duty, GST on applicable bases, delivery-related charges, borrowing, funding, roll costs and slippage/impact. Personal income tax is reported separately because it depends on the investor. Verify schedules for the historical period and current broker; do not hard-code today’s rates across twenty years.

Provide gross, base-cost, doubled-variable-cost and delayed-execution results. Where quotes are unavailable, use explicitly modeled 5/10/20 basis-point-per-leg execution sensitivities plus applicable fixed/statutory fees; these are assumptions, not observed spreads. Never apply a whole-pair cost rate once when the strategy actually incurs separate entry, exit and roll fills. Backtest reports include break-even additional cost per trade and execution sensitivity.

### 7.4 Compare against Nifty fairly

Primary benchmark is Nifty 50 TRI on the exact portfolio dates [S3]. Start both at the same INR capital with the same external cash-flow convention. Strategy total NAV includes idle cash, collateral and its documented cash yield assumption. Also publish the strategy excess-of-cash series. TRI is an index benchmark, not a claim it can be bought without fees; an ETF proxy is a separate comparison with tracking error and expenses.

Publish price-index comparison as secondary and clearly label dividend exclusion. Report CAGR, annualized volatility, maximum drawdown, drawdown recovery, Sharpe with an explicit INR risk-free series, Sortino, Calmar, turnover, exposure, profit factor, hit rate, holding time, convergence rate, trade count and capacity. Calculate beta/alpha with robust standard errors and uncertainty intervals. A volatility-matched Nifty comparison uses only lagged volatility estimates and is supplementary to unscaled results.

Use block-bootstrap uncertainty to respect temporal dependence and report multiplicity-aware model comparisons. A higher Sharpe but lower CAGR can be a valid diversification result; do not market it as outperforming Nifty on absolute returns. Include paired monthly return scatterplots, rolling correlation, yearly tables and underwater charts. Show committed-capital, employed-capital and brokerage-equity figures separately so leverage cannot hide in a denominator.

### 7.5 Research promotion criteria

Before observing the final holdout, set candidate acceptance thresholds. Proposed targets: positive net holdout CAGR; net Sharpe ≥0.8; drawdown ≤10%; positive net return under doubled variable costs; no single security/year responsible for more than half of total profit; and stable direction of benefit in a majority of validation folds. Minimum evidence target: 100 completed portfolio trades and at least three calendar years, or explicitly classify evidence as insufficient. These criteria can fail, and that is a useful result.

Absolute-return outperformance of TRI is a separate objective: require a positive same-capital CAGR difference with uncertainty reported before making that claim. Production reliability does not rescue an unprofitable strategy. A well-built platform may correctly emit no trade opportunities.

## 8. Live signals and opportunity lifecycle

The daily model confirms entries only after finalized EOD data pass validation. Pre-close displays are provisional. An intraday quote feed can monitor the approved pair’s current residual, but it must not silently turn the daily strategy into a minute-trading model. Keep provisional watch alerts, confirmed setup alerts and execution-ready alerts distinct.

Proposed states: DISCOVERED → VALIDATED → WATCHING → SETUP_CONFIRMED → EXECUTION_CHECKED → PAPER_OPEN or EXPIRED. Open positions move through EXIT_DUE → CLOSED, with STOPPED, HALTED and REVIEW_REQUIRED branches. Future real positions use separate order states and broker reconciliation. Statistical entry, readiness to enter and actual fill are distinct events.

SETUP_CONFIRMED requires a finalized bar crossing the entry threshold under the current model. EXECUTION_CHECKED additionally requires valid quotes, contracts/borrow, costs, margin and portfolio limits. A setup can become blocked or expire without a trade. Revalidate immediately before a simulated or real entry; do not send a stale “trade now” message for yesterday’s price.

Calculate the gap as both model z-score and a return-equivalent economic quantity. For z > 0, residual convergence suggests A falls relative to beta-weighted B. Gross rupee reward is approximately notional_A × expected residual change for small log changes. This is a model scenario, not a reliable forecast. Show conservative cost estimates, net modeled convergence reward and estimated risk. Require a proposed net-reward/cost buffer, initially at least two times the estimated round-trip variable execution cost after fees, and reject if the estimate is unavailable.

An illustrative alert contains: pair and instrument IDs; direction and both quantities; spot versus futures basis; finalized signal time; quote time and freshness; z-score, entry/exit/stop levels; formation/model version; half-life and intended maximum holding time; cost range and convergence scenario; capital/margin; risk rejection reasons; expiry and roll deadline; and a unique opportunity ID. Display “watch,” “ready for paper entry,” “blocked” or “exit due” explicitly. No current pair is recommended by this document.

Alerts are edge-triggered, not sent every tick. Use hysteresis, configurable cooldown, opportunity TTL and model-version-aware deduplication. Send one confirmed entry and material-change alerts, then exits, stops, expiration and operational incidents. A stale data source suppresses new entry alerts and creates a data-health incident; it must never look like a quiet market.

The in-app inbox is the durable record. External channels are adapters: email first, Telegram optional, SMS only for configured operational escalation. Users opt into destinations and quiet hours; risk/exit escalation is separately configurable. Use a transactional outbox with event IDs, retries, exponential backoff, dead-letter queue and delivery status. At-least-once transport plus idempotent processing prevents duplicate opportunities internally; an external provider can still deliver duplicates, so do not promise exactly-once notification delivery.

Sample scenario, not a current recommendation: pair A/B reaches z = +2.2, so the proposed direction is short A, long B. If borrowing is unconfirmed or futures lots exceed margin, its state is BLOCKED and the message explains why. The system must not relabel that as an executable opportunity merely because the gap is large.

## 9. Architecture and implementation stack

Use a modular Python application with separate worker processes rather than many microservices at Nifty 50 scale. Shared strategy functions drive batch research, historical replay and live decisions. Keep data adapters, execution simulation, risk, notifications and API boundaries separate so each can be replayed and tested.

Proposed stack: Python, Polars/Pandas and NumPy; statsmodels/SciPy for statistical routines; FastAPI/Pydantic for APIs and contracts; PostgreSQL for metadata, state and ledger; S3-compatible storage with Parquet for immutable datasets and artifacts; DuckDB for research queries; a lightweight task worker/scheduler; React/TypeScript for the operator interface; OpenTelemetry with Prometheus/Grafana for metrics. These are architectural choices, not a requirement to deploy every product on day one. Introduce Redis or a managed queue only if measured delivery/worker requirements justify it.

Architecture flow: source adapters → immutable downloads → validation/identity/adjustments → frozen data snapshot → pair formation → model registry → shared decision engine → portfolio risk → backtest or live opportunity service → outbox → notifications. Broker reconciliation feeds position state back to the risk engine. API and dashboard read persisted state rather than recomputing signals independently.

Modules: data_ingestion, reference_data, corporate_actions, features, pair_selection, models, strategy, portfolio, accounting, simulator, market_stream, opportunities, notifications, broker_adapter, reports, audit and operations. Each has typed input/output contracts and explicit schema versions.

Proposed API surface: GET /data/health; GET /pairs and /pairs/{id}; POST /research/runs; GET /research/runs/{id}/report; GET /opportunities; GET /positions; GET /portfolio/nav; GET /alerts; POST /alerts/{id}/ack; and restricted POST /operations/pause and /resume. Research job creation returns a job ID. Use pagination, time filters and immutable model IDs. No live order endpoint is enabled in initial environments.

UI pages: data coverage with unresolved issues; pair explorer with normalized paths and residuals; run comparison with costs and benchmark; opportunity inbox with blocked reasons; simulated portfolio with exposure and P&L attribution; model registry and incident history. Every chart exposes data time, model version and whether values are research-adjusted or executable raw prices.

## 10. Runtime, resilience and security

Use exchange calendars and Asia/Kolkata for sessions, storing timestamps in UTC with timezone-aware display. Do not assume every weekday trades or hard-code an expiry weekday. Maintain pre-open readiness, market-session monitoring, post-close finalized-file polling, EOD reconciliation, model jobs and an overnight backup schedule. Set an initial expected EOD readiness target of 19:00 IST, revised after measuring upstream publication behavior.

Daily readiness checklist is automated: valid calendar and instruments, authenticated feed, clock sync, current membership/events, available risk state and notification transport. If a dependency fails, retain the previous model only within its validity window, block new entries when necessary and show degraded status. Restarting never clears an open position or re-emits every old entry.

Proposed SLOs: core API 99.5% monthly availability during defined service hours; opportunity generation p95 under 60 seconds after a complete validated event; provider-accepted notification p95 under 30 seconds after outbox creation; no silent stale feed; daily EOD run completes by its scheduled cutoff or emits a failure incident. These targets measure internal latency separately from upstream availability and human receipt.

For a streaming pilot, initial stale-quote threshold is ten seconds during the relevant liquid session, with a separately configured clock-skew allowance. Use event and receipt timestamps, reject out-of-order/replayed events and reconnect with gap detection. After a disconnect, reconcile bars and positions before restoring readiness. Public EOD files cannot meet an intraday quote SLO.

An immutable event log and SQL transactions support idempotent processing. A durable queue retries jobs with bounded backoff; a lease with fencing prevents two workers acting as the same scheduler/execution leader. Persist the opportunity transition and outbox event in one transaction. A restart resumes from checkpoints and replays to a deterministic state.

Monitor ingestion latency, missing rows, corporate-action exceptions, model age, p-value/half-life drift, residual breaks, rejected signals, quote age, concentration, P&L reconciliation differences, alert delivery errors and backup age. Drift triggers review or new-entry suspension according to policy; it does not silently refit open-trade models to make losing z-scores disappear.

Use authentication with MFA for operators, role-based access for viewer/researcher/operator/admin, server-side authorization, TLS, secret management, short-lived provider tokens where supported and redacted structured logs. Separate development, staging, paper and live credentials/accounts. Never commit secrets or market data requiring restricted distribution. Encrypt storage and backups; audit configuration changes and downloads. Retention periods are configurable and reconciled with provider and broker recordkeeping requirements.

Recovery design: daily object/SQL backups with point-in-time SQL recovery; restore rehearsal at least quarterly; proposed research/alerts RPO ≤24 hours and RTO ≤4 hours. A later live-order pilot needs durable order-event storage with effectively zero loss of acknowledged fills, broker-first reconciliation and a tighter operational response. No broker connectivity means no new orders; an independent broker interface and written position-exit runbook must remain available.

Runbooks cover source unavailable, schema changed, data revision, fake split gap, streaming disconnect, model failure, duplicate notification, secret expiry, margin shock, unmatched leg, broker rejection and database recovery. Assign a primary and backup operator; an unattended process with no incident owner is not production-grade.

## 11. Future order execution boundary

If enabled later, use a distinct order-management state machine: APPROVED → SUBMITTING → ACKNOWLEDGED → PARTIAL/FILLED/CANCELLED/REJECTED/UNKNOWN. UNKNOWN requires reconciliation, not blind resubmission. Two-leg trades are not inherently atomic. Record each fill and recompute exposure before sending or replacing the other leg.

Use marketable-limit orders subject to price caps, position limits and maximum unhedged time, with predeclared cancel/hedge/flatten rules. A “basket” interface does not remove leg risk. Idempotency keys, broker order IDs, bounded retry and fill reconciliation are mandatory. Kill switch blocks new risk and initiates a controlled exit process; it cannot guarantee an instantaneous fill in a halted market.

Current broker and exchange API/algo requirements must be confirmed for the intended route before activation. SEBI’s retail algorithmic-trading framework and NSE implementation material make broker participation and applicable API controls part of the deployment design [S13]. Record required static-IP/authentication arrangements, tagging, rate limits and approvals from the selected broker rather than assuming historical API behavior is still valid. Alerts for internal research and distribution of recommendations to outside users have different operational and authorization scopes; the v1 plan is internal.

## 12. Verification and release gates

| Gate | Required evidence | Owner |
| --- | --- | --- |
| Data foundation | Historical coverage audit, membership reconstruction, known-event adjustments, raw-file manifests | Data engineer and quantitative reviewer |
| Accounting | Hand-worked long/short, dividends, split, roll, margin and losing-trade reconciliation | Quant developer and independent reviewer |
| Research validity | Frozen protocol, full trial registry, walk-forward results, holdout and cost stress | Research lead |
| Replay parity | Identical decisions from batch backtest and event replay on identical inputs | Backend/quant engineer |
| Alert reliability | Replay shows one logical opportunity, retry/restart recovery and correct expiry | Backend engineer and operator |
| Paper operations | At least 60 trading sessions, no unresolved reconciliation incidents, realistic fill capture | Operator and research lead |
| Optional live pilot | Broker controls, capital viability, tested unhedged-leg runbook, explicit live enablement | Account owner and operations lead |

Meaningful automated tests include split/dividend conservation of value, short losses when price rises, next-bar chronology, membership effective-date boundaries, p-value correction families, future-feature poisoning, integer-lot rejection, full costs on every leg, no fills on missing bars, stop-gap slippage, futures MTM without double count, roll continuity, capital competition and benchmark NAV alignment.

Use metamorphic checks: shifting all post-cutoff observations must not change earlier decisions; renaming symbols with stable IDs must not change returns; doubling fixed holdings doubles gross rupee P&L but not necessarily costs or capacity. Integration tests exercise provider schema changes, outbox duplicates, interrupted downloads, expired tokens and restart reconciliation. A deterministic replay artifact includes a seed, code commit, dependency lock, configuration hash, data snapshot and full event ledger.

User acceptance means a nontechnical reviewer can open a pair card, understand the gap, see why a trade is blocked or eligible, find exact entry/exit assumptions and reconcile its contribution to NAV. Passing software checks is separate from passing strategy-performance gates.

## 13. Delivery roadmap, roles and budget

| Phase | Indicative elapsed weeks | Deliverable and exit condition |
| --- | --- | --- |
| 0: specification and procurement | 1–2 | Source rights/entitlements, data contracts, frozen evaluation protocol, broker feasibility |
| 1: data foundation | 3–5 | Validated price/event/membership snapshots and source coverage report |
| 2: reference research engine | 6–8 | Signed ledger, distance baseline, Nifty TRI reports and fixtures |
| 3: candidate selection | 9–11 | Cointegration walk-forward and cost/capacity studies; holdout protocol executed |
| 4: operational platform | 12–14 | Dashboard, replay-parity alerts, observability, recovery and access controls |
| 5: paper operation | At least 60 trading sessions after readiness | Forward fills, reliability and research evidence; no automatic live promotion |
| 6: optional live pilot | Separate release | Small capital, supervised execution and measured slippage |

These are estimates for a small experienced team, not guaranteed deadlines. Historical membership/corporate-action cleanup and vendor procurement can dominate the schedule. The paper phase can extend if too few trades occur or the strategy fails qualification.

Roles: quantitative researcher owns hypotheses and evaluation; data/backend engineer owns ingestion, ledger and runtime; frontend engineer owns operator UI; independent quantitative reviewer checks accounting and research leakage; an operator owns incidents and broker reconciliation. Roles can be combined in a small team, but independent review must remain independent of the implementation author.

Planning allowances, not vendor quotes: research-only storage/compute roughly ₹3,000–₹15,000 per month; redundant paper/alert operations roughly ₹15,000–₹50,000 per month before historical/live-data entitlements, messaging, personnel and any trade capital. Validate with deployment sizing and current vendor quotations. Enterprise data rights or a large historical cleanup can exceed these allowances. Alert channels and broker/API subscriptions have separate costs. Include a 20%–30% delivery contingency and operator support, not just development hours.

For Nifty 50, daily research is small enough for a single scheduled worker and SQL/object store. Intraday quote retention, broader universes or many users change sizing; measure before adopting distributed streaming or Kubernetes. Public-data research may be inexpensive, but a robust live service cannot be budgeted as “free data only.”

## 14. Backlog and definition of done

P0: evidence-backed source registry; permission/entitlement record; security master; historical membership and corporate actions; snapshot manifests; signed ledger; distance baseline; TRI comparison; causal replay; cost schedules. No candidate performance claim is accepted before these are complete.

P1: cointegration selection with multiplicity correction; capacity/lot sizing; portfolio allocator; execution feasibility; opportunity state machine; durable alerts; in-app inbox; metrics, access controls and restore drill. Completion requires an end-to-end replay from one source file to one auditable opportunity and a reconciled simulated position.

P2: futures-specific historical reconstruction and rolls where not already required for the chosen executable test; provider cross-checking; OU/copula alternatives; stronger drift monitoring; paper fill calibration. Copula and LSTM remain optional experiments, with an ablation requirement. Any executed strategy using futures needs the futures reconstruction before its executable results are accepted, regardless of backlog label.

P3: supervised live-order adapter after all earlier route-specific gates; multi-user notifications; broader Nifty universes; advanced models only if incremental evidence survives review.

Definition of done for the planning package: requirements traced to research; sources identified with evidence level; strategy and accounting specified; benchmark methodology fixed; data gaps and execution limits explicit; alerts, operating model, release gates, staffing and budget documented. Definition of done for the future system additionally requires working code, audited data, reproducible results and measured forward operation. This document does not assert those future deliverables already exist.

## 15. Decisions to resolve during implementation

The plan proceeds with Nifty 50, daily signals and internal paper/alert deployment. Before any cost-bearing integration, select a broker/feed and confirm entitlements. Before portfolio sizing, specify account capital, drawdown tolerance and whether futures or SLB is acceptable. Before enabling notifications, choose destinations and recipients. Before external distribution or live execution, confirm that route’s provider and broker conditions. These decisions do not prevent building the data and research foundation now.

The first concrete implementation milestone should be a data feasibility report, not a list of attractive pairs: establish how many historical constituents, dates and corporate events can be validated, then publish the earliest defensible backtest window and estimated execution coverage. Only the resulting audited snapshot should generate ranked pairs and Nifty-relative performance.

## 16. Source register

Sources checked on 10 November 2026. Documentation establishes described capabilities, not end-to-end data completeness or a contracted SLA. The repository’s three supplied research papers provide the research background.

S1 — NSE daily reports and UDiFF archive transition: https://www.nseindia.com/all-reports

S2 — Direct samples and retrieval evidence: see source_probe.json in this package. Legacy sample: https://nsearchives.nseindia.com/content/historical/EQUITIES/2024/JUL/cm05JUL2024bhav.csv.zip . UDiFF sample: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv.zip . Current membership: https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv . Membership-change candidate: https://archives.nseindia.com/content/indices/IndexInclExcl.xls . Successful retrieval is not a completed membership audit.

S3 — NSE Indices historical index and total-return reports: https://www.niftyindices.com/reports/historical-data

S4 — NSE corporate-action filings: https://www.nseindia.com/companies-listing/corporate-filings-actions

S5 — NSE historical reports entry point: https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives

S6 — Upstox V3 historical candles: https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/ ; expired instruments: https://upstox.com/developer/api-documentation/expired-instruments/

S7 — Kite historical candles: https://kite.trade/docs/connect/v3/historical/ ; streaming: https://kite.trade/docs/connect/v3/websocket/

S8 — NSE SLB features and eligibility: https://www.nseindia.com/static/products-services/slbs-features ; https://www.nseindia.com/static/products-services/slbs-clearing-settlement-eligible-securities

S9 — Zerodha’s documented short-selling routes: https://support.zerodha.com/category/trading-and-markets/trading-faqs/general/articles/short-sell-shares-in-eq-and-f-o-segments

S10 — NSE derivative contract specifications: https://www.nseindia.com/static/products-services/equity-derivatives-contract-specifications ; broker physical-settlement policy: https://support.zerodha.com/category/trading-and-markets/trading-faqs/f-otrading/articles/policy-on-physical-settlement

S11 — Secondary public dataset candidate, not content-audited: https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data

S12 — NSE data policy: https://www.nseindia.com/static/market-data/nse-data-policy ; real-time subscriptions: https://www.nseindia.com/static/market-data/real-time-data-subscription

S13 — SEBI retail algorithmic-trading framework: https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html ; subsequent timeline circular: https://www.sebi.gov.in/legal/circulars/sep-2025/extension-of-timeline-for-implementation-of-sebi-circular-dated-february-04-2025-on-safer-participation-of-retail-investors-in-algorithmic-trading-_96979.html ; NSE platform guidance: https://betanseapi.nseindia.com/static/trade/platform-services-non-neat-decision-support-tools-algorithm-trading
