"""Sensitivity checks for weights, consequence assumptions, and percentile pairs."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import product
from typing import Any

import numpy as np

from raa.eval.metrics import selective_metrics
from raa.pipeline import BatchDecisions
from raa.risk.engine import weighted_risk
from raa.risk.policy import PolicyThresholds


def evaluate_sensitivity(
    validation: BatchDecisions,
    test: BatchDecisions,
    targets: Any,
    base_weights: Mapping[str, float],
    base_consequences: Mapping[str, float],
) -> list[dict[str, Any]]:
    """Run predefined sensitivity grids; cutoffs are re-fit on validation each time."""
    rows: list[dict[str, Any]] = []
    val_full = {name: getattr(validation, name) for name in base_weights}
    test_full = {name: getattr(test, name) for name in base_weights}
    for delta in product((-0.1, 0.0, 0.1), repeat=3):
        keys = ("uncertainty", "anomaly", "consequence")
        changed = {key: max(0.0, float(base_weights[key]) + delta[i]) for i, key in enumerate(keys)}
        total = sum(changed.values())
        weights = {key: value / total for key, value in changed.items()}
        val_risk, test_risk = weighted_risk(val_full, weights), weighted_risk(test_full, weights)
        thresholds = PolicyThresholds.fit(val_risk)
        metrics = selective_metrics(targets, test.predicted_class, thresholds.route(test_risk))
        rows.append(
            {
                "seed": None,
                "scenario": "weights",
                "automatic_percentile": 70,
                "assisted_percentile": 90,
                **{f"weight_{key}": value for key, value in weights.items()},
                "predicted_malignant_consequence": float(base_consequences["predicted_malignant"]),
                "predicted_benign_consequence": float(base_consequences["predicted_benign"]),
                **metrics,
            }
        )
    for malignant, benign in product((0.2, 0.4, 0.6), (0.6, 0.8, 1.0)):
        val_components = dict(val_full)
        test_components = dict(test_full)
        val_components["consequence"] = np.where(validation.predicted_class == 0, malignant, benign)
        test_components["consequence"] = np.where(test.predicted_class == 0, malignant, benign)
        val_risk = weighted_risk(val_components, base_weights)
        test_risk = weighted_risk(test_components, base_weights)
        thresholds = PolicyThresholds.fit(val_risk)
        metrics = selective_metrics(targets, test.predicted_class, thresholds.route(test_risk))
        rows.append(
            {
                "seed": None,
                "scenario": "consequence",
                "automatic_percentile": 70,
                "assisted_percentile": 90,
                **{f"weight_{key}": float(value) for key, value in base_weights.items()},
                "predicted_malignant_consequence": malignant,
                "predicted_benign_consequence": benign,
                **metrics,
            }
        )
    for automatic, assisted in product((60, 70, 80), (80, 90, 95)):
        if automatic >= assisted:
            continue
        val_risk = weighted_risk(val_full, base_weights)
        test_risk = weighted_risk(test_full, base_weights)
        thresholds = PolicyThresholds.fit(
            val_risk, automatic_percentile=automatic, assisted_percentile=assisted
        )
        metrics = selective_metrics(targets, test.predicted_class, thresholds.route(test_risk))
        rows.append(
            {
                "seed": None,
                "scenario": "percentiles",
                "automatic_percentile": automatic,
                "assisted_percentile": assisted,
                **{f"weight_{key}": float(value) for key, value in base_weights.items()},
                "predicted_malignant_consequence": float(base_consequences["predicted_malignant"]),
                "predicted_benign_consequence": float(base_consequences["predicted_benign"]),
                **metrics,
            }
        )
    return rows
