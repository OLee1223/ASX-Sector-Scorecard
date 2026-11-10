import numpy as np
import pandas as pd
import pytest

from risk import data
from risk.config import load_config, universe


def frame(cols, n=300, start="2024-01-01"):
    idx = pd.bdate_range(start, periods=n)
    rng = np.random.default_rng(0)
    return pd.DataFrame({c: 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))) for c in cols}, index=idx)


def test_currency_of():
    assert data.currency_of("CBA.AX") == "AUD"
    assert data.currency_of("^AXJO") == "AUD"
    assert data.currency_of("MSFT") == "USD"
    assert data.currency_of("GC=F") == "USD"
    assert data.currency_of("AUDUSD=X") is None


def test_to_base_currency_divides_usd_by_audusd():
    idx = pd.bdate_range("2024-01-01", periods=3)
    prices = pd.DataFrame({"MSFT": [100.0, 110, 120], "CBA.AX": [50.0, 51, 52]}, index=idx)
    fx = pd.Series([0.5, 0.5, 0.8], index=idx)
    out = data.to_base_currency(prices, fx)
    assert out["MSFT"].tolist() == [200.0, 220.0, 150.0]
    assert out["CBA.AX"].tolist() == prices["CBA.AX"].tolist()


def test_clean_fills_short_gaps_only():
    raw = frame(["A"])
    raw.iloc[10:12, 0] = np.nan        # 2-day holiday gap -> filled
    raw.iloc[50:60, 0] = np.nan        # 10-day gap -> longer than max_fill_days, stays partly NaN
    prices, report = data.clean_prices(raw, min_history_days=100, max_fill_days=5)
    assert prices["A"].iloc[10:12].notna().all()
    assert prices["A"].iloc[55:60].isna().all()
    assert report.loc["A", "filled_days"] == 7
    assert report.loc["A", "unfilled_gaps"] == 5


def test_clean_does_not_backfill_before_listing():
    raw = frame(["A", "NEW"])
    raw.iloc[:40, 1] = np.nan
    prices, _ = data.clean_prices(raw, min_history_days=100)
    assert prices["NEW"].iloc[:40].isna().all()


def test_clean_drops_short_history_and_reports_it():
    raw = frame(["A", "SHORT", "EMPTY"])
    raw.iloc[:200, 1] = np.nan
    raw["EMPTY"] = np.nan
    prices, report = data.clean_prices(raw, min_history_days=250)
    assert list(prices.columns) == ["A"]
    assert report.loc["SHORT", "status"].startswith("dropped")
    assert report.loc["EMPTY", "status"] == "dropped: no data"


def test_clean_flags_big_moves_but_keeps_data():
    raw = frame(["A"])
    raw.iloc[100:, 0] *= 0.5            # -50% one-day move
    prices, report = data.clean_prices(raw, min_history_days=100, max_daily_move=0.4)
    assert "A" in prices
    assert report.loc["A", "big_moves"] == 1
    assert report.loc["A", "status"] == "check: big moves"


def test_pull_prices_converts_usd(monkeypatch):
    raw = frame(["CBA.AX", "MSFT", "AUDUSD=X"], n=5)
    raw["AUDUSD=X"] = 0.5
    monkeypatch.setattr(data, "_download", lambda tickers, start: raw[tickers])
    out = data.pull_prices(["CBA.AX", "MSFT"], "2024-01-01")
    assert list(out.columns) == ["CBA.AX", "MSFT"]
    np.testing.assert_allclose(out["MSFT"], raw["MSFT"] / 0.5)
    np.testing.assert_allclose(out["CBA.AX"], raw["CBA.AX"])


def test_repo_config_loads():
    cfg = load_config("config")
    u = universe(cfg)
    assert sum(cfg["portfolio"]["holdings"].values()) == pytest.approx(1_000_000)
    assert set(cfg["portfolio"]["holdings"]) <= set(u)
    assert cfg["themes"]["market"] in u
    assert len(u) == len(set(u))
