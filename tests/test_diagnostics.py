from dataclasses import replace
import json
import numpy as np
import pandas as pd
import pytest
from nifty_pairs.config import Config
from nifty_pairs.data import BAR_COLUMNS, Dataset, YFinanceProvider, write_dataset
from nifty_pairs.diagnostics import DiagnosticConfig, corr, diagnose, relationship_test, save_diagnostics
from nifty_pairs.engine import backtest


@pytest.fixture
def relationship_data(tmp_path):
    rng = np.random.default_rng(12)
    dates = pd.bdate_range("2005-01-03", periods=400)
    x = 5 + np.cumsum(rng.normal(.001, .012, len(dates)))
    error = np.zeros(len(dates))
    for i in range(1, len(dates)):
        error[i] = .7 * error[i-1] + rng.normal(0, .004)
    rows = []
    for symbol, values in [("A", np.exp(x)), ("B", np.exp(.2 + x + error))]:
        for date, value in zip(dates, values):
            rows.append([date, symbol, value, value, value, value, value, 1_000_000, 0, 1, "TEST"])
    folder = tmp_path / "data"
    write_dataset(folder, pd.DataFrame(rows, columns=BAR_COLUMNS),
                  pd.DataFrame({"date": dates, "close": np.exp(x)}),
                  {"source": "synthetic_test", "synthetic": True, "price_basis": "raw_execution",
                   "benchmark_kind": "SYNTHETIC"})
    return Dataset.load(folder)


def small_config():
    return DiagnosticConfig(horizons=(60, 120, 5040), rolling_correlation_sessions=60,
                            rolling_coint_sessions=120, rolling_step=60, bootstrap_repeats=20)


def test_long_horizon_is_not_fabricated(relationship_data):
    r = diagnose(relationship_data, small_config())
    twenty = next(w for w in r["windows"] if w["sessions_requested"] == 5040)
    assert not twenty["window_complete"]
    assert twenty["level_observations"] == 400
    assert twenty["test_status"] == "INSUFFICIENT_HISTORY"
    assert not twenty["cointegration_evidence"]
    assert not r["pairs"][0]["execution_ready"]


def test_as_of_cutoff_does_not_see_future(relationship_data):
    date = sorted(relationship_data.bars.date.unique())[250]
    a = diagnose(relationship_data, small_config(), as_of=date)
    poisoned = relationship_data.bars.copy()
    poisoned.loc[poisoned.date > date, "adj_close"] *= 10
    b = diagnose(replace(relationship_data, bars=poisoned), small_config(), as_of=date)
    assert a == b


def test_gaps_do_not_create_daily_returns_or_cointegration(relationship_data):
    bars = relationship_data.bars.copy()
    day = sorted(bars.date.unique())[-30]
    bars = bars.loc[~((bars.date == day) & (bars.symbol == "A"))]
    r = diagnose(replace(relationship_data, bars=bars), small_config())
    w = next(w for w in r["windows"] if w["sessions_requested"] == 60)
    assert w["level_observations"] == 59
    assert w["return_observations"] == 58
    assert w["test_status"] == "GAPS_IN_COINTEGRATION_WINDOW"
    assert not w["cointegration_evidence"]


def test_correction_and_intervals_are_reproducible(relationship_data):
    a = diagnose(relationship_data, small_config())
    assert a == diagnose(relationship_data, small_config())
    family = a["windows"] + a["rolling_cointegration"]
    assert a["hypotheses_in_joint_holm_family"] == len(family)
    assert all(w["holm_pvalue"] >= w["pvalue"] for w in family)
    assert a["rolling_correlation"][-1]["date"] == a["as_of"]
    assert a["rolling_cointegration"][-1]["end"] == a["as_of"]


def test_visual_price_similarity_is_not_return_correlation():
    rng = np.random.default_rng(23)
    x = np.arange(1000) + rng.normal(0, .1, 1000)
    y = np.arange(1000) + rng.normal(0, .1, 1000)
    assert corr(x,y) > .99
    assert abs(corr(np.diff(x), np.diff(y))) < .15


def test_duplicate_and_stationary_series_not_tradable():
    x = np.exp(np.linspace(1, 2, 500))
    assert relationship_test(pd.DataFrame({"A": x, "B": 2*x}))["test_status"] == "DEGENERATE"
    rng = np.random.default_rng(2)
    levels = pd.DataFrame(np.exp(rng.normal(5, .1, (500,2))), columns=["A","B"])
    assert not relationship_test(levels)["integration_compatible"]


def test_json_report_has_no_nan(relationship_data, tmp_path):
    result = diagnose(relationship_data, small_config())
    output = tmp_path / "result"
    save_diagnostics(result, output)
    loaded = json.loads((output / "diagnostics.json").read_text())
    assert loaded["pair_count"] == 1
    assert "RESEARCH DIAGNOSTICS" in (output / "report.html").read_text()


def test_diagnostic_snapshots_block_backtesting(relationship_data):
    d = replace(relationship_data, manifest={**relationship_data.manifest, "usage": "relationship_diagnostics_only"})
    with pytest.raises(ValueError, match="Diagnostics-only"):
        backtest(d, Config(require_membership=False))


def test_sector_exclusion_is_explicit(relationship_data):
    assert diagnose(relationship_data, small_config(), sectors={"A":"ONE","B":"TWO"})["pair_count"] == 0
    assert diagnose(relationship_data, small_config(), sectors={"A":"ONE","B":"TWO"}, same_sector=False)["pair_count"] == 1
