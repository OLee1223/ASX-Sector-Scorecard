import numpy as np
import pandas as pd

from scorecard.config import BENCHMARK, SECTORS
from scorecard.metrics import compute_metrics
from scorecard.score import score


def synthetic_prices(days=400):
    idx = pd.bdate_range("2024-01-01", periods=days)
    rng = np.random.default_rng(0)
    cols = {}
    # Each sector gets a different drift so the ranking is predictable.
    for i, t in enumerate([BENCHMARK, *SECTORS]):
        drift = (i - 6) * 0.0004
        cols[t] = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.002, days)))
    return pd.DataFrame(cols, index=idx)


def test_metrics_shape_and_returns():
    prices = synthetic_prices()
    m = compute_metrics(prices)
    assert list(m.index) == list(SECTORS)
    t = "^AXEJ"
    expected = prices[t].iloc[-1] / prices[t].iloc[-1 - 63] - 1
    assert np.isclose(m.loc[t, "mom_3m"], expected)
    assert (m["max_drawdown"] <= 0).all()
    assert (m["volatility"] > 0).all()


def test_score_range_and_order():
    s = score(compute_metrics(synthetic_prices()))
    assert s["score"].between(0, 100).all()
    assert abs(s["score"].median() - 50) < 15
    assert sorted(s["rank"]) == list(range(1, len(SECTORS) + 1))
    # Highest-drift sector (last in dict) should beat the lowest-drift one (first).
    tickers = list(SECTORS)
    assert s.loc[tickers[-1], "rank"] < s.loc[tickers[0], "rank"]
