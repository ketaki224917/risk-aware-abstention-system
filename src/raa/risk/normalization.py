"""Paper-defined scaling for validation uncertainty and training anomaly scores."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ComponentNormalizer:
    """Scale U by validation p95 and A by training min/p99, never using test data."""

    uncertainty_p95: float
    anomaly_min: float
    anomaly_p99: float

    @classmethod
    def fit(
        cls, validation_uncertainty: ArrayLike, training_anomaly: ArrayLike
    ) -> ComponentNormalizer:
        """Fit U's p95 on validation and A's min/p99 on training scores."""
        u = np.asarray(validation_uncertainty, dtype=np.float64)
        a = np.asarray(training_anomaly, dtype=np.float64)
        if u.size == 0 or a.size == 0 or not np.isfinite(u).all() or not np.isfinite(a).all():
            raise ValueError("Fitting component scores must be nonempty and finite")
        return cls(
            float(np.percentile(u, 95)),
            float(a.min()),
            float(np.percentile(a, 99)),
        )

    @staticmethod
    def _scale_anomaly(values: ArrayLike, minimum: float, maximum: float) -> FloatArray:
        x = np.asarray(values, dtype=np.float64)
        if maximum <= minimum:
            return np.zeros_like(x)
        return np.clip((x - minimum) / (maximum - minimum), 0.0, 1.0)

    @staticmethod
    def _scale_uncertainty(values: ArrayLike, percentile_95: float) -> FloatArray:
        x = np.asarray(values, dtype=np.float64)
        if percentile_95 <= 0:
            return np.zeros_like(x)
        return np.clip(x / percentile_95, 0.0, 1.0)

    def transform(
        self, uncertainty: ArrayLike, anomaly: ArrayLike, consequence: ArrayLike
    ) -> dict[str, FloatArray]:
        """Scale U by validation p95 and A by training min/p99; C is already [0, 1]."""
        u = self._scale_uncertainty(uncertainty, self.uncertainty_p95)
        a = self._scale_anomaly(anomaly, self.anomaly_min, self.anomaly_p99)
        c = np.asarray(consequence, dtype=np.float64)
        if not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
            raise ValueError("Consequence values must be finite and in [0, 1]")
        if not (u.shape == a.shape == c.shape):
            raise ValueError("Risk component arrays must have the same shape")
        return {"uncertainty": u, "anomaly": a, "consequence": c}
