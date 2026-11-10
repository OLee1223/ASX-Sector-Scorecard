"""Command-line entry point: python -m risk.cli <step> [--config config/] [--seed 42]"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .config import load_config, universe

STEPS = ["pull", "regress", "montecarlo", "stress", "backtest"]


def _run_dir(config_dir: Path) -> Path:
    out = Path("outputs") / datetime.now().strftime("%Y-%m-%d_%H%M")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(config_dir, out / "config", dirs_exist_ok=True)
    return out


def step_pull(cfg: dict, run_dir: Path) -> None:
    from .data import clean_prices, pull_prices

    d = cfg["model"]["data"]
    tickers = universe(cfg)
    print(f"Downloading {len(tickers)} tickers from {d['start']} ...")
    raw = pull_prices(tickers, d["start"])
    prices, report = clean_prices(raw, d["min_history_days"], d["max_daily_move"], d["max_fill_days"])

    Path("data").mkdir(exist_ok=True)
    prices.to_parquet("data/prices.parquet")
    report.to_csv("data/coverage.csv")
    report.to_csv(run_dir / "coverage.csv")

    print(f"\nPrices: {prices.shape[1]} tickers, {prices.index[0].date()} to {prices.index[-1].date()}"
          f" ({len(prices)} days) -> data/prices.parquet")
    print(report[["first_date", "observations", "big_moves", "status"]].to_string())
    dropped = report.index[report["status"].str.startswith("dropped")].tolist()
    held = set(cfg["portfolio"]["holdings"])
    if held & set(dropped):
        print(f"\nWARNING: holdings dropped for short/no history: {sorted(held & set(dropped))}")
    elif dropped:
        print(f"\nDropped (not holdings): {dropped}")
    flagged = report.index[report["status"] == "check: big moves"].tolist()
    if flagged:
        print(f"Check for data errors (daily move > {d['max_daily_move']:.0%}): {flagged}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m risk.cli", description=__doc__)
    p.add_argument("step", choices=STEPS + ["all"])
    p.add_argument("--config", default="config", help="config directory (default: config/)")
    p.add_argument("--seed", type=int, default=None, help="overrides the seed in model.yaml")
    args = p.parse_args(argv)

    config_dir = Path(args.config)
    cfg = load_config(config_dir)
    if args.seed is not None:
        cfg["model"]["seed"] = args.seed
    run_dir = _run_dir(config_dir)

    implemented = {"pull": step_pull}
    for step in STEPS if args.step == "all" else [args.step]:
        if step not in implemented:
            print(f"'{step}' is not implemented yet (see README objectives).", file=sys.stderr)
            return 2
        implemented[step](cfg, run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
