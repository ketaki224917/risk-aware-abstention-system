import csv
import io
from pathlib import Path

from streamlit.testing.v1 import AppTest

from raa.data import load_breast_cancer_data


def _app_path() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"


def test_examples_are_optional_and_one_click_case_works():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Example cases").run()
    assert not app.exception
    assert any("Research prototype. Not a medical device." in item.value for item in app.warning)
    assert len(app.button) >= 6
    app.button[0].click().run()
    assert not app.exception
    messages = list(app.warning) + list(app.success) + list(app.error)
    assert any("model leans" in element.value for element in messages)
    assert any("Automatic:" in element.value for element in messages)
    assert any("Rule-based checker passed" in element.value for element in app.success)
    assert any("aria-label='Risk gauge" in element.value for element in app.markdown)


def test_intake_collects_basic_details_and_four_symptoms_but_returns_human_review():
    results_dir = Path(__file__).resolve().parents[1] / "results" / "demo"
    before = {item.name: item.stat().st_size for item in results_dir.iterdir()}
    app = AppTest.from_file(str(_app_path()), default_timeout=90).run()
    assert not app.exception
    assert app.sidebar.radio[0].value == "Breast health questionnaire"
    assert len(app.number_input) == 3
    assert len(app.selectbox) == 6
    assert all(widget.value is None for widget in app.number_input)
    assert all(widget.value is None for widget in app.selectbox)
    assert any("cannot use these answers to predict cancer" in item.value for item in app.info)
    app.button[0].click().run()
    assert any("complete the five basic fields" in item.value.lower() for item in app.error)
    assert not any("Human Review" in item.value for item in app.error)

    app.number_input[0].set_value(42).run()
    app.number_input[1].set_value(165).run()
    app.number_input[2].set_value(65.2).run()
    app.selectbox[0].set_value("Woman").run()
    app.selectbox[1].set_value("Not sure").run()
    app.selectbox[2].set_value("Yes").run()
    app.selectbox[3].set_value("No").run()
    app.selectbox[4].set_value("Not sure").run()
    app.selectbox[5].set_value("No").run()
    app.button[0].click().run(timeout=90)

    assert not app.exception
    assert any(
        "Human Review" in item.value and "no prediction made" in item.value.lower()
        for item in app.error
    )
    assert any("not been trained or validated" in item.value for item in app.info)
    assert any("not a medical assessment" in item.value for item in app.caption)
    assert any("LLM explanation" in item.value for item in app.subheader)
    assert len(app.get("download_button")) == 1
    messages = list(app.warning) + list(app.success)
    assert not any("the model leans" in item.value for item in messages)
    after = {item.name: item.stat().st_size for item in results_dir.iterdir()}
    assert after == before


def test_guided_entry_uses_slider_and_typed_values_for_real_inference():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Guided entry").run()
    data = load_breast_cancer_data()
    values_by_feature = dict(zip(data.feature_names, data.features[0].tolist(), strict=True))

    slider_feature = app.slider[0].label.removesuffix(" slider").lower()
    slider_value = float(values_by_feature[slider_feature])
    app.slider[0].set_value(slider_value).run()
    assert app.number_input[0].value == slider_value

    for index in range(1, 6):
        feature = app.number_input[index].label.removesuffix(" exact value").lower()
        app.number_input[index].set_value(float(values_by_feature[feature]))
    app.run()

    assert not app.exception
    assert all(widget.value is not None for widget in app.number_input)
    assert any("6 of 30 measured, 24 estimated" in item.value for item in app.markdown)
    app.button[0].click().run()
    assert not app.exception
    assert any("6 of 30 measured" in item.value for item in app.caption)
    assert any("24 estimated" in item.value for item in app.caption)
    assert any("model leans" in item.value for item in list(app.warning) + list(app.success))


def test_upload_csv_mode_renders_batch_results():
    data = load_breast_cancer_data()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(data.feature_names)
    writer.writerow(data.features[0].tolist())
    results_dir = Path(__file__).resolve().parents[1] / "results" / "demo"
    before = {item.name: item.stat().st_size for item in results_dir.iterdir()}
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Upload CSV").run()
    app.text_area[0].set_value(output.getvalue()).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert len(app.table) == 1
    assert len(app.metric) == 3
    after = {item.name: item.stat().st_size for item in results_dir.iterdir()}
    assert after == before


def test_what_if_page_has_four_live_sliders_capacity_and_synthetic_button():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("What-if").run()
    assert not app.exception
    assert len(app.slider) == 5
    assert any("How many of 100 cases" in slider.label for slider in app.slider)
    assert any("Default 30/100 maps to p70/p90" in item.value for item in app.caption)
    app.slider[-1].set_value(20).run()
    assert any("Automatic p80.0" in item.value for item in app.caption)
    previous_risk = app.progress[-1].proto.text
    slider = app.slider[0]
    slider.set_value(slider.value * 0.9).run()
    assert app.progress[-1].proto.text != previous_risk
    app.button[0].click().run()
    assert not app.exception
    assert any("Synthetic what-if profile" in item.value for item in app.info)
    assert any("Synthetic shifted fields" in item.value for item in app.caption)


def test_banner_and_navigation_smoke_for_all_six_modes():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    for mode in (
        "Breast health questionnaire",
        "Guided entry",
        "Upload CSV",
        "What-if",
        "Example cases",
        "Why abstain?",
    ):
        app.sidebar.radio[0].set_value(mode).run()
        assert not app.exception
        assert any(
            "Research prototype. Not a medical device. Not for diagnosis." in item.value
            for item in app.warning
        )
