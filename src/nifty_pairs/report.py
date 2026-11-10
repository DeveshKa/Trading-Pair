import html
import json
from pathlib import Path
import pandas as pd
from .alerts import AlertStore


def save_run(result, destination):
    path = Path(destination)
    path.mkdir(parents=True, exist_ok=False)
    result["equity"].to_csv(path / "equity.csv", index=False)
    for key in ("trades", "fills", "events", "selection_audit", "models"):
        pd.DataFrame(result[key]).to_csv(path / f"{key}.csv", index=False)
        (path / f"{key}.json").write_text(json.dumps(result[key], indent=2, allow_nan=False))
    for key in ("summary", "config", "data_manifest"):
        (path / f"{key}.json").write_text(json.dumps(result[key], indent=2, allow_nan=False))
    (path / "run.json").write_text(json.dumps({k: result[k] for k in ("run_id", "data_digest")}, indent=2))
    store = AlertStore(path / "alerts.sqlite")
    for event in result["events"]:
        store.put(f"{result['run_id']}:{json.dumps(event, sort_keys=True)}", event["date"], event["kind"], event)
    (path / "alerts.json").write_text(json.dumps(store.rows(), indent=2))
    frame = result["equity"]
    lo = min(frame.nav.min(), frame.benchmark_nav.min())
    hi = max(frame.nav.max(), frame.benchmark_nav.max())
    def points(series):
        return " ".join(f"{40 + i / max(len(series)-1, 1) * 900:.2f},{260 - (v-lo)/max(hi-lo, 1)*220:.2f}"
                        for i, v in enumerate(series))
    def escape(x): return html.escape(str(x))
    s = result["summary"]
    cards = "".join(f"<article><b>{escape(k.replace('_',' '))}</b><p>{escape(v)}</p></article>"
                    for k, v in {"source": s["data_source"], "benchmark": s["benchmark_kind"],
                                 "completed_trades": s["completed_trades"],
                                 "net_profit_INR": round(s["net_profit"], 2)}.items())
    table = "".join(f"<tr><th>{escape(k)}</th><td>{escape(s['strategy'][k])}</td><td>{escape(s['benchmark'][k])}</td></tr>"
                    for k in s["strategy"])
    warning = "SYNTHETIC DEMONSTRATION — invented assets, not Nifty performance." if s["synthetic"] else "EXPLORATORY RESEARCH — not an audited executable strategy or TRI comparison unless explicitly supplied."
    body = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Nifty pairs research report</title><style>body{{font:16px system-ui;background:#f4f6fa;color:#15283e;max-width:1100px;margin:32px auto;padding:20px}}h1{{margin-bottom:6px}}.warning{{background:#fff0c4;padding:18px;border-radius:8px}}section{{display:flex;flex-wrap:wrap;gap:15px;margin:25px 0}}article{{background:white;padding:20px;flex:1;min-width:180px;border-radius:12px}}svg{{background:white;width:100%;border-radius:12px}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{text-align:left;padding:12px;border-bottom:1px solid #ddd}}details{{margin:20px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}a{{color:#175ca4}}</style>
<h1>Pairs trading research</h1><p>Run {escape(result['run_id'])} · {escape(frame.date.iloc[0])} to {escape(frame.date.iloc[-1])}</p>
<p class="warning">{warning}</p><section>{cards}</section>
<h2>Same starting capital</h2><p>Blue: strategy NAV · Orange: {escape(s['benchmark_kind'])}. Fees and modeled borrowing included.</p>
<svg viewBox="0 0 1000 300" role="img" aria-label="Portfolio and benchmark equity curves"><text x="40" y="22">INR {hi:,.0f} (top) / {lo:,.0f} (bottom)</text><polyline fill="none" stroke="#1b65bc" stroke-width="2" points="{points(frame.nav)}"/><polyline fill="none" stroke="#cc6b18" stroke-width="2" points="{points(frame.benchmark_nav)}"/></svg>
<h2>Performance</h2><p>Returns and drawdowns are decimal fractions; CAGR/volatility/Sharpe use 252 sessions per year.</p>
<table><tr><th>Metric</th><th>Strategy</th><th>Benchmark</th></tr>{table}</table>
<h2>Research status and limitations</h2><pre>{escape(json.dumps(s, indent=2))}</pre>
<details><summary>Configuration and provenance</summary><pre>{escape(json.dumps({'config': result['config'], 'manifest': result['data_manifest']}, indent=2))}</pre></details>
<p><a href="equity.csv">Equity CSV</a> · <a href="trades.json">Trades</a> · <a href="selection_audit.json">All pair tests</a> · <a href="events.json">Opportunity/exit events</a> · <a href="alerts.json">Local alert outbox</a></p>
<p>No external alerts or brokerage orders were sent. Cash-short availability and Indian statutory fees are not verified in this release.</p></html>"""
    (path / "report.html").write_text(body)
    return path
