import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from raa.app.copy import REPORT_HAS_MASS
from raa.mammography import DEFAULT_ARTIFACT_DIR


def test_prediction_page_displays_saved_model_metrics():
    metrics_path = DEFAULT_ARTIFACT_DIR / "metrics.json"
    source = json.loads(metrics_path.read_text(encoding="utf-8"))
    app_path = Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=90).run()
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

    assert not app.exception
    assert any("About this model" in item.label for item in app.expander)
    rendered = " ".join(item.value for item in app.markdown)
    assert f"{source['test']['accuracy']:.1%}" in rendered
    assert f"{source['test']['sensitivity_malignant']:.1%}" in rendered
    assert f"{source['test']['specificity_benign']:.1%}" in rendered
