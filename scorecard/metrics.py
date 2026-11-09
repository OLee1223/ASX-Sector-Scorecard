"""Per-sector metrics computed from daily closes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BENCHMARK, LOOKBACKS, SECTORS


def _ret(s: pd.Series, n: int) -> float:
    s = s.dropna()
    if len(s) <= n:
        return np.nan
    return s.iloc[-1] / s.iloc[-1 - n] - 1


def compute_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    """One row per sector with return, trend and risk metrics."""
    bench = prices[BENCHMARK]
    rows = []
    for ticker, name in SECTORS.items():
        s = prices[ticker].dropna()
        last_year = s.iloc[-LOOKBACKS["12M"]:]
        daily = last_year.pct_change().dropna()
        sma50 = s.rolling(50).mean().iloc[-1]
        sma200 = s.rolling(200).mean().iloc[-1]
        last = s.iloc[-1]
        row = {
            "ticker": ticker,
            "sector": name,
            "last": last,
            **{f"mom_{k.lower()}": _ret(s, n) for k, n in LOOKBACKS.items()},
            "rel_strength_6m": _ret(s, LOOKBACKS["6M"]) - _ret(bench, LOOKBACKS["6M"]),
            "above_50dma": bool(last > sma50),
            "above_200dma": bool(last > sma200),
            # Trend: average % distance above the 50- and 200-day averages.
            "trend": np.nanmean([last / sma50 - 1, last / sma200 - 1]),
            "volatility": daily.std() * np.sqrt(252),
            "max_drawdown": (last_year / last_year.cummax() - 1).min(),
        }
        rows.append(row)
    return pd.DataFrame(rows).set_index("ticker")
