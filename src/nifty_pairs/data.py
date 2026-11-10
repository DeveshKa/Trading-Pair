"""Validated CSV data contract and interchangeable historical-data adapters."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Protocol
import numpy as np
import pandas as pd

BAR_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "adj_close",
               "volume", "dividend", "split", "sector"]


class HistoricalProvider(Protocol):
    def download(self, symbols: list[str], start: str, end: str, destination: Path,
                 benchmark: str) -> None: ...


@dataclass
class Dataset:
    bars: pd.DataFrame
    benchmark: pd.DataFrame
    membership: pd.DataFrame | None
    manifest: dict
    digest: str

    @classmethod
    def load(cls, folder):
        folder = Path(folder)
        manifest = json.loads((folder / "manifest.json").read_text())
        if manifest.get("price_basis") != "raw_execution":
            raise ValueError("Price basis must be raw_execution; do not feed adjusted prices to the ledger")
        if not manifest.get("source") or not manifest.get("benchmark_kind"):
            raise ValueError("Manifest must declare source and benchmark_kind")
        bars = pd.read_csv(folder / "bars.csv")
        missing = set(BAR_COLUMNS) - set(bars)
        if missing:
            raise ValueError(f"Missing bar columns: {sorted(missing)}")
        bars["date"] = pd.to_datetime(bars.date, errors="raise").dt.normalize()
        if bars.date.isna().any() or bars.duplicated(["date", "symbol"]).any():
            raise ValueError("Invalid dates or duplicate bars")
        if bars[["symbol", "sector"]].isna().any().any():
            raise ValueError("Missing symbol or sector")
        numeric = ["open", "high", "low", "close", "adj_close", "volume", "dividend", "split"]
        values = bars[numeric].apply(pd.to_numeric, errors="raise")
        if not np.isfinite(values.to_numpy()).all():
            raise ValueError("Nonfinite bars")
        bars[numeric] = values
        if (bars[["open", "high", "low", "close", "adj_close", "split"]] <= 0).any().any():
            raise ValueError("Nonpositive price or split ratio")
        if (bars[["volume", "dividend"]] < 0).any().any():
            raise ValueError("Negative volume or dividend")
        if ((bars.high < bars[["open", "close", "low"]].max(axis=1)) |
            (bars.low > bars[["open", "close", "high"]].min(axis=1))).any():
            raise ValueError("Invalid OHLC relationships")
        bench = pd.read_csv(folder / "benchmark.csv")
        if not {"date", "close"} <= set(bench):
            raise ValueError("Benchmark needs date,close")
        bench["date"] = pd.to_datetime(bench.date, errors="raise").dt.normalize()
        if bench.date.isna().any() or bench.date.duplicated().any():
            raise ValueError("Duplicate or invalid benchmark dates")
        bench["close"] = pd.to_numeric(bench.close, errors="raise")
        if not np.isfinite(bench.close).all() or (bench.close <= 0).any():
            raise ValueError("Invalid benchmark levels")
        if not set(bars.date) <= set(bench.date):
            raise ValueError("Benchmark missing equity sessions; no silent forward fill")
        member_path = folder / "membership.csv"
        membership = pd.read_csv(member_path) if member_path.exists() else None
        if membership is not None:
            if not {"symbol", "effective_from", "effective_to"} <= set(membership):
                raise ValueError("Membership needs symbol,effective_from,effective_to (exclusive)")
            if membership.symbol.isna().any():
                raise ValueError("Missing membership symbol")
            membership["effective_from"] = pd.to_datetime(membership.effective_from, errors="raise")
            membership["effective_to"] = pd.to_datetime(membership.effective_to, errors="raise")
            if membership.effective_from.isna().any():
                raise ValueError("Membership needs effective_from")
            for _, group in membership.groupby("symbol"):
                ordered = group.sort_values("effective_from")
                end = None
                for row in ordered.itertuples():
                    if pd.notna(row.effective_to) and row.effective_to <= row.effective_from:
                        raise ValueError("Membership end must follow start")
                    if end is not None and (pd.isna(end) or row.effective_from < end):
                        raise ValueError("Overlapping membership intervals")
                    end = row.effective_to
        hashes = {}
        for name in ("bars.csv", "benchmark.csv", "membership.csv", "manifest.json"):
            path = folder / name
            if path.exists():
                hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        manifest = {**manifest, "file_hashes": hashes}
        return cls(bars.sort_values(["date", "symbol"]), bench.sort_values("date"),
                   membership, manifest, digest)

    def members(self, date):
        if self.membership is None:
            return set(self.bars.symbol.unique())
        m = self.membership
        return set(m.loc[(m.effective_from <= date) &
                        (m.effective_to.isna() | (date < m.effective_to)), "symbol"])


def write_dataset(folder, bars, benchmark, manifest, membership=None):
    import tempfile
    folder = Path(folder)
    if folder.exists():
        raise ValueError("Destination exists; use a new snapshot directory")
    folder.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder.parent) as temp:
        stage = Path(temp) / "snapshot"
        stage.mkdir()
        bars[BAR_COLUMNS].to_csv(stage / "bars.csv", index=False)
        benchmark[["date", "close"]].to_csv(stage / "benchmark.csv", index=False)
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2))
        if membership is not None:
            membership.to_csv(stage / "membership.csv", index=False)
        Dataset.load(stage)
        stage.rename(folder)


def make_demo(folder, sessions=1100, seed=42):
    """Invented cointegrated assets. Not NSE observations or a market calendar."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2018-01-01", periods=sessions)
    rows = []
    market = np.cumsum(rng.normal(.0002, .009, sessions))
    for group, sector in enumerate(["BANK", "IT", "PHARMA"]):
        trend = 5 + market + np.cumsum(rng.normal(0, .004, sessions))
        for leg in range(2):
            residual = np.zeros(sessions)
            for i in range(1, sessions):
                residual[i] = .94 * residual[i-1] + rng.normal(0, .007)
            close = np.exp(trend + residual + .2 * leg)
            opens = np.r_[close[0], close[:-1]] * np.exp(rng.normal(0, .002, sessions))
            for i, date in enumerate(dates):
                rows.append([date, f"DEMO{group}{leg}", opens[i],
                             max(opens[i], close[i]) * 1.005,
                             min(opens[i], close[i]) * .995, close[i], close[i],
                             1_000_000, 0.0, 1.0, sector])
    bars = pd.DataFrame(rows, columns=BAR_COLUMNS)
    benchmark = pd.DataFrame({"date": dates, "close": 10000 * np.exp(market)})
    membership = pd.DataFrame({"symbol": bars.symbol.unique(),
                               "effective_from": dates[0], "effective_to": ""})
    write_dataset(folder, bars, benchmark,
                  {"source": "synthetic_demo", "synthetic": True, "seed": seed,
                   "price_basis": "raw_execution", "actions_complete": True,
                   "benchmark_kind": "SYNTHETIC_PRICE", "membership_audited": False}, membership)


class YFinanceProvider:
    """Exploratory adapter. No point-in-time universe or exchange-data certification."""

    def download(self, symbols, start, end, destination, benchmark="^NSEI", allow_calendar_intersection=False):
        import yfinance as yf
        from datetime import datetime, timezone
        frames = []
        for symbol in symbols:
            # Fetch through today so subsequent splits can be undone in Yahoo's split-adjusted OHLC.
            history = yf.Ticker(symbol).history(start=start, auto_adjust=False, actions=True,
                                                raise_errors=True)
            if history.empty:
                raise ValueError(f"Library returned no observations for {symbol}")
            history.index = pd.to_datetime(history.index).tz_localize(None).normalize()
            splits = history.get("Stock Splits", pd.Series(0., index=history.index)).replace(0, 1)
            future_factor = splits.iloc[::-1].cumprod().iloc[::-1] / splits
            h = history.loc[history.index < pd.Timestamp(end)]
            if h.empty or "Adj Close" not in h:
                raise ValueError(f"No usable adjusted-close data for {symbol}")
            # Fixed share units are restored for the ledger; total-return Adj Close stays research-only.
            frame = pd.DataFrame({"date": h.index, "symbol": symbol,
                                  "adj_close": h["Adj Close"].to_numpy(),
                                  "dividend": (h.get("Dividends", 0) * future_factor.loc[h.index]).to_numpy(),
                                  "split": splits.loc[h.index].to_numpy(), "sector": "UNKNOWN"})
            for field in ("open", "high", "low", "close"):
                frame[field] = (h[field.title()] * future_factor.loc[h.index]).to_numpy()
            frame["volume"] = (h.Volume / future_factor.loc[h.index]).to_numpy()
            frames.append(frame)
        b = yf.Ticker(benchmark).history(start=start, end=end, auto_adjust=False, raise_errors=True)
        if b.empty:
            raise ValueError("No benchmark history")
        dates = pd.to_datetime(b.index).tz_localize(None).normalize()
        bench = pd.DataFrame({"date": dates, "close": b.Close.to_numpy()})
        combined = pd.concat(frames)
        missing = sorted(set(combined.date) - set(bench.date))
        if missing and not allow_calendar_intersection:
            raise ValueError(f"Benchmark missing {len(missing)} sessions: {[str(d.date()) for d in missing]}. "
                             "Repair benchmark or explicitly use --allow-calendar-intersection for a smoke test.")
        if missing:
            removed = combined.loc[combined.date.isin(missing)]
            if (removed.dividend != 0).any() or (removed.split != 1).any():
                raise ValueError("Cannot drop benchmark-missing sessions containing corporate actions")
            combined = combined.loc[~combined.date.isin(missing)]
        write_dataset(destination, combined, bench,
                      {"source": "yfinance", "provider_version": yf.__version__,
                       "downloaded_at": datetime.now(timezone.utc).isoformat(),
                       "symbols": symbols, "start": start, "end_exclusive": end,
                       "price_basis": "raw_execution", "actions_complete": False,
                       "split_reconstruction": "Yahoo OHLC times subsequent reported split ratios",
                       "membership_audited": False, "benchmark_symbol": benchmark,
                       "calendar_policy": "explicit_intersection" if allow_calendar_intersection else "strict",
                       "excluded_equity_sessions": [str(d.date()) for d in missing],
                       "benchmark_kind": "PRICE_INDEX" if benchmark == "^NSEI" else "USER_LIBRARY_SERIES",
                       "warning": "Exploratory fixed-symbol sample; actions and reconstructions need NSE audit"})
