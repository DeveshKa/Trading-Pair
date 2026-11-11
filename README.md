# Nifty pairs research engine

Working research implementation of the [production-system plan](planning/nifty-pairs-production/README.md). The active direction is now the **original minimum-distance pairs method**, across a broader ordinary-equity universe. Correlation and cointegration are not gates in the new `discover`/`distance-study` path. Earlier diagnostic tools remain available only for reproducibility. Kite Connect is a future adapter; no broker credentials or external notification destinations are needed.

This is a tested research foundation, not a production trading release. The current simulator uses cash share holdings with modeled short availability and simplified fees. It does not establish that shorts could have been borrowed, that futures lots fit an account, or that the strategy beats Nifty after all Indian trading expenses.

## Interactive frontend

**Pairwise** provides searchable pair cards, company names, formation-window filters, divergence and distance filters, watchlists, CSV export, interactive price/spread charts, cohort history and data-quality details.

**[Open the private dashboard](https://pairwise-nse-research.rusticagave1.chatgpt.site)** — historical research dated 31 December 2024, with one-year and three-year formation screens.

```bash
nifty-pairs dashboard-demo --out runs/dashboard-demo
nifty-pairs serve --run runs/dashboard-demo
```

Open `http://127.0.0.1:8765/report.html`. The offline demonstration is explicitly synthetic. To display actual research artifacts or import a new snapshot, see the [dashboard guide](docs/dashboard.md). The hosted version is owner-private and uses the dated historical research snapshot, not live quotes. Browser visual QA remains unverified; automated DOM interactions and exporter tests are included in CI.

## Active direction: original distance method, broader NSE/BSE universe

Read the [all-market distance plan](docs/all-market-distance-plan.md). The new search compares normalized total-return paths without correlation/cointegration/sector screening. It chooses distinct economic securities, excludes duplicate NSE/BSE listings using ISIN, and records missing/untraded/illiquid/identity exclusions. It uses exact blocked SSD search rather than allocating all pair-by-date combinations in memory.

```bash
# Official local listing exports; BSE is optional until an export is available.
nifty-pairs catalog --nse-list /path/EQUITY_L.csv --bse-list /path/bse-list.csv \
  --out data/exchange-catalog.csv

# Bounded resumable library pilot, NOT full historic exchange coverage.
nifty-pairs bulk-download --catalog data/exchange-catalog.csv \
  --symbols-file /path/research-symbols.txt --limit 300 \
  --start 2005-01-01 --end 2026-01-01 --out data/broad

nifty-pairs discover --data data/broad/snapshot \
  --security-master data/broad/security_master.csv --exploratory --out runs/pairs

nifty-pairs distance-study --data data/broad/snapshot \
  --security-master data/broad/security_master.csv --exploratory --out runs/convergence

# Separate longer formation experiment, not a new correlation requirement.
nifty-pairs discover --data data/broad/snapshot \
  --security-master data/broad/security_master.csv --formation-sessions 756 \
  --exploratory --out runs/pairs-three-year
```

`distance-study` ranks on earlier formation paths, then observes six-month forward crossings. Its output is **convergence evidence, not capital-accounted trading returns**. Exact six-cohort GGR capital accounting and real execution remain separate work. The older `backtest` is a risk-controlled distance variant and still requires a complete benchmark; diagnostic-only snapshots cannot bypass that restriction.

The official NSE listing export retrieved on 11 November 2026 contained 2,633 entries. BSE pages/API/archive probes returned HTTP 403 here; BSE ingestion is covered by import fixtures, but no BSE-wide historical result is claimed. Full-exchange historical coverage must include former listings and audited corporate actions; a current catalog alone is not enough. [Verification notes](docs/marketwide-distance-verification.md) record the actual larger pilot and data issues.

## Quick start: offline demo

Python 3.11+:

```bash
git clone https://github.com/DeveshKa/Trading-Pair.git
cd Trading-Pair
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[library,test]'
python -m pytest -q

nifty-pairs demo --out data/demo
nifty-pairs validate --data data/demo
nifty-pairs backtest --data data/demo --config configs/demo.json --out runs/demo
nifty-pairs scan --data data/demo --config configs/demo.json --out runs/demo-scan
nifty-pairs serve --run runs/demo
```

Open **http://127.0.0.1:8765/report.html**. The offline data are invented, explicitly labeled, and require no network. A generated [example report](examples/demo/report.html) is included; download its folder to open locally, or run the commands above. GitHub itself shows the HTML source rather than hosting the report.

## First real-data library smoke test

The optional `yfinance` adapter supplies exploratory historical observations. This is distinct from the planned official-NSE audited dataset. The example uses four deliberately selected banking stocks, not historical Nifty membership. Keep downloaded market data local and check provider terms for your intended use.

```bash
nifty-pairs download \
  --symbols HDFCBANK.NS ICICIBANK.NS SBIN.NS AXISBANK.NS \
  --start 2020-01-01 --end 2025-01-01 --out data/library

nifty-pairs backtest --data data/library \
  --config configs/library-smoke.json --exploratory --out runs/library

nifty-pairs scan --data data/library \
  --config configs/library-smoke.json --exploratory --out runs/library-scan
```

`--end` is exclusive. If the provider lacks benchmark observations for stock sessions, strict download rejects the snapshot. Repair the benchmark for a proper evaluation. For an explicit smoke test only, use a **new destination** and add `--allow-calendar-intersection` to `download`; every omitted session is recorded in `manifest.json`, and an omitted corporate-action session is rejected. No benchmark prices are forward-filled. On the initial download, Yahoo's Nifty series omitted 14 November 2020, a stock-data session.

The default library benchmark `^NSEI` is the **Nifty price index, not TRI**. Imported official TRI values can replace it through the CSV contract. Reports display the benchmark type. `--exploratory` explicitly permits fixed-symbol/unaudited membership; it does not convert the run into an unbiased Nifty-universe evaluation.

The library adapter reconstructs raw share-unit execution prices from Yahoo split-adjusted OHLC using reported subsequent split events; adjusted close is research-only. This provider convention, dividends, extraordinary distributions, mergers and demergers need exchange cross-checks. The manifest therefore marks actions incomplete. Never regard a successful import as a full corporate-action audit.

## Earlier long-history diagnostics (retained; no longer selection policy)

Read the [detailed development plan](docs/long-history-pair-identification-plan.md). The new diagnostic layer examines **1/3/5/10/20-year horizons**, daily/weekly return correlation, rank correlation, block-bootstrap uncertainty, rolling correlation, market-residual correlation, and rolling cointegration with one conservative joint multiple-testing correction. It does not replace the trading selector or convert high correlation into a trade recommendation.

```bash
nifty-pairs download \
  --symbols HDFCBANK.NS ICICIBANK.NS SBIN.NS AXISBANK.NS KOTAKBANK.NS \
            TCS.NS INFY.NS WIPRO.NS HCLTECH.NS SUNPHARMA.NS DRREDDY.NS CIPLA.NS \
  --start 2005-01-01 --end 2026-01-01 --out data/long-history --diagnostics-only

nifty-pairs diagnose --data data/long-history \
  --universe configs/long-history-universe.json --exploratory --out runs/long-history

nifty-pairs serve --run runs/long-history
```

The curated twelve-stock pilot is not a historical Nifty universe. Diagnostic-only snapshots preserve all stock/corporate-action sessions despite benchmark gaps, and the backtester explicitly rejects them until the benchmark is completed. Reports preserve incomplete horizons and missing-session failures. [Initial long-history observations](docs/long-history-verification.md) record the actual pilot, including negative findings and source-calendar issues.

## Implemented

- Validated and hash-addressed CSV snapshots, atomic writes and source manifests.
- Effective-date membership intervals, exclusive end dates and missing-data rejection.
- Monthly distance-screened and cointegration-screened pairs; Holm correction and half-life diagnostics for cointegration.
- Frozen per-trade models; threshold-crossing entries; next-session opens; convergence, spread, loss, holding-time and drawdown exits.
- Signed holdings, integer initial shares, split adjustments, long/short dividends, per-fill fees/slippage and calendar-day borrow accrual.
- One capital pool with underlying, pair, sector, net and gross exposure limits. No fractional futures are simulated.
- Full selection audit, fills, trades, NAV and reason-coded opportunity/exit/block events.
- As-of gap scanner; it explicitly reports execution blocked until live quotes and borrow/contracts are validated.
- SQLite local event outbox with replay deduplication; no external delivery.
- Read-only local HTML report and machine-readable output, with benchmark and synthetic-data labels.
- Automated accounting, chronology, data-quality, provider and replay tests plus CI.

## Important boundaries

The distance mode is a distance-screened threshold **variant**, not an exact GGR reproduction: v0.1 does not implement six overlapping cohorts or the exact crossing-only exit. The cointegration mode fits log adjusted prices and checks integration assumptions, residual cointegration and half-life using formation data only. Sector metadata is required for the default same-sector filter; library smoke configuration explicitly disables it because the adapter does not infer point-in-time sectors.

Costs are configurable flat fee/slippage assumptions and modeled annual borrow, not a dated statutory schedule. Idle cash earns zero. Borrow accrues ACT/365 on the previous mark across calendar days while positions are carried. Dividend cash is recognized economically on the bar's ex-date, not delayed to payment date; this is an accounting simplification. Daily stops execute at a later available open and can gap. Missing exit bars defer the order and retain an incident; sample-end positions without a tradeable mark remain open and are reported. Nonpositive portfolio NAV halts the simulation with an explicit error instead of compounding invalid returns.

Historical replay uses monthly model formation and frozen models for open trades. `scan` deliberately refits an as-of candidate screen; it is a research diagnostic, not a running instance of the monthly portfolio and not an executable entry recommendation. It never claims `execution_ready=true`.

Production gates still outstanding include full point-in-time Nifty and action audits, official TRI ingestion, dated Indian fee schedules, real futures/SLB and margin feasibility, six-cohort baseline replication, sealed research evaluation, authenticated feeds, operational hardening, external channel opt-in/delivery and supervised paper/live operation. An authenticated Kite adapter alone will not satisfy these gates.

## Outputs and reproducibility

Each backtest writes `report.html`, `summary.json`, `equity.csv`, `config.json`, `data_manifest.json`, model/selection/fill/trade/event CSV and JSON files, `alerts.json`, `alerts.sqlite` and `run.json`. Run IDs include dataset files, configuration and source-code hashes. A new result directory is required, preserving previous runs.

Use `nifty-pairs alerts --run runs/demo` to inspect local pending events. Repeated writes of the same event do not create new outbox rows. Historical events are never sent to a messaging provider automatically.

The [data contract](docs/data-contract.md) describes imports and [Kite integration](docs/kite-integration.md) explains the future boundary. [Verification notes](docs/verification.md) record the first real-data smoke test. `requirements-tested-py312.txt` pins the tested Python 3.12 environment; other supported Python versions resolve compatible dependency versions through `pyproject.toml` and CI.

Raw data, run databases and secrets are ignored by Git. The checked-in example report uses only synthetic assets.
