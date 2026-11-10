from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
import json
import warnings
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller, coint
from .config import Config
from .data import Dataset


@dataclass(frozen=True)
class PairModel:
    a: str
    b: str
    sector: str
    strategy: str
    alpha: float
    beta: float
    mean: float
    std: float
    base_a: float
    base_b: float
    half_life: float
    pvalue: float
    adjusted_pvalue: float
    distance: float
    formed_at: str
    model_id: str

    @property
    def pair_id(self):
        return f"{self.a}|{self.b}"

    def zscore(self, price_a, price_b):
        if self.strategy == "distance":
            spread = price_a / self.base_a - price_b / self.base_b
        else:
            spread = np.log(price_a) - self.alpha - self.beta * np.log(price_b)
        return float((spread - self.mean) / self.std)

    def to_dict(self):
        return asdict(self)


def select_pairs(dataset: Dataset, date, config: Config):
    """Only data available at this daily close enter selection. Audit every tested pair."""
    history = dataset.bars.loc[dataset.bars.date <= date]
    dates = sorted(history.date.unique())[-config.formation_sessions:]
    if len(dates) < config.formation_sessions:
        return [], []
    history = history.loc[history.date.isin(dates)]
    pivot = history.pivot(index="date", columns="symbol", values="adj_close")
    volumes = history.pivot(index="date", columns="symbol", values="volume")
    members = dataset.members(date)
    symbols = sorted(s for s in pivot if s in members and pivot[s].notna().all()
                     and (volumes[s] > 0).all())
    sectors = history.sort_values("date").groupby("symbol").sector.last().to_dict()
    audit = []
    candidates = []
    for a, b in combinations(symbols, 2):
        if config.same_sector and (sectors[a] != sectors[b] or sectors[a] == "UNKNOWN"):
            continue
        pa, pb = pivot[a].to_numpy(), pivot[b].to_numpy()
        distance = float(np.mean((pa / pa[0] - pb / pb[0]) ** 2))
        alpha, beta, pvalue = 0., 1., 1.
        reason = ""
        if config.strategy == "cointegration":
            x, y = np.log(pb), np.log(pa)
            beta, alpha = np.polyfit(x, y, 1)
            spread = y - alpha - beta * x
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    pvalue = float(coint(y, x, trend="c", maxlag=1, autolag=None)[1])
                    if min(adfuller(x, maxlag=1, autolag=None)[1],
                           adfuller(y, maxlag=1, autolag=None)[1]) <= .05:
                        reason = "LEVEL_INTEGRATION_ASSUMPTION"
                except (ValueError, np.linalg.LinAlgError):
                    reason = "TEST_FAILED"
            if beta <= 0 or not np.isfinite(beta):
                reason = "NONPOSITIVE_HEDGE"
        else:
            spread = pa / pa[0] - pb / pb[0]
        std = float(np.std(spread, ddof=1))
        phi = float(np.polyfit(spread[:-1], spread[1:], 1)[0]) if std > 1e-10 else 1.
        half = float(-np.log(2) / np.log(phi)) if 0 < phi < 1 else 0.
        if std <= 1e-10:
            reason = "DEGENERATE_SPREAD"
        if config.strategy == "cointegration" and not config.min_half_life <= half <= config.max_half_life:
            reason = "HALF_LIFE_OUTSIDE_BAND"
        if not np.isfinite(pvalue):
            pvalue, reason = 1., "INVALID_TEST"
        entry = {"a": a, "b": b, "formed_at": str(pd.Timestamp(date).date()),
                 "pvalue": pvalue, "half_life": half, "distance": distance, "reason": reason}
        audit.append(entry)
        candidates.append((entry, alpha, beta, float(np.mean(spread)), std, pa[0], pb[0]))
    corrected = (multipletests([r["pvalue"] for r in audit], alpha=config.family_alpha, method="holm")[1]
                 if audit else [])
    models = []
    for args, adjusted in zip(candidates, corrected):
        entry, alpha, beta, mean, std, base_a, base_b = args
        entry["adjusted_pvalue"] = float(adjusted)
        if config.strategy == "cointegration" and adjusted > config.family_alpha and not entry["reason"]:
            entry["reason"] = "MULTIPLE_TEST_CORRECTION"
        if entry["reason"]:
            continue
        payload = {**entry, "alpha": float(alpha), "beta": float(beta), "mean": mean, "std": std,
                   "base_a": float(base_a), "base_b": float(base_b), "strategy": config.strategy,
                   "sector": sectors[entry["a"]]}
        mid = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
        models.append(PairModel(**{k: payload[k] for k in PairModel.__dataclass_fields__ if k != "model_id"}, model_id=mid))
    models.sort(key=lambda m: (m.distance, m.pair_id) if config.strategy == "distance"
                else (m.half_life, m.distance, m.pair_id))
    selected = {m.pair_id for m in models[:config.top_pairs]}
    for row in audit:
        row["selected"] = f"{row['a']}|{row['b']}" in selected
        if not row["reason"] and not row["selected"]:
            row["reason"] = "RANK_LIMIT"
    return models[:config.top_pairs], audit
