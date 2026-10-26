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
    r"(?<!not a )\bconfirmed diagnosis\b|\b(guaranteed|certain diagnosis|clinically proven|"
    r"this confirms cancer|you have cancer)\b",
    flags=re.IGNORECASE,
)


def check_explanation(record: DecisionRecord, text: str) -> CheckResult:
    """Check expected record values, uncertainty caveat, and non-clinical disclaimer."""
    issues: list[str] = []
    label = {
        "Automatic": "Automatic prediction",
        "Assisted": "Assisted decision",
        "Human Review": "Human review",
    }[record.level.value]
    required = {
        "decision level": f"Decision level: {label}",
        "predicted class": f"predicted class is {record.predicted_label}",
        "confidence": f"model confidence {record.confidence:.2f}",
        "uncertainty": f"Uncertainty U={record.uncertainty:.4f}",
        "anomaly score": f"anomaly score A={record.anomaly:.2f}",
        "risk score": f"risk score R={record.risk:.2f}",
        "automatic threshold": f"thresholds {record.automatic_threshold:.2f}",
        "assisted threshold": f"/ {record.assisted_threshold:.2f}",
        "limitation statement": "This output is a model estimate, not a confirmed diagnosis.",
        "prototype disclaimer": DISCLAIMER,
    }
    for name, phrase in required.items():
        if phrase.casefold() not in text.casefold():
            issues.append(f"missing_or_incorrect_{name.replace(' ', '_')}")
    if record.level.value == "Automatic":
        if "returned automatically" not in text.casefold():
            issues.append("automatic_policy_contradiction")
        if (
            "referred for human review" in text.casefold()
            or "additional verification" in text.casefold()
        ):
            issues.append("automatic_policy_contradiction")
    else:
        if not record.referral_reason or record.referral_reason.casefold() not in text.casefold():
            issues.append("missing_or_incorrect_referral_reason")
        if record.level.value == "Assisted" and (
            "additional verification is advised" not in text.casefold()
        ):
            issues.append("assisted_policy_contradiction")
        if record.level.value == "Human Review" and (
            "referred for human review" not in text.casefold()
        ):
            issues.append("human_review_policy_contradiction")
    if _FORBIDDEN.search(text):
        issues.append("overconfident_clinical_language")
    return CheckResult(passed=not issues, issues=tuple(issues))
