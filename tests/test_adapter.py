import sys
from types import SimpleNamespace
import pandas as pd
import pytest
from nifty_pairs.data import Dataset, YFinanceProvider
from nifty_pairs.scan import scan, save_scan
from nifty_pairs.config import Config
from nifty_pairs.alerts import AlertStore


def install_fake(monkeypatch, missing_benchmark=False, event_on_missing=False):
    dates = pd.date_range("2020-01-01", periods=4, tz="Asia/Kolkata")
    class Ticker:
        def __init__(self, symbol): self.symbol = symbol
        def history(self, **kwargs):
            if self.symbol == "^NSEI":
                return pd.DataFrame({"Close": [100., 101., 102., 103.]}, index=dates).drop(dates[1]) if missing_benchmark else pd.DataFrame({"Close": [100., 101., 102., 103.]}, index=dates)
            return pd.DataFrame({"Open": [50., 51., 52., 53.], "High": [51.,52.,53.,54.],
                                 "Low": [49.,50.,51.,52.], "Close": [50.,51.,52.,53.],
                                 "Adj Close": [49.,50.,51.,52.], "Volume": [1000]*4,
                                 "Dividends": [0., 1. if event_on_missing else 0., 0., 0.],
                                 "Stock Splits": [0.,0.,2.,0.]}, index=dates)
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=Ticker, __version__="fixture"))


def test_library_split_reconstruction(tmp_path, monkeypatch):
    install_fake(monkeypatch)
    path = tmp_path / "library"
    YFinanceProvider().download(["A.NS"], "2020-01-01", "2020-01-05", path)
    d = Dataset.load(path)
    assert d.bars.close.tolist() == [100.,102.,52.,53.]
    assert d.bars.split.tolist() == [1.,1.,2.,1.]
    assert d.manifest["membership_audited"] is False


def test_library_calendar_failure_is_atomic(tmp_path, monkeypatch):
    install_fake(monkeypatch, missing_benchmark=True)
    path = tmp_path / "library"
    with pytest.raises(ValueError, match="Benchmark missing"):
        YFinanceProvider().download(["A.NS"], "2020-01-01", "2020-01-05", path)
    assert not path.exists()


def test_explicit_calendar_policy_records_omissions(tmp_path, monkeypatch):
    install_fake(monkeypatch, missing_benchmark=True)
    path = tmp_path / "library"
    YFinanceProvider().download(["A.NS"], "2020-01-01", "2020-01-05", path, allow_calendar_intersection=True)
    d = Dataset.load(path)
    assert d.manifest["excluded_equity_sessions"] == ["2020-01-02"]
    assert len(d.bars) == 3


def test_calendar_cannot_drop_corporate_actions(tmp_path, monkeypatch):
    install_fake(monkeypatch, missing_benchmark=True, event_on_missing=True)
    with pytest.raises(ValueError, match="corporate actions"):
        YFinanceProvider().download(["A.NS"], "2020-01-01", "2020-01-05", tmp_path / "library", allow_calendar_intersection=True)
