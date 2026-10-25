"""Rule-based checker for factual and safety properties of generated explanations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from raa.explain.record import DecisionRecord
from raa.explain.templates import DISCLAIMER


@dataclass(frozen=True)
class CheckResult:
    """Checker outcome with a stable list of detected problems."""

    passed: bool
    issues: tuple[str, ...]


_FORBIDDEN = re.compile(
    r"\b(confirmed diagnosis|guaranteed|certain diagnosis|clinically proven)\b",
    flags=re.IGNORECASE,
)


def check_explanation(record: DecisionRecord, text: str) -> CheckResult:
    """Check expected record values, uncertainty caveat, and non-clinical disclaimer."""
    issues: list[str] = []
    required = {
        "predicted class": f"predicted {record.predicted_label}",
        "decision level": f"routes this case to {record.level.value}",
        "risk tier": f"{record.risk_tier} tier",
        "risk score": f"risk is {record.risk:.3f}",
        "malignant probability": f"probability {record.malignant_probability:.3f}",
        "uncertainty caveat": "not a calibrated probability of error",
        "design-assumption caveat": "design assumptions",
        "prototype disclaimer": DISCLAIMER,
    }
    for name, phrase in required.items():
        if phrase.casefold() not in text.casefold():
            issues.append(f"missing_or_incorrect_{name.replace(' ', '_')}")
    if _FORBIDDEN.search(text):
        issues.append("overconfident_clinical_language")
    return CheckResult(passed=not issues, issues=tuple(issues))
