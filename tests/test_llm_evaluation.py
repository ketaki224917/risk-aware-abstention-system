"""Tests for LLM report evaluation, hallucination checks, and diagnostic language gates."""

from __future__ import annotations

import json
from pathlib import Path

from raa.explain.llm_evaluation import (
    LLMReportEvaluationSummary,
    evaluate_report_text,
    run_llm_report_evaluation,
    save_llm_report_evaluation,
)


def test_clean_deterministic_report_passes_all_checks():
    facts = {
        "model_output": "Benign",
        "route": "Automatic",
        "risk_score": "0.190",
        "report_status": "Describes a mass",
    }
    clean_text = (
        "The model output is Benign and the route is Automatic. "
        "The software assessed age, mass shape, edge, and density."
    )
    result = evaluate_report_text(facts, clean_text)
    assert result.overall_passed is True
    assert result.prediction_matches is True
    assert result.route_matches is True
    assert result.hallucination_detected is False
    assert result.prohibited_language_detected is False
    assert len(result.failure_reasons) == 0


def test_contradicted_prediction_is_intercepted():
    facts = {"model_output": "Benign", "route": "Automatic"}
    bad_text = "The model predicted is Malignant and the route is Automatic."
    result = evaluate_report_text(facts, bad_text)
    assert result.overall_passed is False
    assert result.prediction_matches is False
    assert any("Prediction mismatch" in r or "contradiction" in r for r in result.failure_reasons)


def test_hallucination_triggers_are_intercepted():
    facts = {"model_output": "Malignant", "route": "Assisted"}
    hallucinated_text = (
        "The model output is Malignant and the route is Assisted. "
        "Stage IV metastasis was detected in the lymph node with BRCA gene mutation."
    )
    result = evaluate_report_text(facts, hallucinated_text)
    assert result.overall_passed is False
    assert result.hallucination_detected is True
    assert "lymph node" in result.hallucinated_phrases
    assert "metastasis" in result.hallucinated_phrases
    assert "brca" in result.hallucinated_phrases


def test_prohibited_clinical_language_is_intercepted():
    facts = {"model_output": "Malignant", "route": "Human Review"}
    prohibited_text = (
        "The model output is Malignant and the route is Human Review. "
        "You have confirmed cancer; we recommend immediate treatment and you must consult a doctor."
    )
    result = evaluate_report_text(facts, prohibited_text)
    assert result.overall_passed is False
    assert result.prohibited_language_detected is True
    assert "you have" in result.prohibited_phrases
    assert "confirmed cancer" in result.prohibited_phrases
    assert "treatment" in result.prohibited_phrases


def test_run_and_save_llm_report_evaluation(tmp_path: Path):
    summary = run_llm_report_evaluation()
    assert isinstance(summary, LLMReportEvaluationSummary)
    assert summary.total_cases_evaluated == 6
    assert summary.overall_pass_rate == 1.0
    assert "ARCHITECTURAL ISOLATION" in summary.architectural_isolation_claim

    out_file = save_llm_report_evaluation(output_dir=tmp_path)
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["total_cases_evaluated"] == 6
    assert data["overall_pass_rate"] == 1.0
