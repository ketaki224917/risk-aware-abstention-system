from dataclasses import FrozenInstanceError

from raa.eval.explanation_eval import evaluate_explanation_checker
from raa.explain.checker import check_explanation
from raa.explain.fault_injection import FaultType, inject_fault
from raa.explain.record import DecisionRecord
from raa.explain.templates import generate_explanation
from raa.risk.policy import DecisionLevel


def make_record():
    return DecisionRecord(0, 0.88, 0.25, 0.40, 0.0, 0.29, DecisionLevel.AUTOMATIC, 0.35, 0.62)


def test_clean_template_passes_and_all_fault_types_are_detected():
    record = make_record()
    clean = generate_explanation(record)
    assert check_explanation(record, clean).passed
    for fault in FaultType:
        target = record
        if fault is FaultType.DROPPED_REASON:
            target = DecisionRecord(
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
            )
        injected = inject_fault(generate_explanation(target), target, fault)
        assert not check_explanation(target, injected).passed, fault.value


def test_checker_evaluation_reports_per_type_and_zero_clean_false_positives():
    metrics = evaluate_explanation_checker()
    assert metrics["clean_false_positive_rate"] == 0
    assert metrics["overall_detection_rate"] == 1
    assert len(metrics["per_fault"]) == len(FaultType)


def test_explanation_is_read_only_with_respect_to_the_decision_record():
    record = make_record()
    before = (record.predicted_class, record.level, record.risk)
    generate_explanation(record)
    after = (record.predicted_class, record.level, record.risk)
    assert before == after
    try:
        record.level = DecisionLevel.HUMAN_REVIEW
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Decision records must be immutable")
