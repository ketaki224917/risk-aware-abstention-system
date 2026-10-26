"""Synthetic feature-shift anomaly stress test and policy escalation analysis."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import roc_auc_score

from raa.data import load_breast_cancer_data, stratified_split
from raa.pipeline import fit_system
from raa.viz.plots import plot_stress_roc

logger = logging.getLogger(__name__)


def _cluster_auc_ci(
    case_ids: np.ndarray,
    clean: np.ndarray,
    shifted: np.ndarray,
    *,
    seed: int,
    replicates: int,
) -> tuple[float, float, float]:
    """Bootstrap paired clean/shifted scores by original dataset case ID."""
    ids = np.asarray(case_ids, dtype=np.int64)
    clean_scores = np.asarray(clean, dtype=float)
    shifted_scores = np.asarray(shifted, dtype=float)
    if not (ids.shape == clean_scores.shape == shifted_scores.shape):
        raise ValueError("Case IDs and paired score arrays must have matching shapes")
    classes = np.unique(ids)
    groups = {case_id: np.flatnonzero(ids == case_id) for case_id in classes}

    def auc(indices: np.ndarray) -> float:
        y = np.r_[np.zeros(indices.size, dtype=int), np.ones(indices.size, dtype=int)]
        return float(roc_auc_score(y, np.r_[clean_scores[indices], shifted_scores[indices]]))

    point = auc(np.arange(ids.size))
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates)
    for index in range(replicates):
        sampled_ids = rng.choice(classes, size=classes.size, replace=True)
        indices = np.concatenate([groups[case_id] for case_id in sampled_ids])
        draws[index] = auc(indices)
    return point, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def run_stress_test(config: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Run the paper's eight-feature, signed three-sigma stress test over 30 splits."""
    data = load_breast_cancer_data()
    split_count = int(config["data"]["split_count"])
    base_seed = int(config["data"]["base_seed"])
    magnitude = float(config["stress_test"]["shift_magnitude_sigma"])
    feature_count = int(config["stress_test"]["feature_count"])
    clip_minimum = float(config["stress_test"]["clip_minimum"])
    seed = int(config["stress_test"]["seed"])
    rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    case_groups: list[np.ndarray] = []
    clean_groups = {name: [] for name in ("anomaly", "uncertainty", "risk")}
    shifted_groups = {name: [] for name in ("anomaly", "uncertainty", "risk")}
    shifted_accuracy: list[float] = []
    for index in range(split_count):
        split_seed = base_seed + index
        split = stratified_split(
            data.targets,
            seed=split_seed,
            test_fraction=float(config["data"]["test_fraction"]),
            validation_fraction_of_remainder=float(
                config["data"]["validation_fraction_of_remainder"]
            ),
        )
        system = fit_system(
            data.features, data.targets, split.train, split.validation, config, seed=split_seed
        )
        clean_x = data.features[split.test]
        shifted_x = clean_x.copy()
        train_std = data.features[split.train].std(axis=0, ddof=0)
        rng = np.random.default_rng(seed + split_seed)
        for case_index in range(len(split.test)):
            columns = rng.choice(data.features.shape[1], size=feature_count, replace=False)
            signs = rng.choice((-1.0, 1.0), size=feature_count)
            shifted_x[case_index, columns] += signs * magnitude * train_std[columns]
        shifted_x = np.maximum(shifted_x, clip_minimum)
        clean_batch = system.predict_batch(clean_x)
        shifted_batch = system.predict_batch(shifted_x)
        score_pairs = {
            "anomaly": (clean_batch.anomaly, shifted_batch.anomaly),
            "uncertainty": (clean_batch.uncertainty, shifted_batch.uncertainty),
            "risk": (clean_batch.risk, shifted_batch.risk),
        }
        split_aucs: dict[str, float] = {}
        for name, (clean_score, shifted_score) in score_pairs.items():
            split_aucs[name] = float(
                roc_auc_score(
                    np.r_[np.zeros(len(clean_score)), np.ones(len(shifted_score))],
                    np.r_[clean_score, shifted_score],
                )
            )
            clean_groups[name].append(clean_score)
            shifted_groups[name].append(shifted_score)
        rows.append(
            {
                "seed": split_seed,
                "feature_subset_rule": f"{feature_count} random features per case",
                "feature_subset_seed": seed + split_seed,
                "anomaly_auroc": split_aucs["anomaly"],
                "uncertainty_auroc": split_aucs["uncertainty"],
                "risk_auroc": split_aucs["risk"],
                "test_count": int(len(split.test)),
            }
        )
        labels = data.targets[split.test]
        shifted_accuracy.append(float(np.mean(shifted_batch.predicted_class == labels)))
        clean_levels, shifted_levels = clean_batch.level, shifted_batch.level
        automatic = shifted_levels == "Automatic"
        policy_rows.append(
            {
                "seed": split_seed,
                "clean_automatic_fraction": float(np.mean(clean_levels == "Automatic")),
                "perturbed_automatic_fraction": float(np.mean(automatic)),
                "perturbed_assisted_fraction": float(np.mean(shifted_levels == "Assisted")),
                "perturbed_human_review_fraction": float(np.mean(shifted_levels == "Human Review")),
                "perturbed_escalated_fraction": float(np.mean(~automatic)),
                "perturbed_always_predict_accuracy": shifted_accuracy[-1],
                "perturbed_automatic_selective_accuracy": (
                    float(np.mean(shifted_batch.predicted_class[automatic] == labels[automatic]))
                    if automatic.any()
                    else float("nan")
                ),
            }
        )
        case_groups.append(split.test)
    case_ids = np.concatenate(case_groups)
    ci_seed = int(config["evaluation"]["bootstrap_seed"])
    reps = int(config["evaluation"]["bootstrap_replicates"])
    summaries: dict[str, Any] = {}
    pooled_scores: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name in ("anomaly", "uncertainty", "risk"):
        clean = np.concatenate(clean_groups[name])
        shifted = np.concatenate(shifted_groups[name])
        pooled_scores[name] = clean, shifted
        auc_value, low, high = _cluster_auc_ci(
            case_ids, clean, shifted, seed=ci_seed, replicates=reps
        )
        split_values = np.asarray([row[f"{name}_auroc"] for row in rows], dtype=float)
        summaries[name] = {
            "mean": float(split_values.mean()),
            "std": float(split_values.std(ddof=1)),
            "pooled_auroc": auc_value,
            "cluster_bootstrap_ci95": [low, high],
        }
    pooled_clean, pooled_shifted = pooled_scores["anomaly"]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plot_stress_roc(pooled_clean, pooled_shifted, output / "stress_roc.png")
    _write_rows(output / "stress_test.csv", rows)
    _write_rows(output / "stress_policy.csv", policy_rows)
    result = {
        "seed": seed,
        "split_seed_range": [base_seed, base_seed + split_count - 1],
        "test_cases": int(sum(len(ids) for ids in case_groups)),
        "recipe": (
            f"For every held-out case, independently select {feature_count} random features and "
            f"add a seeded random +/-{magnitude:g} training-standard-deviation shift to each; "
            f"clip values below {clip_minimum:g}. The Isolation Forest and feature scaler are "
            "fitted on training data only. This resolves the paper's unspecified perturbation RNG."
        ),
        "confidence_interval_method": (
            "Paired cluster bootstrap over original dataset row IDs; each sampled row keeps its "
            "clean and shifted scores together across all split occurrences."
        ),
        "score_summaries": summaries,
        "perturbed_always_predict_accuracy_mean": float(np.mean(shifted_accuracy)),
        "variants": rows,
        "policy_behavior": policy_rows,
    }
    (output / "stress_test.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("Stress test results written to %s", output)
    return result


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
