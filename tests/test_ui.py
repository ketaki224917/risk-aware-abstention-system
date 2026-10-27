from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_mode_a_landing_banner_and_one_click_case():
    app_path = Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=45).run()

    assert not app.exception
    assert any("Research prototype. Not a medical device." in item.value for item in app.error)
    assert len(app.button) >= 6
    app.button[0].click().run()
    assert not app.exception
    messages = list(app.warning) + list(app.success) + list(app.error)
    assert any("model leans" in element.value for element in messages)
