# ASX Sector Scorecard

Scores and ranks the 11 S&P/ASX 200 GICS sectors on momentum, relative strength, trend and risk,
using daily index prices from Yahoo Finance.

## Quick start

```bash
pip install -r requirements.txt
python -m scorecard            # prints the table, writes output/scorecard_<date>.csv/.html
python -m pytest -q            # offline tests on synthetic data
```

Options: `--period 2y` (download history, needs at least ~13 months), `--out output`.

## Sectors

| Ticker | Sector | Ticker | Sector |
|---|---|---|---|
| ^AXEJ | Energy | ^AXHJ | Health Care |
| ^AXMJ | Materials | ^AXFJ | Financials |
| ^AXNJ | Industrials | ^AXIJ | Information Technology |
| ^AXDJ | Consumer Discretionary | ^AXTJ | Communication Services |
| ^AXSJ | Consumer Staples | ^AXUJ | Utilities |
| ^AXPJ | A-REIT | ^AXJO | Benchmark: S&P/ASX 200 |

## Methodology

Metrics per sector (`scorecard/metrics.py`):

- **Momentum**: price return over 1, 3, 6 and 12 months (21/63/126/252 trading days).
- **Relative strength**: 6-month return minus the ASX 200's 6-month return.
- **Trend**: average % distance of the last close above its 50- and 200-day moving averages.
- **Volatility**: annualised standard deviation of daily returns over the past year.
- **Max drawdown**: largest peak-to-trough fall over the past year.

Scoring (`scorecard/score.py`): each factor is z-scored across the 11 sectors (sign flipped where lower
is better), combined with the weights in `scorecard/config.py`, re-standardised, and mapped through the
normal CDF to 0–100. **50 = average sector**. Signals: Overweight > 65, Underweight < 35.

Scores are relative, so a sector can rank well while the whole market is falling.

## Limitations

- Index prices are price-only, so dividends aren't included; this hurts high-yield sectors such as
  Financials and A-REITs on raw returns.
- No valuation or earnings data is used yet.
- Yahoo Finance is unofficial and sometimes rate-limits requests (HTTP 429). Re-run if a download fails.

Not financial advice.
