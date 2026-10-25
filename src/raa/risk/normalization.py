"""Validation-fitted min-max normalization for uncertainty and anomaly scores."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ComponentNormalizer:
    """Component ranges learned from validation data, never from the test set."""

    uncertainty_min: float
    uncertainty_max: float
    anomaly_min: float
    anomaly_max: float

    @classmethod
    def fit(cls, uncertainty: ArrayLike, anomaly: ArrayLike) -> ComponentNormalizer:
        """Fit component ranges on validation predictions only."""
        u = np.asarray(uncertainty, dtype=np.float64)
        a = np.asarray(anomaly, dtype=np.float64)
        if u.size == 0 or a.size == 0 or not np.isfinite(u).all() or not np.isfinite(a).all():
            raise ValueError("Validation component scores must be nonempty and finite")
        return cls(float(u.min()), float(u.max()), float(a.min()), float(a.max()))

    @staticmethod
    def _scale(values: ArrayLike, minimum: float, maximum: float) -> FloatArray:
        x = np.asarray(values, dtype=np.float64)
        if maximum <= minimum:
            return np.zeros_like(x)
        return np.clip((x - minimum) / (maximum - minimum), 0.0, 1.0)

    def transform(
        self, uncertainty: ArrayLike, anomaly: ArrayLike, consequence: ArrayLike
    ) -> dict[str, FloatArray]:
        """Normalize U/A using validation ranges; C is already specified in [0, 1]."""
        u = self._scale(uncertainty, self.uncertainty_min, self.uncertainty_max)
        a = self._scale(anomaly, self.anomaly_min, self.anomaly_max)
        c = np.asarray(consequence, dtype=np.float64)
        if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
            raise ValueError("Consequence values must be finite and in [0, 1]")
        if not (u.shape == a.shape == c.shape):
            raise ValueError("Risk component arrays must have the same shape")
        return {"uncertainty": u, "anomaly": a, "consequence": c}
