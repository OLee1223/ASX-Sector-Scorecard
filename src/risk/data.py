"""Objective 1: download daily prices and convert them to AUD.

pull_prices(tickers, start) is the public contract (see CLAUDE.md). The helpers
below it are pure functions so they can be tested without the network.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BASE_CURRENCY = "AUD"
FX_TICKER = "AUDUSD=X"  # US dollars per Australian dollar


def currency_of(ticker: str) -> str | None:
    """Trading currency inferred from the Yahoo ticker. None = leave as is (FX rates)."""
    if ticker.endswith("=X"):
        return None
    if ticker.endswith(".AX") or ticker.startswith("^AX"):
        return "AUD"
    return "USD"  # US listings, US futures (=F) and other indices


def to_base_currency(prices: pd.DataFrame, audusd: pd.Series) -> pd.DataFrame:
    """Convert USD-priced columns to AUD: AUD price = USD price / (USD per AUD)."""
    out = prices.copy()
    fx = audusd.reindex(out.index).ffill()
    for col in out.columns:
        if currency_of(col) == "USD":
            out[col] = out[col] / fx
    return out


def clean_prices(
    raw: pd.DataFrame,
    min_history_days: int = 250,
    max_daily_move: float = 0.40,
    max_fill_days: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Align calendars, fill short gaps, drop short histories and flag big moves.

    Returns (prices, report). report has one row per input ticker.
    """
    raw = raw.sort_index()
    rows = []
    keep = []
    for t in raw.columns:
        s = raw[t]
        first = s.first_valid_index()
        obs = int(s.notna().sum())
        if first is None:
            rows.append({"ticker": t, "first_date": None, "last_date": None, "observations": 0,
                         "filled_days": 0, "unfilled_gaps": 0, "big_moves": 0,
                         "big_move_dates": "", "status": "dropped: no data"})
            continue
        last = s.last_valid_index()
        live = s.loc[first:last]
        filled = live.ffill(limit=max_fill_days)
        rets = filled.pct_change(fill_method=None)
        big = rets[rets.abs() > max_daily_move]
        status = "ok"
        if obs < min_history_days:
            status = f"dropped: {obs} < {min_history_days} days"
        elif len(big):
            status = "check: big moves"
        rows.append({
            "ticker": t,
            "first_date": first.date(),
            "last_date": last.date(),
            "observations": obs,
            "filled_days": int(filled.notna().sum() - live.notna().sum()),
            "unfilled_gaps": int(filled.isna().sum()),
            "big_moves": len(big),
            "big_move_dates": ", ".join(f"{d.date()} ({r:+.0%})" for d, r in big.items()),
            "status": status,
        })
        if obs >= min_history_days:
            keep.append(t)
            raw.loc[first:last, t] = filled
    report = pd.DataFrame(rows).set_index("ticker")
    return raw[keep], report


def _download(tickers: list[str], start: str) -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(tickers, start=start, progress=False, auto_adjust=True, threads=True)
    if data is None or data.empty:
        raise RuntimeError("No data returned from Yahoo Finance")
    closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    if not isinstance(data.columns, pd.MultiIndex):
        closes.columns = tickers
    closes.index = pd.to_datetime(closes.index).tz_localize(None).normalize()
    closes.index.name = "Date"
    return closes.reindex(columns=tickers)


def pull_prices(tickers: list[str], start: str) -> pd.DataFrame:
    """Daily dividend-adjusted closes in AUD, Date index, one column per ticker.

    Calendars of all tickers are unioned (ASX and US holidays differ) and not yet
    cleaned; pass the result to clean_prices(). AUDUSD=X is downloaded if any
    ticker trades in USD, and is returned only if it was requested.
    """
    tickers = list(dict.fromkeys(tickers))
    need_fx = any(currency_of(t) == "USD" for t in tickers)
    fetch = tickers + ([FX_TICKER] if need_fx and FX_TICKER not in tickers else [])
    raw = _download(fetch, start).replace([np.inf, -np.inf], np.nan)
    raw = raw.dropna(how="all")
    if need_fx:
        raw = to_base_currency(raw, raw[FX_TICKER])
    return raw[tickers]
