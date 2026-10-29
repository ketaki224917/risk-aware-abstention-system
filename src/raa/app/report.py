"""Prediction report content assembled in memory after an explicit user request."""

from __future__ import annotations

from datetime import datetime

from raa.explain.record import DecisionRecord

DATASET_SOURCE = "UCI Mammographic Mass, DOI 10.24432/C53K6Z"


def build_prediction_report(
    *,
    answers: dict[str, object],
    record: DecisionRecord | None,
    explanations: tuple[str, ...],
    narrative: str,
    evaluation: dict[str, object],
    generated_at: datetime | None = None,
) -> str:
    """Return a report string; no file is created or written by this function."""
    timestamp = (generated_at or datetime.now().astimezone()).astimezone()
    route = record.level.value if record is not None else "Human Review"
    model_output = record.predicted_label.title() if record is not None else "No class estimate"
    lines = [
        "RISK AWARE ABSTENTION SYSTEM - PREDICTION REPORT",
        f"Generated locally: {timestamp:%Y-%m-%d %H:%M %Z}",
        "",
        "RESULT",
        f"Model output: {model_output}",
        f"Risk-aware route: {route}",
    ]
    if record is not None:
        lines.extend(
            [
                f"Malignant-class model score (not calibrated): {record.malignant_probability:.3f}",
                f"Combined risk score: {record.risk:.3f}",
                f"Routing thresholds: Automatic <= {record.automatic_threshold:.3f}; "
                f"Assisted <= {record.assisted_threshold:.3f}; otherwise Human Review",
            ]
        )
    lines.extend(
        [
            "",
            "REPORT SUMMARY",
            narrative,
            "",
            "WHY THE MODEL LEANED THIS WAY",
            *(
                [f"- {text}" for text in explanations]
                if explanations
                else [
                    "No model explanation was generated because no mammogram report was supplied."
                ]
            ),
            "",
            "INPUTS",
            f"Age at mammogram: {answers.get('age')}",
            f"Height (cm): {answers.get('height_cm')}",
            f"Weight (kg): {answers.get('weight_kg')}",
            f"Gender: {answers.get('gender')}",
            f"Mass shape: {answers.get('shape') or 'Not supplied'}",
            f"Mass edge: {answers.get('margin') or 'Not supplied'}",
            f"Mass density: {answers.get('density') or 'Not supplied'}",
            f"Family history: {answers.get('family_history')}",
            f"Previous breast condition, biopsy, or treatment: {answers.get('medical_history')}",
            "Symptoms:",
        ]
    )
    symptom_names = {
        "symptom_lump": "New lump",
        "symptom_swelling": "Breast swelling",
        "symptom_skin_changes": "Skin changes",
        "symptom_nipple_changes": "Nipple changes",
    }
    lines.extend(f"- {label}: {answers.get(key)}" for key, label in symptom_names.items())
    test = evaluation.get("test", {})
    if isinstance(test, dict):
        automatic_false_negatives = int(test.get("malignant_false_negatives", 0)) - int(
            test.get("malignant_false_negatives_routed_away", 0)
        )
        lines.extend(
            [
                "",
                "HELD-OUT DATASET CHECK",
                f"Accuracy: {float(test.get('accuracy', 0)):.1%}",
                f"Malignant sensitivity: {float(test.get('sensitivity_malignant', 0)):.1%}",
                f"Benign specificity: {float(test.get('specificity_benign', 0)):.1%}",
                f"Automatic-tier error rate: {float(test.get('automatic_error_rate', 0)):.1%}",
                f"Malignant false negatives in Automatic: "
                f"{automatic_false_negatives} / "
                f"{int(test.get('malignant_false_negatives', 0))}",
            ]
        )
    lines.extend(
        [
            "",
            "LIMITS",
            "The model estimates the benign/malignant severity label of a mammographic mass "
            "from age, shape, edge, and density. Symptoms and history are included for context "
            "and do not change the model score. This is not a diagnosis. The source dataset is "
            "small, older, and from one collection.",
            f"Dataset source: {DATASET_SOURCE}",
            "Answers are not saved by the app. This report exists only in memory for download.",
        ]
    )
    return "\n".join(lines)
