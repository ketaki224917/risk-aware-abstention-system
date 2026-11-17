"""Tests for subgroup fairness audit, Wilson score intervals, and fairness gap statement."""

from __future__ import annotations

import json
from pathlib import Path

from raa.eval.fairness_audit import (
    FAIRNESS_GAP_STATEMENT,
    FairnessAuditReport,
    SubgroupMetrics,
    run_fairness_audit,
    save_fairness_audit,
    wilson_score_interval,
)


def test_wilson_score_interval_bounds_and_coverage():
    ci = wilson_score_interval(50, 100, confidence=0.95)
    assert 0.40 <= ci.low <= 0.45
    assert 0.55 <= ci.high <= 0.60

    zero_ci = wilson_score_interval(0, 50, confidence=0.95)
    assert zero_ci.low >= 0.0
    assert zero_ci.high < 0.10

    full_ci = wilson_score_interval(50, 50, confidence=0.95)
    assert full_ci.low > 0.90
    assert full_ci.high <= 1.0


def test_fairness_audit_report_execution():
    report = run_fairness_audit(on_test_split_only=True)
    assert isinstance(report, FairnessAuditReport)
    assert report.total_evaluated == 193
    assert FAIRNESS_GAP_STATEMENT in report.fairness_gap_statement
    assert len(report.subgroups) >= 8

    # Verify presence of key subgroups
    names = [sub.group_name for sub in report.subgroups]
    assert "Overall Benchmark Cohort" in names
    assert any("Age < 50" in name for name in names)
    assert any("Dense Breast Tissue" in name for name in names)

    # Check metrics integrity
    for sub in report.subgroups:
        assert isinstance(sub, SubgroupMetrics)
        assert 0.0 <= sub.cohort_share <= 1.0
        assert sub.baseline_error_ci.low <= sub.baseline_error_ci.high
        assert len(sub.sample_limitations) > 0


def test_save_fairness_audit_json(tmp_path: Path):
    target = tmp_path / "fairness_audit.json"
    result = save_fairness_audit(output_path=target, on_test_split_only=True)
    assert result == target
    assert target.is_file()

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["total_evaluated"] == 193
    assert "fairness_gap_statement" in data
    assert len(data["subgroups"]) >= 8
