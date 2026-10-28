"""In-memory text report for the breast-health questionnaire."""

from __future__ import annotations

from datetime import datetime


def build_intake_report(
    answers: dict[str, str],
    *,
    explanation: str,
    explanation_source: str,
    generated_at: datetime | None = None,
) -> str:
    """Build a user-downloadable report; this function does not write a file."""
    timestamp = (generated_at or datetime.now().astimezone()).astimezone()
    basic_fields = (
        ("Age (years)", "age"),
        ("Height (cm)", "height_cm"),
        ("Weight (kg)", "weight_kg"),
        ("Gender", "gender"),
        ("Breast/family history", "history"),
    )
    symptom_fields = (
        ("Lump", "symptom_lump"),
        ("Breast swelling", "symptom_swelling"),
        ("Skin changes", "symptom_skin_changes"),
        ("Nipple changes", "symptom_nipple_changes"),
    )
    basic_lines = [f"{label}: {answers[key]}" for label, key in basic_fields]
    symptom_lines = [f"{label}: {answers[key]}" for label, key in symptom_fields]
    return "\n".join(
        [
            "RISK-AWARE ABSTENTION - INTAKE RESULT REPORT",
            f"Generated locally: {timestamp:%Y-%m-%d %H:%M %Z}",
            "",
            "SYSTEM RESULT",
            "Human Review - no prediction made",
            "Predicted class: None",
            "",
            "BASIC DETAILS",
            *basic_lines,
            "",
            "SYMPTOM ANSWERS",
            *symptom_lines,
            "",
            "EXPLANATION",
            explanation,
            f"Explanation source: {explanation_source}",
            "",
            "IMPORTANT LIMIT",
            (
                "The current classifier was trained on numeric cell-nucleus measurements and "
                "was not trained or validated to use these questionnaire answers. Human Review "
                "here means the prototype could not assess this input. It is not a diagnosis, "
                "clinical assessment, or referral."
            ),
            "",
            (
                "The local LLM received only fixed status text, not the answers above. The app "
                "does not save this report; it is created only when you download it."
            ),
            "",
            "Research prototype. Not a medical device. Not for diagnosis.",
        ]
    )
