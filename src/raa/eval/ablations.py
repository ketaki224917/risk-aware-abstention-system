"""Ablation evaluation with thresholds re-fit on validation for each component set."""

from __future__ import annotations

from collections.abc import Mapping

from numpy.typing import ArrayLike

from raa.eval.metrics import selective_metrics
from raa.pipeline import BatchDecisions
from raa.risk.engine import weighted_risk
from raa.risk.policy import PolicyThresholds

ABLATIONS: dict[str, tuple[str, ...]] = {
    "uncertainty_only": ("uncertainty",),
    "anomaly_only": ("anomaly",),
    "consequence_only": ("consequence",),
    "uncertainty_anomaly": ("uncertainty", "anomaly"),
    "uncertainty_consequence": ("uncertainty", "consequence"),
    "anomaly_consequence": ("anomaly", "consequence"),
    "full": ("uncertainty", "anomaly", "consequence"),
}


def evaluate_ablations(
    validation: BatchDecisions,
    test: BatchDecisions,
    targets: ArrayLike,
    weights: Mapping[str, float],
    *,
    automatic_percentile: float,
    assisted_percentile: float,
) -> list[dict[str, object]]:
    """Score each ablation, selecting both cutoffs solely from validation risks."""
    rows: list[dict[str, object]] = []
    for name, included in ABLATIONS.items():
        val_components = {key: getattr(validation, key) for key in included}
        test_components = {key: getattr(test, key) for key in included}
        reduced_weights = {key: weights[key] for key in included}
        validation_risk = weighted_risk(val_components, reduced_weights)
        risk = weighted_risk(test_components, reduced_weights)
        policy = PolicyThresholds.fit(
            validation_risk,
            automatic_percentile=automatic_percentile,
            assisted_percentile=assisted_percentile,
        )
        metrics = selective_metrics(targets, test.predicted_class, policy.route(risk))
        rows.append({"ablation": name, **metrics})
    return rows
