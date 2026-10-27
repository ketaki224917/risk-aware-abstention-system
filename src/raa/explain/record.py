"""Immutable structured decision record used to ground explanations."""

from __future__ import annotations

from dataclasses import dataclass

from raa.risk.policy import DecisionLevel


@dataclass(frozen=True)
class DecisionRecord:
    """Complete prediction and routing state; explanation code receives read-only data."""

    predicted_class: int
    malignant_probability: float
    uncertainty: float
    anomaly: float
    consequence: float
    risk: float
    level: DecisionLevel
    automatic_threshold: float
    assisted_threshold: float
    referral_reason: str = ""
    measured_feature_count: int = 30
    estimated_feature_count: int = 0
    input_warnings: tuple[str, ...] = ()

    @property
    def predicted_label(self) -> str:
        """Human-readable predicted class."""
        return "malignant" if self.predicted_class == 0 else "benign"

    @property
    def confidence(self) -> float:
        """Model confidence in the predicted class; not calibrated error risk."""
        if self.predicted_class == 0:
            return self.malignant_probability
        return 1.0 - self.malignant_probability

    @property
    def risk_tier(self) -> str:
        """Describe the policy tier from the same thresholds used for routing."""
        if self.risk <= self.automatic_threshold:
            return "lower"
        if self.risk <= self.assisted_threshold:
            return "intermediate"
        return "higher"

