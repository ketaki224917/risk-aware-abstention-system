"""Tests for human review workload evaluation, capacity sweeps, and offline policy simulations."""

from __future__ import annotations

import json
from pathlib import Path

from raa.eval.workload_simulation import (
    HUMAN_REVIEW_CLAIM_BOUNDARY,
    CapacitySettingResult,
    OfflinePolicyComparison,
    WorkloadEvaluationReport,
    run_workload_simulation,
    save_workload_simulation,
)


def test_workload_simulation_execution():
    report = run_workload_simulation()
    assert isinstance(report, WorkloadEvaluationReport)
    assert report.sample_evaluated_count == 193
    assert HUMAN_REVIEW_CLAIM_BOUNDARY in report.claim_boundary
    assert len(report.capacity_sweep) >= 8

    # Verify monotonic trends in capacity sweep
    caps = [res.capacity_per_100 for res in report.capacity_sweep]
    assert caps == sorted(caps)

    # Workload share should generally increase as capacity increases
    workload_shares = [res.review_workload_share for res in report.capacity_sweep]
    assert workload_shares[-1] > workload_shares[0]

    # Automatic false negatives should decrease as capacity increases
    auto_fns = [res.false_negatives_in_automatic for res in report.capacity_sweep]
    assert auto_fns[-1] <= auto_fns[0]

    for item in report.capacity_sweep:
        assert isinstance(item, CapacitySettingResult)
        assert 0.0 <= item.automatic_share <= 1.0
        assert 0.0 <= item.false_negative_catch_rate <= 1.0

    # Verify offline policy comparisons
    assert len(report.offline_policy_simulations) >= 4
    for policy in report.offline_policy_simulations:
        assert isinstance(policy, OfflinePolicyComparison)
        assert len(policy.policy_name) > 0
        assert 0.0 <= policy.net_system_error_rate <= 1.0


def test_save_workload_simulation_json(tmp_path: Path):
    out_file = save_workload_simulation(output_dir=tmp_path)
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["sample_evaluated_count"] == 193
    assert "claim_boundary" in data
    assert len(data["capacity_sweep"]) >= 8
    assert len(data["offline_policy_simulations"]) >= 4
