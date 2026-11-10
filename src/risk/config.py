"""Load the YAML files in config/ into one dict."""
from __future__ import annotations

from pathlib import Path

import yaml


def load_config(config_dir: str | Path = "config") -> dict:
    """Return {"portfolio": ..., "themes": ..., "model": ...} from config_dir."""
    config_dir = Path(config_dir)
    cfg = {}
    for name in ("portfolio", "themes", "model"):
        path = config_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Missing config file: {path}")
        cfg[name] = yaml.safe_load(path.read_text()) or {}
    return cfg


def universe(cfg: dict) -> list[str]:
    """Every ticker the model needs: holdings, theme members, market and extra factors."""
    seen: dict[str, None] = {}
    for t in cfg["portfolio"]["holdings"]:
        seen[t] = None
    for members in cfg["themes"].get("themes", {}).values():
        for t in members:
            seen[t] = None
    seen[cfg["themes"]["market"]] = None
    for t in cfg["themes"].get("extra_factors", []):
        seen[t] = None
    return list(seen)
