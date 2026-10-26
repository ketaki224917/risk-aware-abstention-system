"""Deterministic explanation faults for checker evaluation."""

from __future__ import annotations

import re
from enum import StrEnum

from raa.explain.record import DecisionRecord


class FaultType(StrEnum):
    """Supported injected explanation faults."""

    WRONG_LEVEL = "wrong_decision_level"
    WRONG_CLASS = "wrong_predicted_class"
    ALTERED_VALUE = "altered_numeric_value"
    UNSUPPORTED_CLAIM = "unsupported_diagnostic_claim"
    DROPPED_REASON = "dropped_referral_reason"
    POLICY_CONTRADICTION = "policy_contradiction"


def inject_fault(text: str, record: DecisionRecord, fault: FaultType) -> str:
    """Return an explanation with one targeted fault injected."""
    if fault is FaultType.WRONG_LEVEL:
        labels = {
            "Automatic": "Automatic prediction",
            "Assisted": "Assisted decision",
            "Human Review": "Human review",
        }
        replacement = "Assisted decision" if record.level.value != "Assisted" else "Human review"
        return text.replace(
            f"Decision level: {labels[record.level.value]}",
            f"Decision level: {replacement}",
            1,
        )
    if fault is FaultType.WRONG_CLASS:
        wrong = "benign" if record.predicted_class == 0 else "malignant"
        return text.replace(
            f"predicted class is {record.predicted_label}",
            f"predicted class is {wrong}",
            1,
        )
    if fault is FaultType.ALTERED_VALUE:
        return text.replace(
            f"risk score R={record.risk:.2f}",
            f"risk score R={record.risk + 0.13:.2f}",
            1,
        )
    if fault is FaultType.UNSUPPORTED_CLAIM:
        return f"{text} This confirms cancer."
    if fault is FaultType.DROPPED_REASON:
        return re.sub(r"because .*? is high\.", "", text, count=1)
    if fault is FaultType.POLICY_CONTRADICTION:
        return text.replace("returned automatically", "referred for human review", 1)
    raise ValueError(f"Unsupported fault type: {fault}")
