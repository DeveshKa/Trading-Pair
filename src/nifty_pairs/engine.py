from dataclasses import dataclass
import hashlib
import json
import math
import numpy as np
import pandas as pd
from .config import Config
from .data import Dataset
from .selection import PairModel, select_pairs


@dataclass
class Position:
    model: PairModel
    qa: float
    qb: float
    entry_a: float
    entry_b: float
    opened: str
    open_index: int
    cost: float
    income: float = 0.

    def pnl(self, pa, pb):
        return self.qa * (pa - self.entry_a) + self.qb * (pb - self.entry_b) + self.income - self.cost


def metrics(nav, benchmark, risk_free=0.):
    nav, benchmark = np.asarray(nav, float), np.asarray(benchmark, float)
    r, b = nav[1:] / nav[:-1] - 1, benchmark[1:] / benchmark[:-1] - 1
    years = len(r) / 252
    def stats(x, returns):
        vol = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.
        return {"total_return": float(x[-1] / x[0] - 1),
                "cagr": float((x[-1] / x[0]) ** (1 / years) - 1) if years and (x > 0).all() else None,
                "annual_volatility": vol * math.sqrt(252),
                "sharpe": float((np.mean(returns) - risk_free / 252) / vol * math.sqrt(252)) if vol else None,
                "max_drawdown": float(np.min(x / np.maximum.accumulate(x) - 1))}
    return {"strategy": stats(nav, r), "benchmark": stats(benchmark, b),
            "return_correlation": float(np.corrcoef(r, b)[0, 1]) if np.std(r) and np.std(b) else None}


def backtest(dataset: Dataset, config: Config):
    if config.require_membership and dataset.membership is None:
        raise ValueError("Point-in-time membership required. Exploratory fixed-symbol runs must explicitly disable it.")
    c = config
    dates = sorted(dataset.bars.date.unique())
    if len(dates) <= c.formation_sessions + 1:
        raise ValueError("Not enough data after formation")
    grouped = {d: g.set_index("symbol") for d, g in dataset.bars.groupby("date")}
    benchmark = dataset.benchmark.set_index("date").close
    positions, marks, models, previous_z = {}, {}, [], {}
    pending, rows, trades, fills, events, audit, model_history = [], [], [], [], [], [], []
    cash = c.initial_capital
    peak = c.initial_capital
    paused = False
    formation_month = None
    total_fees = total_borrow = 0.
    last_date = dates[-1]

    def event(day, kind, pair_id, reason, **extra):
        events.append({"date": str(pd.Timestamp(day).date()), "kind": kind,
                       "pair_id": pair_id, "reason": reason, **extra})

    def nav():
        return cash + sum(p.qa * marks[p.model.a] + p.qb * marks[p.model.b] for p in positions.values())

    def transact(day, symbol, quantity, reference, pair_id, action):
        nonlocal cash, total_fees
        price = reference * (1 + math.copysign(c.slippage_bps / 10000, quantity))
        fee = abs(quantity * price) * c.fee_bps / 10000
        cash -= quantity * price + fee
        total_fees += fee
        fills.append({"date": str(pd.Timestamp(day).date()), "pair_id": pair_id, "symbol": symbol,
                      "quantity": quantity, "reference_price": reference, "fill_price": price,
                      "fee": fee, "action": action})
        return price, fee

    def close(day, pair_id, prices, reason):
        p = positions.pop(pair_id)
        fa, ca = transact(day, p.model.a, -p.qa, prices[p.model.a], pair_id, "CLOSE")
        fb, cb = transact(day, p.model.b, -p.qb, prices[p.model.b], pair_id, "CLOSE")
        pnl = p.pnl(fa, fb) - ca - cb
        trades.append({"pair_id": pair_id, "model_id": p.model.model_id, "opened": p.opened,
                       "closed": str(pd.Timestamp(day).date()), "qa": p.qa, "qb": p.qb,
                       "pnl": pnl, "fees": p.cost + ca + cb, "income_less_borrow": p.income,
                       "reason": reason})
        event(day, "CLOSED", pair_id, reason, pnl=pnl)

    for index, date in enumerate(dates):
        bars = grouped[date]
        prices = bars.close.to_dict()
        opens = bars.open.to_dict()
        # Corporate actions apply to holdings carried from the previous session.
        for p in positions.values():
            for leg in ("a", "b"):
                symbol = getattr(p.model, leg)
                if symbol in bars.index:
                    ratio = float(bars.loc[symbol, "split"])
                    qty = getattr(p, "q" + leg) * ratio
                    setattr(p, "q" + leg, qty)
                    setattr(p, "entry_" + leg, getattr(p, "entry_" + leg) / ratio)
                    amount = qty * float(bars.loc[symbol, "dividend"])
                    p.income += amount
                    cash += amount
                    if ratio != 1 and symbol in marks:
                        marks[symbol] /= ratio
        # Accrue calendar-day borrow on positions carried across sessions, including exit days.
        elapsed_days = (pd.Timestamp(date) - pd.Timestamp(dates[index-1])).days if index else 0
        for p in positions.values():
            borrow = (max(-p.qa, 0) * marks[p.model.a] + max(-p.qb, 0) * marks[p.model.b]) * c.short_borrow_annual * elapsed_days / 365
            p.income -= borrow
            cash -= borrow
            total_borrow += borrow
        # Values at open are known before allocation; missing prices never become fills.
        marks.update(opens)
        deferred_exits = []
        for order in pending:
            m, kind = order["model"], order["kind"]
            pair_id = m.pair_id
            if m.a not in opens or m.b not in opens or bars.loc[[m.a, m.b], "volume"].min() <= 0:
                event(date, "BLOCKED", pair_id, "MISSING_OR_UNTRADED_OPEN")
                if kind == "EXIT" and pair_id in positions:
                    deferred_exits.append(order)
                continue
            if kind == "EXIT":
                if pair_id in positions:
                    close(date, pair_id, opens, order["reason"])
                continue
            if pair_id in positions or paused:
                event(date, "BLOCKED", pair_id, "POSITION_EXISTS_OR_PAUSED")
                continue
            if not {m.a, m.b} <= dataset.members(date):
                event(date, "BLOCKED", pair_id, "MEMBERSHIP_CHANGED")
                continue
            equity = nav()
            budget = equity * c.pair_gross_fraction
            qa = math.floor(budget / (1 + m.beta) / opens[m.a]) * order["side"]
            qb = -math.floor(budget * m.beta / (1 + m.beta) / opens[m.b]) * order["side"]
            if not qa or not qb or equity <= 0:
                event(date, "BLOCKED", pair_id, "CAPITAL_OR_INTEGER_SHARES")
                continue
            exposure = {}
            sector_exp = {}
            net = 0.
            for p in positions.values():
                for s, q in [(p.model.a, p.qa), (p.model.b, p.qb)]:
                    value = q * marks[s]
                    exposure[s] = exposure.get(s, 0.) + abs(value)
                    sector_exp[p.model.sector] = sector_exp.get(p.model.sector, 0.) + abs(value)
                    net += value
            for s, q in [(m.a, qa), (m.b, qb)]:
                value = q * opens[s]
                exposure[s] = exposure.get(s, 0.) + abs(value)
                sector_exp[m.sector] = sector_exp.get(m.sector, 0.) + abs(value)
                net += value
            if (sum(exposure.values()) > equity * c.max_gross_fraction or
                max(exposure.values()) > equity * c.max_underlying_fraction or
                max(sector_exp.values()) > equity * c.max_sector_fraction or
                abs(net) > equity * c.max_net_fraction):
                event(date, "BLOCKED", pair_id, "PORTFOLIO_EXPOSURE_LIMIT")
                continue
            fa, ca = transact(date, m.a, qa, opens[m.a], pair_id, "OPEN")
            fb, cb = transact(date, m.b, qb, opens[m.b], pair_id, "OPEN")
            positions[pair_id] = Position(m, qa, qb, fa, fb, str(pd.Timestamp(date).date()), index, ca + cb)
            event(date, "PAPER_OPEN", pair_id, "IDEALIZED_CASH_SHORT", model_id=m.model_id)
        pending = deferred_exits
        marks.update(prices)
        current_nav = nav()
        if current_nav <= 0:
            raise ValueError(f"Portfolio insolvent on {pd.Timestamp(date).date()}; halted without compounding invalid NAV")
        peak = max(peak, current_nav)
        if current_nav <= peak * (1 - c.portfolio_drawdown_pause) and not paused:
            paused = True
            event(date, "PAUSED", "PORTFOLIO", "DRAWDOWN_LIMIT")
        for pair_id, p in list(positions.items()):
            m = p.model
            if m.a not in prices or m.b not in prices:
                event(date, "DATA_INCIDENT", pair_id, "STALE_MARK_NO_FILL")
                continue
            z = m.zscore(bars.loc[m.a, "adj_close"], bars.loc[m.b, "adj_close"])
            reason = ("MEMBERSHIP_EXIT" if not {m.a, m.b} <= dataset.members(date) else
                      "PORTFOLIO_PAUSE" if paused else
                      "PAIR_LOSS_STOP" if p.pnl(prices[m.a], prices[m.b]) <= -c.initial_capital * c.pair_loss_fraction else
                      "SPREAD_STOP" if abs(z) >= c.stop_z else
                      "MAX_HOLDING" if index - p.open_index >= c.max_holding_sessions else
                      "CONVERGENCE" if abs(z) <= c.exit_z else None)
            if reason:
                if not any(o["kind"] == "EXIT" and o["model"].pair_id == pair_id for o in pending):
                    pending.append({"kind": "EXIT", "model": m, "reason": reason})
                event(date, "EXIT_DUE", pair_id, reason, z=z, model_id=m.model_id)
        if date == last_date:
            for pair_id, p in list(positions.items()):
                if (p.model.a in prices and p.model.b in prices and
                    bars.loc[[p.model.a, p.model.b], "volume"].min() > 0):
                    close(date, pair_id, prices, "PREDECLARED_SAMPLE_END")
            pending = []
        if index >= c.formation_sessions - 1 and date != last_date:
            month = pd.Timestamp(date).strftime("%Y-%m")
            if month != formation_month:
                models, tested = select_pairs(dataset, date, c)
                audit.extend(tested)
                model_history.extend(m.to_dict() for m in models)
                formation_month = month
                # Seed z with the preceding session; a new model does not imply a crossing.
                previous_z = {}
                if index:
                    prior = grouped[dates[index-1]]
                    for m in models:
                        if {m.a, m.b} <= set(prior.index):
                            previous_z[m.model_id] = m.zscore(prior.loc[m.a, "adj_close"], prior.loc[m.b, "adj_close"])
            for m in models:
                if m.a not in prices or m.b not in prices:
                    continue
                z = m.zscore(bars.loc[m.a, "adj_close"], bars.loc[m.b, "adj_close"])
                old = previous_z.get(m.model_id)
                previous_z[m.model_id] = z
                crossing = old is not None and ((old < c.entry_z <= z) or (old > -c.entry_z >= z))
                if crossing and m.pair_id not in positions and not paused:
                    if abs(z) >= c.stop_z:
                        event(date, "BLOCKED", m.pair_id, "CATASTROPHIC_GAP", z=z)
                    else:
                        event(date, "RESEARCH_SETUP", m.pair_id, "DAILY_CLOSE_CROSSING",
                              z=z, model_id=m.model_id, direction="SHORT_A_LONG_B" if z > 0 else "LONG_A_SHORT_B")
                        pending.append({"kind": "ENTRY", "model": m, "side": -1 if z > 0 else 1})
        if index >= c.formation_sessions - 1:
            rows.append({"date": str(pd.Timestamp(date).date()), "nav": nav(), "cash": cash,
                         "open_pairs": len(positions), "paused": paused,
                         "gross_exposure": sum(abs(p.qa * marks[p.model.a]) + abs(p.qb * marks[p.model.b]) for p in positions.values()),
                         "benchmark_level": float(benchmark.loc[date])})
    frame = pd.DataFrame(rows)
    frame["benchmark_nav"] = c.initial_capital * frame.benchmark_level / frame.benchmark_level.iloc[0]
    summary = metrics(frame.nav, frame.benchmark_nav, c.risk_free_annual)
    summary.update({"completed_trades": len(trades), "wins": sum(t["pnl"] > 0 for t in trades),
                    "fees": total_fees, "borrow_cost": total_borrow, "open_pairs_at_end": len(positions),
                    "net_profit": float(frame.nav.iloc[-1] - c.initial_capital),
                    "trade_pnl": sum(t["pnl"] for t in trades),
                    "benchmark_kind": dataset.manifest["benchmark_kind"],
                    "data_source": dataset.manifest["source"], "synthetic": dataset.manifest.get("synthetic", False),
                    "membership_audited": dataset.manifest.get("membership_audited", False),
                    "execution": "IDEALIZED_CASH_WITH_MODELED_SHORT_BORROW_NOT_FUTURES",
                    "limitations": ["No historical borrow confirmation, statutory fee schedule or broker execution",
                                    "Daily next-open fills; no intraday stop guarantee; zero idle cash yield",
                                    "Monthly reformation; no six overlapping GGR cohorts in v0.1",
                                    "Price benchmark is not TRI unless provided explicitly",
                                    "No production promotion based on smoke tests"]})
    from pathlib import Path
    code_hash = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))).hexdigest()
    run_id = hashlib.sha256((dataset.digest + code_hash + json.dumps(c.to_dict(), sort_keys=True)).encode()).hexdigest()[:20]
    return {"run_id": run_id, "summary": summary, "equity": frame, "trades": trades,
            "fills": fills, "events": events, "selection_audit": audit, "models": model_history,
            "config": c.to_dict(), "data_manifest": {**dataset.manifest, "code_sha256": code_hash}, "data_digest": dataset.digest}
