"""Turn metrics into a 0-100 composite score and rank."""
from __future__ import annotations

import math

import pandas as pd

from .config import FACTORS


def _zscore(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0.0


def score(metrics: pd.DataFrame) -> pd.DataFrame:
    """Add per-factor z-scores, a composite score (0-100, 50 = average) and rank."""
    out = metrics.copy()
    composite = pd.Series(0.0, index=out.index)
    total_w = sum(w for w, _ in FACTORS.values())
    for col, (weight, better) in FACTORS.items():
        z = _zscore(out[col].astype(float)).fillna(0.0)
        if better == "lower":
            z = -z
        out[f"z_{col}"] = z
        composite += weight * z
    composite /= total_w
    # Standardise the composite and map through the normal CDF: 50 = average sector,
    # ~84 = one standard deviation above average, ~16 = one below.
    z = _zscore(composite)
    out["score"] = z.map(lambda v: 50 * (1 + math.erf(v / math.sqrt(2))))
    out["composite_z"] = composite
    out["rank"] = out["score"].rank(ascending=False, method="min").astype(int)
    out["signal"] = pd.cut(
        out["score"], bins=[-0.01, 35, 65, 100.01], labels=["Underweight", "Neutral", "Overweight"]
    )
    return out.sort_values("rank")
