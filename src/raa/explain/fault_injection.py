"""Deterministic explanation faults for checker evaluation."""

from __future__ import annotations

import re
from enum import StrEnum

from raa.explain.record import DecisionRecord


class FaultType(StrEnum):
    """Supported injected explanation faults."""

    WRONG_CLASS = "wrong_predicted_class"
    WRONG_LEVEL = "wrong_decision_level"
    WRONG_RISK_TIER = "wrong_risk_tier"
    FABRICATED_SCORE = "fabricated_score"
    OVERCONFIDENT = "overconfident_language"
    MISSING_CAVEAT = "missing_caveat"


def inject_fault(text: str, record: DecisionRecord, fault: FaultType) -> str:
    """Return an explanation with one targeted fault injected."""
    if fault is FaultType.WRONG_CLASS:
        wrong = "benign" if record.predicted_class == 0 else "malignant"
        return text.replace(f"predicted {record.predicted_label}", f"predicted {wrong}", 1)
    if fault is FaultType.WRONG_LEVEL:
        wrong = "Human Review" if record.level.value != "Human Review" else "Automatic"
        return text.replace(
            f"routes this case to {record.level.value}", f"routes this case to {wrong}", 1
        )
    if fault is FaultType.WRONG_RISK_TIER:
        wrong = "higher" if record.risk_tier != "higher" else "lower"
        return text.replace(f"{record.risk_tier} tier", f"{wrong} tier", 1)
    if fault is FaultType.FABRICATED_SCORE:
        fake = record.risk + 0.123
        return text.replace(f"risk is {record.risk:.3f}", f"risk is {fake:.3f}", 1)
    if fault is FaultType.OVERCONFIDENT:
        return f"{text} This is a confirmed diagnosis."
    if fault is FaultType.MISSING_CAVEAT:
        return re.sub(
            r"Ensemble disagreement is a signal, not a calibrated probability of error; "
            r"risk weights and consequence values are design assumptions\.\s*",
            "",
            text,
            count=1,
        )
    raise ValueError(f"Unsupported fault type: {fault}")
