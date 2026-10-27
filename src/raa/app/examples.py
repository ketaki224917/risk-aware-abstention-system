"""Deterministic examples selected only from the fixed held-out test partition."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from raa.data import BreastCancerData, DataSplit
from raa.explain.record import DecisionRecord
from raa.risk.policy import DecisionLevel


@dataclass(frozen=True)
class ExampleCase:
    """One labeled demo card; the recorded target stays hidden by default."""

    key: str
    title: str
    description: str
    test_position: int
    dataset_row: int


_CASE_TEXT = {
    "low_risk": (
        "Clear low-risk example",
        "Lowest-risk Automatic case in the held-out test split.",
    ),
    "high_concern": (
        "Clear high-concern example",
        "Highest-risk Human Review case in the held-out test split.",
    ),
    "borderline_review": (
        "Borderline Human Review example",
        "Human Review case nearest the validation-p90 cutoff from above.",
    ),
    "unusual": (
        "Unusual example",
        "A high-anomaly case in the top decile of the held-out test split.",
    ),
    "baseline_wrong": (
        "Always-predict baseline error",
        "The classifier made an error on this held-out case; the baseline always accepts it.",
    ),
    "random": (
        "Random held-out example",
        "A reproducible random case from the held-out test split.",
    ),
}


def select_example_cases(
    data: BreastCancerData,
    split: DataSplit,
    records: tuple[DecisionRecord, ...],
    *,
    random_seed: int = 20261027,
) -> dict[str, ExampleCase]:
    """Select six unique claims from test rows and corresponding real predictions."""
    test_indices = np.asarray(split.test, dtype=np.int64)
    if len(records) != len(test_indices) or not len(test_indices):
        raise ValueError("One prediction record is required for every held-out test row")
    chosen: dict[str, int] = {}
    used: set[int] = set()
    levels = np.array([record.level.value for record in records], dtype=object)
    risks = np.array([record.risk for record in records], dtype=float)
    anomalies = np.array([record.anomaly for record in records], dtype=float)
    threshold = records[0].assisted_threshold

    def choose(key: str, candidates: np.ndarray, scores: np.ndarray, *, largest: bool) -> None:
        available = np.asarray([index for index in candidates if int(index) not in used])
        if not len(available):
            raise ValueError(f"No unique held-out test case is available for {key}")
        local = scores[available]
        selected = int(available[np.argmax(local) if largest else np.argmin(local)])
        chosen[key] = selected
        used.add(selected)

    automatic = np.flatnonzero(levels == DecisionLevel.AUTOMATIC.value)
    human = np.flatnonzero(levels == DecisionLevel.HUMAN_REVIEW.value)
    choose("low_risk", automatic, risks, largest=False)
    choose("high_concern", human, risks, largest=True)
    borderline = human[risks[human] > threshold]
    choose("borderline_review", borderline, risks, largest=False)
    choose("unusual", np.arange(len(records)), anomalies, largest=True)

    always_predict_errors = np.asarray(
        [
            record.predicted_class != int(data.targets[test_indices[i]])
            for i, record in enumerate(records)
        ]
    )
    choose(
        "baseline_wrong",
        np.flatnonzero(always_predict_errors),
        risks,
        largest=True,
    )

    remaining = np.asarray([i for i in range(len(records)) if i not in used])
    if not len(remaining):
        raise ValueError("No held-out test case remains for the random example")
    random_position = int(np.random.default_rng(random_seed).choice(remaining))
    chosen["random"] = random_position

    return {
        key: ExampleCase(
            key=key,
            title=_CASE_TEXT[key][0],
            description=_CASE_TEXT[key][1],
            test_position=position,
            dataset_row=int(test_indices[position]),
        )
        for key, position in chosen.items()
    }
