"""CLI: python -m scorecard [--period 2y] [--out output]"""
from __future__ import annotations

import argparse
from pathlib import Path

from .data import fetch_prices
from .metrics import compute_metrics
from .report import print_table, write_csv, write_html
from .score import score


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Score and rank the ASX 200 GICS sectors.")
    p.add_argument("--period", default="2y", help="History to download (default 2y; need >= ~13 months)")
    p.add_argument("--out", default="output", help="Directory for CSV/HTML output")
    args = p.parse_args(argv)

    prices = fetch_prices(args.period)
    scored = score(compute_metrics(prices))
    as_of = prices.index[-1].date()

    print(f"ASX 200 Sector Scorecard - data as of {as_of}\n")
    print_table(scored)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(scored, out / f"scorecard_{as_of}.csv")
    write_html(scored, out / f"scorecard_{as_of}.html", as_of)
    write_html(scored, out / "latest.html", as_of)
    print(f"\nWrote {out}/scorecard_{as_of}.csv and .html")


if __name__ == "__main__":
    main()
