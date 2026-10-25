"""Classification and selective-prediction metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import accuracy_score, roc_auc_score


def binary_classification_metrics(
    targets: ArrayLike, predictions: ArrayLike
) -> dict[str, float | int]:
    """Return accuracy, errors, false negatives, and false positives (malignant=0)."""
    y, pred = np.asarray(targets), np.asarray(predictions)
    if y.shape != pred.shape:
        raise ValueError("Targets and predictions must have the same shape")
    return {
        "n": int(y.size),
        "accuracy": float(accuracy_score(y, pred)),
        "error_rate": float(np.mean(y != pred)),
        "false_negatives": int(np.sum((y == 0) & (pred == 1))),
        "false_positives": int(np.sum((y == 1) & (pred == 0))),
    }


def selective_metrics(
    targets: ArrayLike, predictions: ArrayLike, levels: ArrayLike
) -> dict[str, float | int]:
    """Summarize automatic coverage, accepted-case performance, and review workload."""
    y, pred, route = np.asarray(targets), np.asarray(predictions), np.asarray(levels, dtype=object)
    if not (y.shape == pred.shape == route.shape):
        raise ValueError("Targets, predictions, and levels must have the same shape")
    automatic = route == "Automatic"
    assisted = route == "Assisted"
    human = route == "Human Review"
    accepted_errors = int(np.sum((y != pred) & automatic))
    accepted = int(automatic.sum())
    return {
        "n": int(y.size),
        "automatic_count": accepted,
        "automatic_coverage": float(automatic.mean()),
        "selective_accuracy": float(1 - accepted_errors / accepted) if accepted else float("nan"),
        "selective_error_rate": float(accepted_errors / accepted) if accepted else float("nan"),
        "assisted_count": int(assisted.sum()),
        "human_review_count": int(human.sum()),
        "review_workload_count": int(assisted.sum() + human.sum()),
        "review_workload_fraction": float((assisted | human).mean()),
        "false_negatives_automatic": int(np.sum((y == 0) & (pred == 1) & automatic)),
        "false_negatives_routed_away": int(np.sum((y == 0) & (pred == 1) & ~automatic)),
    }


def uncertainty_diagnostics(
    targets: ArrayLike, predictions: ArrayLike, uncertainty: ArrayLike
) -> dict[str, float]:
    """Evaluate U as a ranking signal for classifier errors; not calibrated error probability."""
    y, pred, u = np.asarray(targets), np.asarray(predictions), np.asarray(uncertainty, dtype=float)
    errors = (y != pred).astype(int)
    auc = float(roc_auc_score(errors, u)) if np.unique(errors).size == 2 else float("nan")
    correlation = (
        float(np.corrcoef(u, errors)[0, 1]) if u.std() > 0 and errors.std() > 0 else float("nan")
    )
    return {"uncertainty_error_auroc": auc, "uncertainty_error_correlation": correlation}


def expected_calibration_error(
    targets: ArrayLike, malignant_probability: ArrayLike, bins: int = 10
) -> float:
    """Compute equal-width ECE for P(malignant), using class 0 as the positive event."""
    y = np.asarray(targets)
    p = np.asarray(malignant_probability, dtype=float)
    if y.shape != p.shape or bins <= 0:
        raise ValueError("Invalid targets, probabilities, or bin count")
    observed = (y == 0).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for index in range(bins):
        mask = (p >= edges[index]) & (
            (p <= edges[index + 1]) if index == bins - 1 else (p < edges[index + 1])
        )
        if mask.any():
            ece += float(mask.mean()) * abs(float(p[mask].mean()) - float(observed[mask].mean()))
    return ece
