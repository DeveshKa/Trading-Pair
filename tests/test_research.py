from dataclasses import replace
import json
import numpy as np
import pandas as pd
import pytest
from nifty_pairs.alerts import AlertStore
from nifty_pairs.config import Config
from nifty_pairs.data import BAR_COLUMNS, Dataset, make_demo, write_dataset
from nifty_pairs.engine import Position, backtest
from nifty_pairs.selection import PairModel, select_pairs


@pytest.fixture
def demo(tmp_path):
    folder = tmp_path / "demo"
    make_demo(folder, sessions=650)
    return Dataset.load(folder)


def model():
    return PairModel("A", "B", "BANK", "cointegration", 0, 1, 0, .01,
                     100, 100, 10, .001, .002, .001, "2020-01-01", "fixture")


def scenario(tmp_path, monkeypatch, adverse=False, split=False, missing_exit=False, dividend=0):
    dates = pd.bdate_range("2020-01-01", periods=55)
    spread = np.zeros(55)
    spread[40:43] = [.03, .025, 0.08 if adverse else .02]
    rows = []
    for symbol in ["A", "B"]:
        adj = 100 * np.exp(spread) if symbol == "A" else np.full(55, 100.)
        raw = adj.copy()
        if split and symbol == "A":
            raw[42:] /= 2
        opens = np.r_[raw[0], raw[:-1]]
        if split and symbol == "A":
            opens[42] /= 2
        for i, date in enumerate(dates):
            if missing_exit and symbol == "A" and i == 44:
                continue
            rows.append([date, symbol, opens[i], max(opens[i], raw[i]), min(opens[i], raw[i]),
                         raw[i], adj[i], 1000000, dividend if i == 42 and symbol == "A" else 0,
                         2 if split and i == 42 and symbol == "A" else 1, "BANK"])
    folder = tmp_path / "scenario"
    bars = pd.DataFrame(rows, columns=BAR_COLUMNS)
    bench = pd.DataFrame({"date": dates, "close": np.full(55, 100.)})
    members = pd.DataFrame({"symbol": ["A", "B"], "effective_from": dates[0], "effective_to": ""})
    write_dataset(folder, bars, bench, {"source": "test", "price_basis": "raw_execution", "benchmark_kind": "TEST"}, members)
    monkeypatch.setattr("nifty_pairs.engine.select_pairs", lambda *_: ([model()], []))
    c = Config(formation_sessions=40, fee_bps=0, slippage_bps=0,
               short_borrow_annual=0, pair_loss_fraction=.1)
    return backtest(Dataset.load(folder), c)


def test_profit_is_signed_and_reconciled(tmp_path, monkeypatch):
    r = scenario(tmp_path, monkeypatch)
    assert r["summary"]["completed_trades"] == 1
    assert r["trades"][0]["pnl"] > 0
    assert r["summary"]["net_profit"] == pytest.approx(r["summary"]["trade_pnl"])


def test_adverse_move_can_lose(tmp_path, monkeypatch):
    r = scenario(tmp_path, monkeypatch, adverse=True)
    assert r["trades"][0]["pnl"] < 0
    assert r["trades"][0]["reason"] == "SPREAD_STOP"


def test_signal_never_earns_same_day_return(tmp_path, monkeypatch):
    r = scenario(tmp_path, monkeypatch)
    setup = next(e for e in r["events"] if e["kind"] == "RESEARCH_SETUP")
    first_fill = r["fills"][0]
    assert first_fill["date"] > setup["date"]


def test_split_preserves_value_and_pnl(tmp_path, monkeypatch):
    a = tmp_path / "a"; a.mkdir()
    b = tmp_path / "b"; b.mkdir()
    unsplit = scenario(a, monkeypatch)
    split = scenario(b, monkeypatch, split=True)
    assert split["summary"]["net_profit"] == pytest.approx(unsplit["summary"]["net_profit"])
    assert abs(split["trades"][0]["qa"]) == 2 * abs(unsplit["trades"][0]["qa"])


def test_short_dividend_is_a_liability(tmp_path, monkeypatch):
    a = tmp_path / "a"; a.mkdir()
    b = tmp_path / "b"; b.mkdir()
    normal = scenario(a, monkeypatch)
    dividend = scenario(b, monkeypatch, dividend=1)
    assert dividend["summary"]["net_profit"] == pytest.approx(normal["summary"]["net_profit"] + normal["trades"][0]["qa"])
    assert dividend["summary"]["net_profit"] == pytest.approx(dividend["summary"]["trade_pnl"])


def test_missing_exit_does_not_create_fill(tmp_path, monkeypatch):
    r = scenario(tmp_path, monkeypatch, missing_exit=True)
    assert any(e["reason"] == "MISSING_OR_UNTRADED_OPEN" for e in r["events"])
    assert r["trades"][0]["closed"] == "2020-03-04"


def test_ledger_matches_closed_portfolio(demo):
    r = backtest(demo, Config(strategy="distance"))
    assert r["summary"]["completed_trades"] > 0
    assert r["summary"]["open_pairs_at_end"] == 0
    assert r["summary"]["net_profit"] == pytest.approx(r["summary"]["trade_pnl"], abs=1e-7)
    assert r["summary"]["fees"] > 0 and r["summary"]["borrow_cost"] > 0


def test_future_poisoning_cannot_change_past_decisions(demo):
    c = Config(formation_sessions=100)
    first = backtest(demo, c)
    cutoff = sorted(demo.bars.date.unique())[400]
    modified = demo.bars.copy()
    mask = modified.date > cutoff
    modified.loc[mask, ["open", "high", "low", "close", "adj_close"]] *= 3
    second = backtest(replace(demo, bars=modified), c)
    a = first["equity"]
    end = str(pd.Timestamp(cutoff).date())
    pd.testing.assert_frame_equal(a.loc[a.date <= end], second["equity"].loc[second["equity"].date <= end])
    assert [e for e in first["events"] if e["date"] <= end] == [e for e in second["events"] if e["date"] <= end]


def test_holm_adjustment_and_future_selection(demo):
    date = sorted(demo.bars.date.unique())[300]
    models, audit = select_pairs(demo, date, Config(strategy="cointegration",same_sector=True))
    assert audit
    assert all(r["adjusted_pvalue"] >= r["pvalue"] for r in audit)
    modified = replace(demo, bars=demo.bars.loc[demo.bars.date <= date].copy())
    assert select_pairs(modified, date, Config(strategy="cointegration",same_sector=True))[1] == audit
    assert all(m.adjusted_pvalue <= .05 for m in models)


def test_alert_replay_is_idempotent(tmp_path):
    store = AlertStore(tmp_path / "events.sqlite")
    assert store.put("one", "2020-01-01", "SETUP", {"z": 2.1})
    assert not store.put("one", "2020-01-01", "SETUP", {"z": 2.1})
    assert len(AlertStore(tmp_path / "events.sqlite").rows()) == 1


def test_member_end_is_exclusive(demo):
    end = sorted(demo.bars.date.unique())[300]
    m = demo.membership.copy()
    m.loc[0, "effective_to"] = end
    d = replace(demo, membership=m)
    assert m.iloc[0].symbol in d.members(pd.Timestamp(end) - pd.Timedelta(days=1))
    assert m.iloc[0].symbol not in d.members(end)


def test_missing_benchmark_and_duplicate_bars_rejected(tmp_path):
    folder = tmp_path / "d"
    make_demo(folder, 350)
    bars = pd.read_csv(folder / "bars.csv")
    pd.concat([bars, bars.iloc[[0]]]).to_csv(folder / "bars.csv", index=False)
    with pytest.raises(ValueError, match="duplicate"):
        Dataset.load(folder)
    bars.to_csv(folder / "bars.csv", index=False)
    benchmark = pd.read_csv(folder / "benchmark.csv")
    benchmark.iloc[1:].to_csv(folder / "benchmark.csv", index=False)
    with pytest.raises(ValueError, match="Benchmark missing"):
        Dataset.load(folder)


def test_membership_required_unless_explicit(demo):
    with pytest.raises(ValueError, match="membership required"):
        backtest(replace(demo, membership=None), Config())


def test_risk_limits_can_reject_all_entries(demo):
    r = backtest(demo, Config(strategy="distance", max_gross_fraction=.01))
    assert r["summary"]["completed_trades"] == 0
    assert any(e["reason"] == "PORTFOLIO_EXPOSURE_LIMIT" for e in r["events"])


@pytest.mark.parametrize("kwargs", [{"entry_z": 0}, {"initial_capital": float("nan")},
                                    {"fee_bps": -1}, {"strategy": "unknown"},
                                    {"require_membership": "false"}, {"formation_sessions": True}])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_scanner_is_as_of_and_outbox_deduplicates(demo, tmp_path):
    from nifty_pairs.scan import scan, save_scan
    c = Config(strategy="distance")
    date = sorted(demo.bars.date.unique())[400]
    result = scan(demo, c, date)
    shorter = replace(demo, bars=demo.bars.loc[demo.bars.date <= date])
    assert scan(shorter, c, date) == result
    assert result["pairs"] and all(not p["execution_ready"] for p in result["pairs"])
    path = tmp_path / "scan"
    save_scan(result, path)
    n = len(AlertStore(path / "alerts.sqlite").rows())
    save_scan(result, path)
    assert len(AlertStore(path / "alerts.sqlite").rows()) == n
