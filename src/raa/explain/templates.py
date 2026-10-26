"""Deterministic explanations grounded in an immutable decision record."""

from __future__ import annotations

from raa.explain.record import DecisionRecord

DISCLAIMER = "Research prototype only; not clinically validated and not for real diagnosis."


def generate_explanation(record: DecisionRecord) -> str:
    """Render a factual explanation; this function cannot change model decisions."""
    label = {
        "Automatic": "Automatic prediction",
        "Assisted": "Assisted decision",
        "Human Review": "Human review",
    }[record.level.value]
    common = (
        f"Decision level: {label}. The classifier's predicted class is "
        f"{record.predicted_label} (model confidence {record.confidence:.2f}). "
        f"Uncertainty U={record.uncertainty:.4f}; anomaly score A={record.anomaly:.2f}; "
        f"risk score R={record.risk:.2f} (thresholds "
        f"{record.automatic_threshold:.2f} / {record.assisted_threshold:.2f}). "
    )
    if record.level.value == "Automatic":
        decision_text = (
            "The risk score is below the first threshold, so the prediction is "
            "returned automatically."
        )
    elif record.level.value == "Assisted":
        decision_text = (
            f"Additional verification is advised because {record.referral_reason} is high."
        )
    else:
        decision_text = (
            f"The case is referred for human review because {record.referral_reason} is high."
        )
    return (
        common
        + decision_text
        + " This output is a model estimate, not a confirmed diagnosis. "
        + DISCLAIMER
    )
