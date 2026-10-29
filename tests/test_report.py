import json

from raa.app.report import build_prediction_report
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    load_mammography_artifact,
    predict_mammography_case,
)


def test_prediction_report_contains_model_result_context_and_results_metrics():
    artifact = load_mammography_artifact()
    answers = {
        "age": 58,
        "height_cm": 165,
        "weight_kg": 64,
        "gender": "Woman",
        "shape": "Irregular",
        "margin": "Spiculated (spiky edge)",
        "density": "High",
        "family_history": "Yes",
        "medical_history": "No",
        "symptom_lump": "Yes",
        "symptom_swelling": "No",
        "symptom_skin_changes": "No",
        "symptom_nipple_changes": "Not sure",
    }
    values = {"Age": 58, "Shape": 4, "Margin": 5, "Density": 1}
    record = predict_mammography_case(values, artifact)
    metrics = json.loads((DEFAULT_ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))
    report = build_prediction_report(
        answers=answers,
        record=record,
        explanations=("Margin pushed the score toward malignant.",),
        narrative="The model output is Malignant and the route is Automatic.",
        evaluation=metrics,
    )
    assert report.startswith("RISK AWARE ABSTENTION SYSTEM - PREDICTION REPORT")
    assert "Model output: Malignant" in report
    assert f"Risk-aware route: {record.level.value}" in report
    assert "Height (cm): 165" in report
    assert "Weight (kg): 64" in report
    assert "Gender: Woman" in report
    assert "New lump: Yes" in report
    assert "Nipple changes: Not sure" in report
    assert f"Malignant sensitivity: {metrics['test']['sensitivity_malignant']:.1%}" in report
    assert "This is not a diagnosis." in report
