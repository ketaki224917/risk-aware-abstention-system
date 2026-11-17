"""Tests for decoupled class vs route explanations, stability, and fidelity."""

from __future__ import annotations

from raa.app.copy import MARGIN_CHOICES, SHAPE_CHOICES
from raa.explain.separate_explanations import (
    ClassExplanation,
    DualExplanation,
    ExplanationDiagnostics,
    RouteExplanation,
)
from raa.mammography import (
    explain_mammography_case_dual,
    load_mammography_artifact,
    predict_mammography_case,
)


def test_dual_explanation_generation_and_diagnostics():
    artifact = load_mammography_artifact()
    values = {
        "Age": 62,
        "Shape": SHAPE_CHOICES["Irregular (uneven)"],
        "Margin": MARGIN_CHOICES["Spiky edge (spiculated)"],
        "Density": 2,
    }
    record = predict_mammography_case(values, artifact)
    dual = explain_mammography_case_dual(values, record, artifact)

    assert isinstance(dual, DualExplanation)
    assert isinstance(dual.class_explanation, ClassExplanation)
    assert isinstance(dual.route_explanation, RouteExplanation)
    assert isinstance(dual.diagnostics, ExplanationDiagnostics)

    # Class explanation checks
    assert dual.class_explanation.predicted_label in ("Benign", "Malignant")
    assert 0.0 <= dual.class_explanation.malignant_probability <= 1.0
    assert len(dual.class_explanation.feature_attributions) == 4
    top_feature = dual.class_explanation.feature_attributions[0]
    assert top_feature.attribution_score >= 0.0
    assert top_feature.directional_push in (
        "toward malignant",
        "toward benign",
        "neutral (imputed)",
    )
    assert len(top_feature.summary_text) > 0

    # Route explanation checks
    assert dual.route_explanation.route_tier == record.level.value
    assert len(dual.route_explanation.risk_components) == 3
    names = [c.component_name for c in dual.route_explanation.risk_components]
    assert any("Disagreement" in n for n in names)
    assert any("Unusualness" in n for n in names)
    assert any("Consequence" in n for n in names)
    assert dual.route_explanation.composite_risk == record.risk

    # Diagnostics checks
    assert dual.diagnostics.stability_score >= 0.5
    assert dual.diagnostics.fidelity_ratio >= 1.0
    assert "Spearman rank correlation" in dual.diagnostics.stability_note
    assert "fidelity ratio" in dual.diagnostics.fidelity_note.lower()


def test_missing_data_route_explanation_override():
    artifact = load_mammography_artifact()
    values = {
        "Age": 55,
        "Shape": None,  # Not sure / missing
        "Margin": MARGIN_CHOICES["Spiky edge (spiculated)"],
        "Density": 2,
    }
    record = predict_mammography_case(values, artifact)
    dual = explain_mammography_case_dual(values, record, artifact)

    assert dual.route_explanation.missing_data_override is True
    assert dual.route_explanation.route_tier == "Human Review"
    assert "FORCED ESCALATION" in dual.route_explanation.summary_narrative
