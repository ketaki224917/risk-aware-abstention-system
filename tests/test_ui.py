import csv
import io
from pathlib import Path

from streamlit.testing.v1 import AppTest

from raa.data import load_breast_cancer_data


def _app_path() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"


def test_mode_a_landing_banner_and_one_click_case():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    assert not app.exception
    assert any("Research prototype. Not a medical device." in item.value for item in app.error)
    assert len(app.button) >= 6
    app.button[0].click().run()
    assert not app.exception
    messages = list(app.warning) + list(app.success) + list(app.error)
    assert any("model leans" in element.value for element in messages)


def test_guided_mode_has_six_inputs_and_returns_estimated_profile():
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Guided entry").run()
    assert not app.exception
    assert len(app.slider) == 6
    assert len(app.number_input) == 6
    assert any("6 of 30 measured, 24 estimated" in item.value for item in app.markdown)
    app.button[0].click().run()
    assert not app.exception
    assert any("6 of 30 measured" in item.value for item in app.caption)
    assert any("24 estimated" in item.value for item in app.caption)


def test_upload_csv_mode_renders_batch_results():
    data = load_breast_cancer_data()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(data.feature_names)
    writer.writerow(data.features[0].tolist())
    app = AppTest.from_file(str(_app_path()), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Upload CSV").run()
    app.text_area[0].set_value(output.getvalue()).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert len(app.table) == 1
    assert len(app.metric) == 3


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
