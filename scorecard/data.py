"""Price download from Yahoo Finance."""
from __future__ import annotations

import pandas as pd
import yfinance as yf

from .config import BENCHMARK, SECTORS


def fetch_prices(period: str = "2y", tickers: list[str] | None = None) -> pd.DataFrame:
    """Return adjusted daily closes, one column per ticker, indexed by date."""
    tickers = tickers or [BENCHMARK, *SECTORS]
    data = yf.download(tickers, period=period, progress=False, auto_adjust=True)
    if data.empty:
        raise RuntimeError("No data returned from Yahoo Finance")
    closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    closes = closes.dropna(how="all").ffill()
    missing = [t for t in tickers if t not in closes.columns or closes[t].isna().all()]
    if missing:
        raise RuntimeError(f"No data for: {', '.join(missing)}")
    return closes[tickers]
