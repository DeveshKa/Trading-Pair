"""Correlation-free exact SSD discovery on complete formation paths."""
from dataclasses import asdict, dataclass
import hashlib
import heapq
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .data import Dataset


@dataclass(frozen=True)
class DistanceConfig:
    formation_sessions: int = 252
    trading_sessions: int = 126
    top_pairs: int = 20
    block_size: int = 128
    min_median_turnover_inr: float = 1_000_000

    def __post_init__(self):
        for name in ("formation_sessions", "trading_sessions", "top_pairs", "block_size"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.formation_sessions < 40 or not np.isfinite(self.min_median_turnover_inr) or self.min_median_turnover_inr < 0:
            raise ValueError("Invalid formation window or turnover threshold")


def exact_neighbours(paths, symbols, k, block_size=128):
    """Exact all-pairs SSD with O(block_size * N) temporary memory, deterministic ties.

    Input rows are complete normalized paths for distinct economic securities.
    Returned distances are mean SSD; equal-length paths have identical sum-SSD rankings.
    """
    x = np.asarray(paths, dtype=float)
    if x.ndim != 2 or x.shape[0] != len(symbols) or x.shape[1] < 2 or not np.isfinite(x).all():
        raise ValueError("Finite two-dimensional complete paths required")
    if k < 1 or block_size < 1 or len(set(symbols)) != len(symbols):
        raise ValueError("Invalid neighbour search parameters")
    # Center on one, not per-series mean: preserve the economic SSD metric while
    # reducing cancellation error from common unit-valued starting points.
    y = x - 1.
    norms = np.einsum("ij,ij->i", y, y)
    n = len(symbols)
    best = []
    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        d = np.maximum(norms[start:end, None] + norms[None, :] - 2 * (y[start:end] @ y.T), 0) / x.shape[1]
        for local, i in enumerate(range(start, end)):
            # Keep top k from each row; no globally top-k pair can be beyond k in its row.
            count = min(k, n-i-1)
            if not count:
                continue
            indices = np.arange(i+1, n)
            order = np.lexsort((np.array(symbols, dtype=str)[indices], d[local, indices]))[:count]
            for j in indices[order]:
                # Direct recomputation makes exported distances independent of BLAS roundoff.
                distance = float(np.mean((x[i] - x[j]) ** 2))
                best.append((distance, symbols[i], symbols[j]))
        best = heapq.nsmallest(k, best)
    return sorted(best)


def load_master(path):
    master = pd.read_csv(path, dtype=str).fillna("")
    required = {"symbol", "exchange", "isin", "security_type"}
    if not required <= set(master):
        raise ValueError(f"Security master needs {sorted(required)}")
    if master.symbol.duplicated().any() or (master.symbol == "").any():
        raise ValueError("Security-master symbols must be unique and nonempty")
    if not master.exchange.isin(["NSE", "BSE", "SYNTHETIC"]).all():
        raise ValueError("Unsupported exchange")
    return master.set_index("symbol", drop=False)


def discover(dataset: Dataset, master: pd.DataFrame, config=None, as_of=None):
    c = config or DistanceConfig()
    cutoff = pd.Timestamp(as_of) if as_of else dataset.bars.date.max()
    history = dataset.bars.loc[dataset.bars.date <= cutoff]
    if history.empty:
        raise ValueError("No data before cutoff")
    dates = sorted(history.date.unique())[-c.formation_sessions:]
    if len(dates) < c.formation_sessions:
        raise ValueError("Insufficient formation sessions")
    history = history.loc[history.date.isin(dates)]
    pivot = history.pivot(index="date", columns="symbol", values="adj_close")
    volume = history.pivot(index="date", columns="symbol", values="volume")
    turnover = history.assign(turnover=history.close * history.volume).groupby("symbol").turnover.median()
    eligible, audit = [], []
    # Only securities observed at formation can appear; no final-sample survivor filter.
    for symbol in sorted(pivot):
        reason = ""
        if symbol not in master.index:
            reason = "IDENTITY_UNRESOLVED"
        elif master.loc[symbol, "security_type"] != "EQUITY":
            reason = "NOT_ORDINARY_EQUITY"
        elif not master.loc[symbol, "isin"]:
            reason = "IDENTITY_UNRESOLVED"
        elif pivot[symbol].isna().any() or (volume[symbol] <= 0).any():
            reason = "INCOMPLETE_OR_UNTRADED_FORMATION"
        elif turnover[symbol] < c.min_median_turnover_inr:
            reason = "LOW_FORMATION_TURNOVER"
        if not reason:
            eligible.append(symbol)
        audit.append({"symbol": symbol, "reason": reason, "median_turnover_inr": float(turnover[symbol])})
    # Select the highest-turnover venue *during formation*, not the venue that later performed best.
    venue_groups = {}
    for symbol in eligible:
        venue_groups.setdefault(master.loc[symbol, "isin"], []).append(symbol)
    chosen = []
    for candidates in venue_groups.values():
        winner = sorted(candidates, key=lambda s: (-turnover[s], s))[0]
        chosen.append(winner)
        for row in audit:
            if row["symbol"] in candidates and row["symbol"] != winner:
                row["reason"] = "DUPLICATE_SECURITY_OTHER_VENUE"
    chosen.sort()
    values = pivot[chosen].to_numpy().T
    normalized = values / values[:, [0]] if len(chosen) else np.empty((0,len(dates)))
    ranked = exact_neighbours(normalized, chosen, c.top_pairs, c.block_size)
    pairs = []
    for rank, (distance, a, b) in enumerate(ranked, 1):
        spread = pivot[a] / pivot[a].iloc[0] - pivot[b] / pivot[b].iloc[0]
        std = float(spread.std(ddof=1))
        pairs.append({"rank": rank, "a": a, "b": b, "isin_a": master.loc[a,"isin"],
                      "isin_b": master.loc[b,"isin"], "distance_mean_ssd": distance,
                      "distance_sum_ssd": distance * len(dates), "formation_spread_std": std,
                      "formation_start": str(pd.Timestamp(dates[0]).date()),
                      "formed_at": str(pd.Timestamp(dates[-1]).date()),
                      "tradeable_signal_basis": std > 1e-10, "execution_ready": False})
    return {"method": "GGR_STYLE_MINIMUM_DISTANCE_NO_CORRELATION_GATE",
            "as_of": str(pd.Timestamp(dates[-1]).date()), "config": asdict(c),
            "snapshot": dataset.digest, "master_sha256": hashlib.sha256(master.to_csv(index=False).encode()).hexdigest(),
            "source": dataset.manifest["source"], "synthetic": dataset.manifest.get("synthetic",False),
            "observed_listings": len(pivot.columns), "eligible_distinct_securities": len(chosen),
            "candidate_pair_count": len(chosen)*(len(chosen)-1)//2, "pairs": pairs,
            "security_audit": audit,
            "limitations": ["Current-master library samples are exploratory and survivorship biased",
                            "Corporate-action-adjusted paths need source audit",
                            "Pair ranking is not proof of convergence or short availability",
                            "Same-ISIN listings are one security, not a candidate pair"]}


def forward_convergence(dataset, discovery):
    """Observe subsequent crossings without feeding outcomes back into formation ranking.

    Normalized total-return units give an economic spread payoff, not actual fills.
    This is deliberately separate from the capital-accounting backtester.
    """
    cutoff = pd.Timestamp(discovery["as_of"])
    c = discovery["config"]
    days = sorted(dataset.bars.date.unique())
    forward_dates = [d for d in days if d > cutoff][:c["trading_sessions"]]
    # Filter/pivot the forward block once per cohort, not the entire market per pair.
    forward = dataset.bars.loc[dataset.bars.date.isin(forward_dates)]
    all_prices = forward.pivot(index="date",columns="symbol",values="adj_close").reindex(forward_dates)
    all_volumes = forward.pivot(index="date",columns="symbol",values="volume").reindex(forward_dates)
    output = []
    for pair in discovery["pairs"]:
        a,b = pair["a"],pair["b"]
        present = [s for s in (a,b) if s in all_prices]
        p = all_prices[present]
        v = all_volumes[present]
        complete = len(forward_dates) == c["trading_sessions"] and {a,b} <= set(p.columns) and p[[a,b]].notna().all().all()
        traded = complete and (v[[a,b]] > 0).all().all()
        status = "INCOMPLETE_FORWARD_WINDOW" if not complete else "INVALID_FORWARD_OBSERVATIONS" if not traded else "OK"
        complete = bool(complete and traded)
        result = {"a":a,"b":b,"formed_at":discovery["as_of"],"forward_sessions":len(forward_dates),
                  "window_complete": bool(complete),"opened":0,"converged":0,"unresolved":0,
                  "status":status}
        if not complete or not pair["tradeable_signal_basis"]:
            output.append(result);continue
        # Renormalize once at trading start, then use the formation standard deviation.
        normalized = p[[a,b]] / p[[a,b]].iloc[0]
        spread = (normalized[a]-normalized[b]).to_numpy()
        threshold = 2 * pair["formation_spread_std"]
        opened_at = None
        sign = 0
        durations = []
        for i,value in enumerate(spread):
            if opened_at is None:
                if abs(value) > threshold:
                    result["opened"] += 1;opened_at=i;sign=np.sign(value)
            elif value*sign <= 0:
                result["converged"] += 1;durations.append(i-opened_at);opened_at=None
        result["unresolved"] = int(opened_at is not None)
        result["median_convergence_sessions"] = float(np.median(durations)) if durations else None
        output.append(result)
    return output


def distance_study(dataset, master, config=None):
    c = config or DistanceConfig()
    dates = sorted(dataset.bars.date.unique())
    formations, outcomes = [], []
    last_month = None
    for index in range(c.formation_sessions-1, len(dates)-c.trading_sessions):
        day = pd.Timestamp(dates[index])
        month = day.strftime("%Y-%m")
        if month == last_month:
            continue
        result = discover(dataset,master,c,day)
        formations.append({k:v for k,v in result.items() if k != "security_audit"})
        outcomes.extend(forward_convergence(dataset,result))
        last_month = month
    return {"method":"ROLLING_FORMATION_THEN_SEPARATE_CONVERGENCE_OBSERVATION",
            "config":asdict(c),"snapshot":dataset.digest,"cohorts":len(formations),
            "formations":formations,"outcomes":outcomes,
            "note":"Overlapping cohorts are not independent; convergence counts are not net trading returns"}


def save_marketwide(result, folder):
    import html
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    (folder/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    for key in ("pairs","security_audit","outcomes"):
        if key in result:pd.DataFrame(result[key]).to_csv(folder/f"{key}.csv",index=False)
    body=html.escape(json.dumps({k:v for k,v in result.items() if k not in ("security_audit","formations","outcomes")},indent=2))
    (folder/"report.html").write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Distance pairs research</title><style>body{{font:16px system-ui;max-width:1000px;margin:30px auto}}pre{{white-space:pre-wrap}}</style><h1>Distance-based pairs research</h1><p>Research only. No correlation selection; no executable return claim.</p><pre>{body}</pre><p><a href="results.json">Complete research evidence</a></p></html>')
