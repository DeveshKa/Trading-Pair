# v0.1 verification record

Checked in the coding workspace on 10 November 2026. This records tests actually performed, not production certification or an investment recommendation.

## Automated checks

The test suite covers signed gains and losses, next-session execution, split conservation of value, short dividend liabilities, deferred exits without a valid bar, NAV/trade-ledger reconciliation, future-data poisoning, cointegration multiple-testing correction, point-in-time membership boundaries, missing benchmark/duplicate rejection, exposure rejections, invalid configuration, provider split reconstruction, atomic failed downloads, explicit calendar exclusions and local alert idempotency/as-of scans.

Run `python -m pytest -q`. CI also generates the offline dataset and runs the cointegration-configured demo. A successful test run does not establish external provider availability on another day.

## Offline demonstration

The seeded generator created six invented assets in three sectors and a synthetic price benchmark. The 1,100-session demo completed selection, fills, fees, modeled borrow, closing trades, reports and local events. These are engineering fixtures, not Nifty data. The checked-in `examples/demo/` contains only synthetic output and labels it accordingly.

## Real library-data smoke test

- Provider: yfinance 1.8.0, downloaded 10 November 2026.
- Symbols: HDFCBANK.NS, ICICIBANK.NS, SBIN.NS and AXISBANK.NS; fixed, manually selected sample.
- Requested stock history: 1 January 2020 to 1 January 2025 exclusive.
- Source issue discovered: benchmark `^NSEI` lacked 14 November 2020 while stock observations included it. Strict download failed as intended.
- Explicit exploratory calendar-intersection mode excluded that session and recorded it. No event occurred on the excluded stock bars; the adapter rejects dropping corporate-action bars.
- Validated stock observations after the exclusion: 4,948 across four symbols. No historical membership supplied; actions remain unaudited.
- Snapshot hash: `a92cd6bfd7cc839e12f3f14fb7484ad3434fbc08892c840638a29916f3ea1a5a`.
- Configuration: `configs/library-smoke.json`, plus explicit `--exploratory`. Distance-screened threshold variant, 252-session formation, monthly reselection, top three candidates, 5 bps fees per fill, 10 bps slippage per leg and default 5% modeled annual short borrow.
- Evaluated NAV dates after formation: 4 January 2021 through 31 December 2024. Completed trades: 41; closed-position ledger reconciled to portfolio equity within one millionth of a rupee.
- Net strategy change: approximately **−2.88%** on starting capital. Nifty **price-index** change on the matched dates: approximately **+67.30%**. These are exploratory observations from the unqualified fixed-symbol sample, not a final Nifty backtest or TRI comparison. The negative strategy result was retained; no parameter search was performed to make it positive.
- As-of scanner produced research cards and explicitly blocked execution readiness. It did not send notifications or open broker positions.

The complete downloaded data and real-data run remain local under ignored `data/` and `runs/`; they are not redistributed in the repository. Provider revisions can change a subsequent download and therefore its snapshot hash and output.

## Report verification

The read-only report server served `report.html` and `summary.json` on loopback. An HTTP check confirmed the exploratory warning, benchmark label, equity SVG and summary values. This was an HTTP/content check, not cross-browser visual certification. JSON/CSV reports and the synthetic sample are available without a server.

## Remaining qualification

This is not the full point-in-time Nifty-universe evaluation in the planning document. Official membership/actions/TRI, complete historical execution costs, futures/SLB feasibility, production streaming, independent research validation and forward operation remain open. See the root README and original production plan for the next gates.
