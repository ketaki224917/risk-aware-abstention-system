"""Load and validate the project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read YAML settings and validate assumptions shared by the pipeline."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"Configuration must contain a mapping: {config_path}")
    weights = config["risk"]["weights"]
    if set(weights) != {"uncertainty", "anomaly", "consequence"}:
        raise ValueError("Risk weights must define uncertainty, anomaly, and consequence")
    if any(float(weight) < 0 for weight in weights.values()):
        raise ValueError("Risk weights must be nonnegative")
    if abs(sum(float(weight) for weight in weights.values()) - 1.0) > 1e-9:
        raise ValueError("Risk weights must sum to 1")
    if config["policy"]["automatic_percentile"] >= config["policy"]["assisted_percentile"]:
        raise ValueError("Automatic percentile must be lower than assisted percentile")
    return config
