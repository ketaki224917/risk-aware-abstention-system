import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from raa.app.demo_assets import DEFAULT_RUN_DIR, load_paper_results


def test_why_abstain_page_displays_canonical_results_file_values():
    metrics_path = DEFAULT_RUN_DIR / "metrics.json"
    with metrics_path.open("r", encoding="utf-8") as stream:
        source = json.load(stream)
    parsed = load_paper_results()
    assert parsed == source

    app_path = Path(__file__).resolve().parents[1] / "src" / "raa" / "app" / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Why abstain?").run()

    assert not app.exception
    assert any(source["run_id"] in item.value for item in app.caption)
    assert len(app.metric) == 4
    assert app.metric[0].value == f"{source['pooled_case_metrics']['error_rate']:.2%}"
    assert app.metric[1].value == f"{source['pooled_case_metrics']['automatic_coverage']:.2%}"
