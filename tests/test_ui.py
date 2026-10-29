from pathlib import Path

from streamlit.testing.v1 import AppTest

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
    app.number_input[0].set_value(58)
    app.number_input[1].set_value(165)
    app.number_input[2].set_value(64)
    app.run()
    for widget, value in zip(
        app.selectbox[:8],
        ("Woman", "Yes", "No", "Yes", "No", "No", "No", "Yes"),
        strict=True,
    ):
        widget.set_value(value)
    app.run()
    for widget, value in zip(
        app.selectbox[8:],
        ("Irregular", "Spiculated (spiky edge)", "High"),
        strict=True,
    ):
        widget.set_value(value)
    app.run()
    app.button[0].click().run(timeout=90)
    return app


def test_landing_page_is_the_user_questionnaire_and_uses_requested_title():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    assert not app.exception
    assert [title.value for title in app.title] == ["Risk Aware Abstention System"]
    assert len(app.number_input) == 3
    assert len(app.selectbox) == 8
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


def test_no_mammogram_report_returns_human_review_without_class_estimate():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.number_input[0].set_value(42)
    app.number_input[1].set_value(170)
    app.number_input[2].set_value(72)
    app.run()
    for widget, value in zip(
        app.selectbox[:8],
        ("Woman", "Not sure", "No", "Yes", "No", "No", "No", "No"),
        strict=True,
    ):
        widget.set_value(value)
    app.button[0].click().run(timeout=90)
    assert not app.exception
    assert any("Human Review" in item.value for item in app.error)
    assert any("No class estimate was produced" in item.value for item in app.markdown)


def test_unknown_report_fields_are_estimated_but_forced_to_human_review():
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    app.number_input[0].set_value(58)
    app.number_input[1].set_value(165)
    app.number_input[2].set_value(64)
    app.run()
    for widget, value in zip(
        app.selectbox[:8],
        ("Woman", "Yes", "No", "No", "No", "No", "No", "Yes"),
        strict=True,
    ):
        widget.set_value(value)
    app.run()
    for widget in app.selectbox[8:]:
        widget.set_value("Not sure")
    app.run()
    app.button[0].click().run(timeout=90)
    assert not app.exception
    assert any("Human Review" in item.value for item in app.error)
    assert any("1 of 4 inputs measured" in item.value for item in app.info)
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
    assert not app.exception
    assert any(
        button.label == "Download prediction report" for button in app.get("download_button")
    )
    assert any("Your report is ready." in item.value for item in app.success)


def test_saved_model_responds_to_report_inputs_and_routes_missing_data_to_review():
    artifact = load_mammography_artifact()
    malignant_case = {"Age": 58, "Shape": 4, "Margin": 5, "Density": 1}
    benign_case = {"Age": 43, "Shape": 1, "Margin": 1, "Density": 3}
    malignant = predict_mammography_case(malignant_case, artifact)
    benign = predict_mammography_case(benign_case, artifact)
    incomplete = predict_mammography_case(
        {"Age": 58, "Shape": 4, "Margin": None, "Density": 1}, artifact
    )
    assert malignant.predicted_label == "malignant"
    assert benign.predicted_label == "benign"
    assert malignant.risk != benign.risk
    assert incomplete.level is DecisionLevel.HUMAN_REVIEW
    assert incomplete.estimated_feature_count == 1
    assert incomplete.predicted_label in {"malignant", "benign"}
