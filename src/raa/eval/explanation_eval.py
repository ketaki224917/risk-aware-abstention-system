"""Checker evaluation on clean templates and injected faults."""

from __future__ import annotations

from collections.abc import Sequence

from raa.explain.checker import check_explanation
from raa.explain.fault_injection import FaultType, inject_fault
from raa.explain.record import DecisionRecord
from raa.explain.templates import generate_explanation
from raa.risk.policy import DecisionLevel


def evaluate_explanation_checker(
    records: Sequence[DecisionRecord] | None = None,
) -> dict[str, object]:
    """Measure clean false positives and injected-fault detection by fault type."""
    if records is None:
        records = (
            DecisionRecord(0, 0.91, 0.12, 0.25, 0.4, 0.21, DecisionLevel.AUTOMATIC, 0.35, 0.62),
            DecisionRecord(
                1,
                0.18,
                0.31,
                0.61,
                1.0,
                0.71,
                DecisionLevel.HUMAN_REVIEW,
                0.35,
                0.62,
                "ensemble disagreement (uncertainty)",
            ),
        )
    clean_results = [
        check_explanation(record, generate_explanation(record)).passed for record in records
    ]
    per_fault: dict[str, dict[str, int | float]] = {}
    detected = total = 0
    for fault in FaultType:
        found = 0
        eligible = tuple(
            record
            for record in records
            if (
                fault is not FaultType.DROPPED_REASON or record.level is not DecisionLevel.AUTOMATIC
            )
            and (
                fault is not FaultType.POLICY_CONTRADICTION
                or record.level is DecisionLevel.AUTOMATIC
            )
        )
        for record in eligible:
            text = inject_fault(generate_explanation(record), record, fault)
            found += int(not check_explanation(record, text).passed)
        per_fault[fault.value] = {
            "detected": found,
            "injected": len(eligible),
            "detection_rate": found / len(eligible) if eligible else 0.0,
        }
        detected += found
        total += len(eligible)
    return {
        "clean_count": len(clean_results),
        "clean_false_positives": int(sum(not result for result in clean_results)),
        "clean_false_positive_rate": float(
            sum(not result for result in clean_results) / len(clean_results)
        ),
        "fault_count": total,
        "faults_detected": detected,
        "overall_detection_rate": detected / total,
        "per_fault": per_fault,
    }
