"""Weighted risk score and component ablation helpers."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def weighted_risk(
    components: Mapping[str, ArrayLike],
    weights: Mapping[str, float] | None = None,
) -> FloatArray:
    """Combine normalized components with the specified weighted sum."""
    selected_weights = weights or {"uncertainty": 0.5, "anomaly": 0.2, "consequence": 0.3}
    if not selected_weights or any(value < 0 for value in selected_weights.values()):
        raise ValueError("Risk weights must be nonempty and nonnegative")
    total = float(sum(selected_weights.values()))
    if total <= 0:
        raise ValueError("At least one risk weight must be positive")
    missing = set(selected_weights) - set(components)
    if missing:
        raise ValueError(f"Missing risk components: {sorted(missing)}")
    arrays = [np.asarray(components[key], dtype=np.float64) for key in selected_weights]
    if len({array.shape for array in arrays}) != 1:
        raise ValueError("Risk component arrays must have the same shape")
    result = np.zeros_like(arrays[0], dtype=np.float64)
    for key, values in zip(selected_weights, arrays, strict=True):
        result += (float(selected_weights[key]) / total) * values
    return result
