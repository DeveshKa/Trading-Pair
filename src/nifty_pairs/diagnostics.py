"""Long-history relationship evidence. Diagnostic output is not a trading selector."""
from dataclasses import asdict, dataclass
from itertools import combinations
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller, coint
from .data import Dataset


@dataclass(frozen=True)
class DiagnosticConfig:
    horizons: tuple = (252, 756, 1260, 2520, 5040)
    rolling_correlation_sessions: int = 252
    rolling_coint_sessions: int = 756
    rolling_step: int = 126
    bootstrap_repeats: int = 200
    bootstrap_block: int = 21
    alpha: float = .05
    minimum_coverage: float = .98
    seed: int = 42

    def __post_init__(self):
        if not self.horizons or any(type(h) is not int or h < 40 for h in self.horizons):
            raise ValueError("Horizons require at least 40 sessions")
        if self.bootstrap_repeats < 20 or self.bootstrap_block < 1:
            raise ValueError("Invalid bootstrap specification")
        if not 0 < self.minimum_coverage <= 1 or not 0 < self.alpha < 1:
            raise ValueError("Invalid coverage or alpha")
        if self.rolling_step < 1 or min(self.rolling_correlation_sessions, self.rolling_coint_sessions) < 40:
            raise ValueError("Invalid rolling-window specification")


def finite(value):
    return float(value) if np.isfinite(value) else None


def corr(x, y):
    if len(x) < 20 or np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return None
    return finite(np.corrcoef(x, y)[0, 1])


def correlation_interval(x, y, config, seed):
    """Paired circular moving blocks, preserving within-block time order and pairing."""
    if corr(x, y) is None:
        return [None, None]
    rng = np.random.default_rng(seed)
    n = len(x)
    count = int(np.ceil(n / config.bootstrap_block))
    samples = []
    for _ in range(config.bootstrap_repeats):
        starts = rng.integers(0, n, size=count)
        ix = ((starts[:, None] + np.arange(config.bootstrap_block)) % n).reshape(-1)[:n]
        value = corr(x[ix], y[ix])
        if value is not None:
            samples.append(value)
    return [float(v) for v in np.quantile(samples, [.025, .975])] if samples else [None, None]


def relationship_test(levels):
    """One deterministic orientation. Caller corrects the entire reported test family."""
    x, y = np.log(levels.iloc[:, 1].to_numpy()), np.log(levels.iloc[:, 0].to_numpy())
    result = {"pvalue": 1., "beta": None, "half_life": None, "level_adf_pvalues": [None, None],
              "integration_compatible": False, "test_status": "DEGENERATE"}
    if min(np.std(x), np.std(y)) < 1e-10:
        return result
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            beta, intercept = np.polyfit(x, y, 1)
            residual = y - intercept - beta * x
            p = finite(coint(y, x, trend="c", maxlag=1, autolag=None)[1])
            adf = [finite(adfuller(v, maxlag=1, autolag=None)[1]) for v in (y, x)]
            phi = np.polyfit(residual[:-1], residual[1:], 1)[0] if np.std(residual) > 1e-10 else 1
            half = finite(-np.log(2) / np.log(phi)) if 0 < phi < 1 else None
            result.update(pvalue=1. if p is None else p, beta=finite(beta),
                          half_life=half, level_adf_pvalues=adf,
                          integration_compatible=all(v is not None and v > .05 for v in adf),
                          test_status="OK" if np.std(residual) > 1e-10 else "DEGENERATE")
            if result["test_status"] != "OK":
                result["pvalue"] = 1.
        except (ValueError, np.linalg.LinAlgError):
            result["test_status"] = "FAILED"
    return result


def correct_family(rows, alpha):
    if not rows:
        return
    # Missing/invalid tests contribute p=1 rather than disappearing from the declared family.
    adjusted = multipletests([r.get("pvalue", 1.) for r in rows], alpha=alpha, method="holm")[1]
    for row, value in zip(rows, adjusted):
        row["holm_pvalue"] = float(value)
        row["cointegration_evidence"] = bool(value <= alpha and row.get("integration_compatible")
                                             and row.get("test_status") == "OK" and (row.get("beta") or 0) > 0)


def diagnose(dataset: Dataset, config=None, as_of=None, sectors=None, same_sector=True):
    c = config or DiagnosticConfig()
    cutoff = pd.Timestamp(as_of) if as_of else dataset.bars.date.max()
    source = dataset.bars.loc[dataset.bars.date <= cutoff]
    if source.empty:
        raise ValueError("No data at requested cutoff")
    cutoff = source.date.max()
    session_counts = source.groupby("date").symbol.nunique()
    sparse = session_counts.loc[session_counts < max(2, source.symbol.nunique() / 2)]
    # Preserve missing sessions on the benchmark calendar; no bridging returns over absent bars.
    calendar = pd.DatetimeIndex(sorted(source.date.unique()))
    pivot = source.pivot(index="date", columns="symbol", values="adj_close").reindex(calendar)
    returns = np.log(pivot).diff()
    benchmark = np.log(dataset.benchmark.set_index("date").close.reindex(calendar)).diff()
    classifications = sectors or source.groupby("symbol").sector.last().to_dict()
    symbols = sorted(s for s in pivot if s in dataset.members(cutoff))
    pair_list = [(a,b) for a,b in combinations(symbols, 2)
                 if not same_sector or (classifications.get(a, "UNKNOWN") != "UNKNOWN"
                                        and classifications.get(a) == classifications.get(b))]
    windows, rolling_tests, summaries, rolling_corr_rows = [], [], [], []
    for a, b in pair_list:
        levels = pivot[[a,b]]
        pair_returns = returns[[a,b]]
        common = levels.dropna()
        pair_id = f"{a}|{b}"
        for horizon in c.horizons:
            part = levels.iloc[-horizon:]
            observations = part.dropna()
            r = pair_returns.reindex(part.index).dropna()
            seed = c.seed + int(hashlib.sha256(f"{pair_id}:{horizon}".encode()).hexdigest()[:8], 16)
            complete = len(part) == horizon and len(observations) / horizon >= c.minimum_coverage
            row = {"pair_id": pair_id, "sessions_requested": horizon, "available_calendar_sessions": len(part),
                   "level_observations": len(observations), "return_observations": len(r),
                   "window_complete": complete, "pvalue": 1., "test_status": "INSUFFICIENT_HISTORY",
                   "contiguous_observations": len(observations) == len(part),
                   "price_level_correlation_descriptive_only": corr(observations[a], observations[b]),
                   "return_pearson": corr(r[a], r[b]),
                   "return_spearman": corr(r[a].rank(), r[b].rank()),
                   "return_correlation_95_block_interval": correlation_interval(r[a].to_numpy(), r[b].to_numpy(), c, seed),
                   "start": str(part.index.min().date()), "end": str(part.index.max().date())}
            # Show partial correlations but never label them as a completed requested horizon.
            if complete and len(observations) == len(part):
                row.update(relationship_test(observations))
            elif complete:
                row["test_status"] = "GAPS_IN_COINTEGRATION_WINDOW"
            weekly = part.dropna().resample("W-FRI").last()
            enough = part.dropna().resample("W-FRI").size() >= 3
            weekly.loc[~enough, :] = np.nan
            weekly_returns = np.log(weekly).diff().dropna()
            row["weekly_return_correlation"] = corr(weekly_returns[a], weekly_returns[b])
            aligned = pd.concat([r, benchmark.rename("market")], axis=1).dropna()
            if len(aligned) >= 40 and np.std(aligned.market) > 1e-10:
                residuals = []
                for symbol in (a,b):
                    beta, alpha = np.polyfit(aligned.market, aligned[symbol], 1)
                    residuals.append(aligned[symbol] - alpha - beta * aligned.market)
                row["market_residual_return_correlation"] = corr(*residuals)
            else:
                row["market_residual_return_correlation"] = None
            windows.append(row)
        rolling_corr = pair_returns[a].rolling(c.rolling_correlation_sessions,
                                              min_periods=c.rolling_correlation_sessions).corr(pair_returns[b])
        sampled_corr = rolling_corr.iloc[c.rolling_correlation_sessions-1::21].dropna()
        if len(rolling_corr) and pd.notna(rolling_corr.iloc[-1]) and rolling_corr.index[-1] not in sampled_corr.index:
            sampled_corr = pd.concat([sampled_corr, rolling_corr.iloc[[-1]]])
        for day, value in sampled_corr.items():
            rolling_corr_rows.append({"pair_id": pair_id, "date": str(day.date()),
                                      "return_correlation": float(value)})
        endpoints = list(range(c.rolling_coint_sessions, len(levels) + 1, c.rolling_step))
        if len(levels) >= c.rolling_coint_sessions and len(levels) not in endpoints:
            endpoints.append(len(levels))
        for end in endpoints:
            part = levels.iloc[end-c.rolling_coint_sessions:end]
            valid = part.dropna()
            row = {"pair_id": pair_id, "start": str(part.index[0].date()), "end": str(part.index[-1].date()),
                   "pvalue": 1., "test_status": "MISSING_OBSERVATIONS"}
            if len(valid) == c.rolling_coint_sessions:
                row.update(relationship_test(valid))
            rolling_tests.append(row)
        summaries.append({"pair_id": pair_id, "sector": classifications.get(a, "UNKNOWN"),
                          "common_start": str(common.index.min().date()) if len(common) else None,
                          "common_end": str(common.index.max().date()) if len(common) else None,
                          "common_observations": len(common),
                          "rolling_correlation_windows": len(sampled_corr),
                          "rolling_correlation_median": finite(sampled_corr.median()),
                          "rolling_correlation_p10": finite(sampled_corr.quantile(.1)),
                          "rolling_correlation_latest": finite(sampled_corr.iloc[-1]) if len(sampled_corr) else None,
                          "rolling_share_corr_at_least_0_6": float((sampled_corr >= .6).mean()) if len(sampled_corr) else None})
    # Conservative joint family: all pair/horizon and all rolling cointegration attempts.
    correct_family(windows + rolling_tests, c.alpha)
    for row in summaries:
        own = [w for w in windows if w["pair_id"] == row["pair_id"]]
        rolling = [w for w in rolling_tests if w["pair_id"] == row["pair_id"]]
        row["complete_horizons"] = [w["sessions_requested"] for w in own if w["window_complete"]]
        row["supported_horizons"] = [w["sessions_requested"] for w in own if w["cointegration_evidence"]]
        row["rolling_coint_attempts"] = len(rolling)
        row["rolling_coint_supported"] = sum(w["cointegration_evidence"] for w in rolling)
        row["classification"] = ("INSUFFICIENT_FIVE_YEAR_HISTORY" if 1260 not in row["complete_horizons"] else
                                 "STATISTICAL_REVIEW_ONLY" if {252,756} <= set(row["supported_horizons"]) else
                                 "CORRELATED_WITHOUT_RECENT_STABLE_SPREAD" if (row["rolling_correlation_latest"] or 0) >= .6 else
                                 "WEAK_OR_UNSTABLE_RELATIONSHIP")
        row["execution_ready"] = False
    summaries.sort(key=lambda r: (-(r["rolling_correlation_median"] or -1), r["pair_id"]))
    return {"as_of": str(cutoff.date()), "snapshot": dataset.digest, "config": asdict(c),
            "source": dataset.manifest["source"], "synthetic": dataset.manifest.get("synthetic", False),
            "membership_audited": dataset.manifest.get("membership_audited", False),
            "calendar_basis": "union_of_observed_stock_sessions_not_an_audited_exchange_calendar",
            "benchmark_missing_sessions": [d for d in dataset.manifest.get("benchmark_missing_sessions", [])
                                            if pd.Timestamp(d) <= cutoff],
            "sparse_observed_sessions_requiring_calendar_review": {str(d.date()): int(n) for d,n in sparse.items()},
            "hypotheses_in_joint_holm_family": len(windows) + len(rolling_tests),
            "pair_count": len(summaries), "pairs": summaries, "windows": windows,
            "rolling_cointegration": rolling_tests, "rolling_correlation": rolling_corr_rows,
            "limitations": ["Descriptive as-of diagnostics, not a forward-selected trading backtest",
                            "Historical correlation cannot prove future convergence",
                            "Partial horizons and missing observations remain explicitly labeled",
                            "Rolling windows overlap and are not independent success trials",
                            "Holm family includes all reported horizons and rolling cointegration attempts",
                            "Library actions, issuer breaks, membership and sector history require official audit",
                            "No statistical category constitutes an executable trade"]}


def save_diagnostics(result, folder):
    import html
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "diagnostics.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    for key in ("pairs", "windows", "rolling_cointegration", "rolling_correlation"):
        pd.DataFrame(result[key]).to_csv(folder / f"{key}.csv", index=False)
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(k)))}</td>" for k in
                   ("pair_id","common_start","common_end","rolling_correlation_median",
                    "rolling_correlation_latest","supported_horizons","classification")) + "</tr>"
                   for row in result["pairs"])
    headers = "".join(f"<th>{h}</th>" for h in ["Pair","Common start","Common end","Rolling median r","Latest rolling r","Supported horizons","Research category"])
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Long-history pair evidence</title>
<style>body{{font:15px system-ui;margin:32px;color:#18304b}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:12px;border-bottom:1px solid #ddd}}.notice{{background:#fff1c5;padding:20px}}pre{{white-space:pre-wrap}}</style>
<h1>Long-history pair evidence</h1><p>As of {result['as_of']} · {result['pair_count']} candidate pairs · source {html.escape(result['source'])}</p>
<p class="notice">RESEARCH DIAGNOSTICS. Correlation is not proof of a stable spread or a trade recommendation. Membership audited: {result['membership_audited']}. Synthetic: {result['synthetic']}.</p>
<table><tr>{headers}</tr>{rows}</table><h2>Method and limitations</h2><pre>{html.escape(json.dumps(result['limitations'], indent=2))}</pre>
<p>Correlation values are decimal coefficients between −1 and +1. Supported horizons are session counts, not years. Empty support is a valid negative finding.</p>
<p><a href="pairs.csv">Pair evidence</a> · <a href="windows.csv">All horizons</a> · <a href="rolling_correlation.csv">Rolling correlations</a> · <a href="rolling_cointegration.csv">Rolling spread tests</a> · <a href="diagnostics.json">Full JSON</a></p></html>"""
    (folder / "report.html").write_text(page)
