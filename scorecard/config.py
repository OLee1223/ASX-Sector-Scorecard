"""Sector definitions and scoring weights."""

BENCHMARK = "^AXJO"  # S&P/ASX 200

# S&P/ASX 200 GICS sector indices as listed on Yahoo Finance.
SECTORS = {
    "^AXEJ": "Energy",
    "^AXMJ": "Materials",
    "^AXNJ": "Industrials",
    "^AXDJ": "Consumer Discretionary",
    "^AXSJ": "Consumer Staples",
    "^AXHJ": "Health Care",
    "^AXFJ": "Financials",
    "^AXIJ": "Information Technology",
    "^AXTJ": "Communication Services",
    "^AXUJ": "Utilities",
    "^AXPJ": "A-REIT",
}

# Trading-day lookbacks.
LOOKBACKS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}

# Composite score weights per factor (should sum to 1).
# "higher" = a higher raw value is better; "lower" = lower is better.
FACTORS = {
    "mom_3m": (0.20, "higher"),
    "mom_6m": (0.20, "higher"),
    "mom_12m": (0.15, "higher"),
    "rel_strength_6m": (0.15, "higher"),
    "trend": (0.15, "higher"),
    "volatility": (0.075, "lower"),
    "max_drawdown": (0.075, "higher"),  # drawdown is negative; closer to 0 is better
}
