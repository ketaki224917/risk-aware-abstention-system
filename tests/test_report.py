import json
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

from raa.app.copy import MARGIN_CHOICES, REPORT_HAS_MASS, SHAPE_CHOICES
from raa.app.docx_report import build_prediction_report_docx
from raa.app.report import build_prediction_report
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    load_mammography_artifact,
    predict_mammography_case,
)


def test_prediction_report_contains_model_result_and_only_relevant_inputs():
    artifact = load_mammography_artifact()
    answers = {
        "report_status": REPORT_HAS_MASS,
        "age": 58,
        "shape": "Irregular (uneven)",
        "margin": "Spiky edge (spiculated)",
        "density": "High",
    }
    values = {
        "Age": 58,
        "Shape": SHAPE_CHOICES[answers["shape"]],
        "Margin": MARGIN_CHOICES[answers["margin"]],
        "Density": 1,
    }
    record = predict_mammography_case(values, artifact)
    metrics = json.loads((DEFAULT_ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))
    report = build_prediction_report(
        answers=answers,
        record=record,
        explanations=("Mass edge moved the score toward malignant.",),
        narrative="The model output is Malignant and the route is Automatic.",
        evaluation=metrics,
    )
    assert report.startswith("RISK AWARE ABSTENTION SYSTEM - PREDICTION REPORT")
    assert "Model output: Malignant" in report
    assert f"Risk-aware route: {record.level.value}" in report
    assert "Age at mammogram: 58" in report
    assert "Mass shape: Irregular (uneven)" in report
    assert "Mass edge: Spiky edge (spiculated)" in report
    assert "Mass density: High" in report
    assert "Height (cm)" not in report
    assert "Symptoms:" not in report
    assert "This is not a diagnosis." in report
    docx = build_prediction_report_docx(report)
    with ZipFile(BytesIO(docx)) as archive:
        assert archive.testzip() is None
        document_xml = archive.read("word/document.xml")
        assert document_xml.count(b"<w:tblHeader/>") == 3
        document = ElementTree.fromstring(document_xml)
    word_text = " ".join(
        element.text or ""
        for element in document.iter(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        )
    )
    assert "Risk Aware Abstention System" in word_text
    assert "Prediction report" in word_text
    assert "Model output" in word_text and "Malignant" in word_text
    assert "Age at mammogram" in word_text
    assert "Height (cm)" not in word_text
