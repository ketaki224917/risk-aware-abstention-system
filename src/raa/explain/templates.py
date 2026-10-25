"""Deterministic explanations grounded in an immutable decision record."""

from __future__ import annotations

from raa.explain.record import DecisionRecord

DISCLAIMER = "Research prototype only; not clinically validated and not for real diagnosis."


def generate_explanation(record: DecisionRecord) -> str:
    """Render a factual explanation; this function cannot change model decisions."""
    return (
        f"The model predicted {record.predicted_label} with malignant probability "
        f"{record.malignant_probability:.3f}. The normalized uncertainty signal is "
        f"{record.uncertainty:.3f}, the anomaly score is {record.anomaly:.3f}, and the "
        f"design-assumption consequence value is {record.consequence:.3f}. The combined "
        f"risk is {record.risk:.3f} ({record.risk_tier} tier), so the policy routes this "
        f"case to {record.level.value}. Ensemble disagreement is a signal, not a calibrated "
        f"probability of error; risk weights and consequence values are design assumptions. "
        f"{DISCLAIMER}"
    )
