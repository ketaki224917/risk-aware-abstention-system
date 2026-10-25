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

    @property
    def predicted_label(self) -> str:
        """Human-readable predicted class."""
        return "malignant" if self.predicted_class == 0 else "benign"

    @property
    def risk_tier(self) -> str:
        """Describe the policy tier from the same thresholds used for routing."""
        if self.risk <= self.automatic_threshold:
            return "lower"
        if self.risk <= self.assisted_threshold:
            return "intermediate"
        return "higher"
