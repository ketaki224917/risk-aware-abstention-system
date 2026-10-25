"""Three-level policy using validation risk percentiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import ArrayLike, NDArray


class DecisionLevel(StrEnum):
    """Routing destination for a case."""

    AUTOMATIC = "Automatic"
    ASSISTED = "Assisted"
    HUMAN_REVIEW = "Human Review"


@dataclass(frozen=True)
class PolicyThresholds:
    """Two risk cutoffs selected from validation scores."""

    automatic_max: float
    assisted_max: float

    @classmethod
    def fit(
        cls,
        validation_risk: ArrayLike,
        *,
        automatic_percentile: float = 70,
        assisted_percentile: float = 90,
    ) -> PolicyThresholds:
        """Select t70/t90 from validation data, without consulting test outcomes."""
        risk = np.asarray(validation_risk, dtype=np.float64)
        if risk.size == 0 or not np.isfinite(risk).all():
            raise ValueError("Validation risk must be nonempty and finite")
        if not 0 <= automatic_percentile <= 100 or not 0 <= assisted_percentile <= 100:
            raise ValueError("Percentiles must lie between 0 and 100")
        if automatic_percentile > assisted_percentile:
            raise ValueError("Automatic percentile must not exceed assisted percentile")
        thresholds = cls(
            automatic_max=float(np.percentile(risk, automatic_percentile, method="linear")),
            assisted_max=float(np.percentile(risk, assisted_percentile, method="linear")),
        )
        if thresholds.automatic_max > thresholds.assisted_max:
            raise ValueError("Threshold ordering violated")
        return thresholds

    def route(self, risk: ArrayLike) -> NDArray[np.object_]:
        """Route each score using R <= t70, t70 < R <= t90, and R > t90."""
        values = np.asarray(risk, dtype=np.float64)
        if not np.isfinite(values).all():
            raise ValueError("Risk values must be finite")
        levels = np.full(values.shape, DecisionLevel.HUMAN_REVIEW, dtype=object)
        levels[values <= self.assisted_max] = DecisionLevel.ASSISTED
        levels[values <= self.automatic_max] = DecisionLevel.AUTOMATIC
        return levels

    def route_one(self, risk: float) -> DecisionLevel:
        """Route a single risk score."""
        return DecisionLevel(str(self.route([risk])[0]))
