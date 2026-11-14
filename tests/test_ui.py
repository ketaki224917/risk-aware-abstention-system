from pathlib import Path

from streamlit.testing.v1 import AppTest

from raa.app.copy import (
    MARGIN_CHOICES,
    REPORT_HAS_MASS,
    REPORT_NO_MASS,
    REPORT_UNAVAILABLE,
    SHAPE_CHOICES,
    UNKNOWN_REPORT_VALUE,
)
from raa.explain.llm_adapter import LocalReportNarrative
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    load_mammography_artifact,
    predict_mammography_case,
)
from raa.risk.policy import DecisionLevel


def _app_path() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"


def _completed_report_case() -> AppTest:
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.selectbox[0].set_value(REPORT_HAS_MASS)
    app.run()
    app.number_input[0].set_value(58)
    app.run()
    for widget, value in zip(
        app.selectbox[1:],
        ("Irregular (uneven)", "Spiky edge (spiculated)", "High"),
        strict=True,
    ):
        widget.set_value(value)
    app.run()
    app.button[0].click().run(timeout=90)
    return app


def test_landing_page_asks_only_model_relevant_report_questions():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    assert not app.exception
    assert [title.value for title in app.title] == ["Risk Aware Abstention System"]
    assert len(app.number_input) == 0
    assert len(app.selectbox) == 1
    assert not app.sidebar.radio
    rendered = " ".join(
        [item.value for item in app.title]
        + [item.value for item in app.header]
        + [item.value for item in app.subheader]
        + [item.value for item in app.caption]
        + [item.value for item in app.markdown]
    )
    assert "Research prototype" not in rendered
    assert "Example cases" not in rendered
    assert "symptoms" not in rendered.lower()

    app.selectbox[0].set_value(REPORT_HAS_MASS)
    app.run()
    assert len(app.number_input) == 1
    assert len(app.selectbox) == 4


def test_complete_mammogram_report_runs_model_and_explains_prediction():
    result_dir = DEFAULT_ARTIFACT_DIR
    before = {item.name: item.stat().st_size for item in result_dir.iterdir()}
    app = _completed_report_case()
    after = {item.name: item.stat().st_size for item in result_dir.iterdir()}
    assert after == before
    assert not app.exception
    assert any("model leans malignant" in item.value for item in app.success)
    assert any(item.value == "Why the model leaned this way" for item in app.subheader)
    assert any("moved the malignant-class score" in item.value for item in app.markdown)
    assert any(item.label == "Generate prediction report" for item in app.button)
    assert not app.get("download_button")


def test_no_compatible_report_returns_human_review_without_class_estimate():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.selectbox[0].set_value(REPORT_UNAVAILABLE)
    app.button[0].click().run(timeout=90)
    assert not app.exception
    assert any("Human Review" in item.value for item in app.error)
    assert any(
        "No benign/malignant class estimate was produced" in item.value for item in app.markdown
    )


def test_report_with_no_mass_returns_human_review_without_class_estimate():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.selectbox[0].set_value(REPORT_NO_MASS)
    app.button[0].click().run(timeout=90)
    assert not app.exception
    assert any("Human Review" in item.value for item in app.error)
    assert any("did not describe a mass" in item.value for item in app.caption)


def test_unknown_report_fields_are_imputed_but_forced_to_human_review():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.selectbox[0].set_value(REPORT_HAS_MASS)
    app.run()
    app.number_input[0].set_value(58)
    app.run()
    for widget in app.selectbox[1:]:
        widget.set_value(UNKNOWN_REPORT_VALUE)
    app.run()
    app.button[0].click().run(timeout=90)
    assert not app.exception
    assert any("Human Review" in item.value for item in app.error)
    assert any("1 of 4 model inputs measured" in item.value for item in app.info)
    assert any("incomplete findings require Human Review" in item.value for item in app.warning)


def test_report_is_only_generated_after_button_and_download_contains_prediction(monkeypatch):
    calls = []

    def fake_report_writer(facts):
        calls.append(facts)
        return LocalReportNarrative(
            f"The model output is {facts['model_output']} and the route is {facts['route']}."
        )

    monkeypatch.setattr("raa.app.health_intake.generate_prediction_narrative", fake_report_writer)
    app = _completed_report_case()
    assert calls == []
    assert not app.get("download_button")
    report_button = next(
        button for button in app.button if button.label == "Generate prediction report"
    )
    report_button.click().run()
    assert len(calls) == 1
    assert calls[0]["report_findings"]["shape"] == "Irregular (uneven)"
    assert not app.exception
    assert any(button.label == "Download Word report" for button in app.get("download_button"))
    assert any("Your report is ready." in item.value for item in app.success)


def test_every_model_question_changes_a_real_inference_signal():
    artifact = load_mammography_artifact()
    base = {"Age": 46, "Shape": 1, "Margin": 1, "Density": 3}
    baseline = predict_mammography_case(base, artifact)
    alternatives = (
        ("Age", 60),
        ("Shape", SHAPE_CHOICES["Irregular (uneven)"]),
        ("Margin", MARGIN_CHOICES["Spiky edge (spiculated)"]),
        ("Density", 1),
    )
    for feature, value in alternatives:
        changed = predict_mammography_case({**base, feature: value}, artifact)
        assert (
            changed.malignant_probability != baseline.malignant_probability
            or changed.risk != baseline.risk
            or changed.level is not baseline.level
        )


def test_saved_model_covers_all_three_real_raa_routes():
    artifact = load_mammography_artifact()
    examples = (
        (
            {"Age": 46, "Shape": 1, "Margin": 1, "Density": 3},
            DecisionLevel.AUTOMATIC,
            "benign",
        ),
        (
            {"Age": 55, "Shape": 4, "Margin": 3, "Density": 3},
            DecisionLevel.ASSISTED,
            "malignant",
        ),
        (
            {"Age": 65, "Shape": 3, "Margin": 3, "Density": 3},
            DecisionLevel.HUMAN_REVIEW,
            "malignant",
        ),
    )
    for values, expected_level, expected_lean in examples:
        record = predict_mammography_case(values, artifact)
        assert record.level is expected_level
        assert record.predicted_label == expected_lean
