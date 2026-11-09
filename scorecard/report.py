"""Console, CSV and HTML output."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import pandas as pd

PCT_COLS = ["mom_1m", "mom_3m", "mom_6m", "mom_12m", "rel_strength_6m", "trend", "volatility", "max_drawdown"]
HEADERS = {
    "rank": "Rank", "sector": "Sector", "score": "Score", "signal": "Signal",
    "mom_1m": "1M", "mom_3m": "3M", "mom_6m": "6M", "mom_12m": "12M",
    "rel_strength_6m": "6M vs ASX200", "trend": "Trend", "above_50dma": ">50DMA",
    "above_200dma": ">200DMA", "volatility": "Vol (ann.)", "max_drawdown": "Max DD (1Y)",
}


def to_table(scored: pd.DataFrame) -> pd.DataFrame:
    return scored.reset_index()[["ticker", *HEADERS]]


def print_table(scored: pd.DataFrame) -> None:
    t = to_table(scored).drop(columns="ticker").copy()
    for c in PCT_COLS:
        t[c] = t[c].map(lambda v, c=c: f"{v:.1%}" if c == "volatility" else f"{v:+.1%}")
    t["score"] = t["score"].map(lambda v: f"{v:.0f}")
    for c in ("above_50dma", "above_200dma"):
        t[c] = t[c].map({True: "Y", False: "-"})
    print(t.rename(columns=HEADERS).to_string(index=False))


def write_csv(scored: pd.DataFrame, path: Path) -> None:
    to_table(scored).to_csv(path, index=False, float_format="%.6f")


def write_html(scored: pd.DataFrame, path: Path, as_of: date) -> None:
    t = to_table(scored).drop(columns="ticker")
    head = "".join(f"<th>{html.escape(HEADERS[c])}</th>" for c in t.columns)
    body = []
    for _, r in t.iterrows():
        cells = []
        for c in t.columns:
            v = r[c]
            cls = ""
            if c in PCT_COLS:
                txt = f"{v:.1%}" if c == "volatility" else f"{v:+.1%}"
                if c != "volatility":
                    cls = "pos" if v > 0 else "neg" if v < 0 else ""
            elif c == "score":
                txt = f"{v:.0f}"
            elif c in ("above_50dma", "above_200dma"):
                txt, cls = ("Yes", "pos") if v else ("No", "neg")
            elif c == "signal":
                txt, cls = str(v), f"sig-{str(v).lower()}"
            else:
                txt = html.escape(str(v))
            cells.append(f'<td class="{cls}">{txt}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    path.write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASX Sector Scorecard {as_of}</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1b1b1b; background: #fff; }}
 h1 {{ font-size: 1.4rem; margin-bottom: .2rem; }}
 p.meta {{ color: #666; margin-top: 0; }}
 .wrap {{ overflow-x: auto; }}
 table {{ border-collapse: collapse; font-size: .9rem; font-variant-numeric: tabular-nums; }}
 th, td {{ padding: .45rem .7rem; border-bottom: 1px solid #e3e3e3; text-align: right; white-space: nowrap; }}
 th:nth-child(2), td:nth-child(2), th:nth-child(4), td:nth-child(4) {{ text-align: left; }}
 th {{ background: #f5f5f5; position: sticky; top: 0; }}
 .pos {{ color: #0a7a3d; }} .neg {{ color: #b3261e; }}
 .sig-overweight {{ color: #0a7a3d; font-weight: 600; }}
 .sig-underweight {{ color: #b3261e; font-weight: 600; }}
 .sig-neutral {{ color: #555; }}
 @media (prefers-color-scheme: dark) {{
  body {{ background: #141414; color: #e8e8e8; }} th {{ background: #222; }}
  th, td {{ border-color: #333; }} .pos, .sig-overweight {{ color: #5fd38d; }}
  .neg, .sig-underweight {{ color: #ff8a80; }} .sig-neutral, p.meta {{ color: #aaa; }}
 }}
</style></head><body>
<h1>ASX 200 Sector Scorecard</h1>
<p class="meta">Data as of {as_of} (Yahoo Finance, S&amp;P/ASX 200 GICS sector indices). Score 0&ndash;100 ranks
sectors relative to each other on momentum, relative strength, trend and risk. Not financial advice.</p>
<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>
{''.join(body)}
</tbody></table></div>
</body></html>
""", encoding="utf-8")
