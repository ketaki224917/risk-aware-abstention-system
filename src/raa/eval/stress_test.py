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
from raa.models.anomaly import anomaly_score
from raa.pipeline import fit_system
from raa.viz.plots import plot_stress_roc

logger = logging.getLogger(__name__)


def _paired_auc_ci(
    clean: np.ndarray, shifted_by_case: np.ndarray, *, seed: int, replicates: int
) -> tuple[float, float, float]:
    shifted = np.asarray(shifted_by_case, dtype=float)
    if shifted.ndim == 1:
        shifted = shifted[None, :]
    if shifted.shape[1] != clean.size:
        raise ValueError("Clean and shifted scores must share held-out case IDs")
    y = np.r_[np.zeros(clean.size, dtype=int), np.ones(shifted.size, dtype=int)]
    scores = np.r_[clean, shifted.ravel()]
    point = float(roc_auc_score(y, scores))
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates)
    for index in range(replicates):
        sampled_cases = rng.integers(0, clean.size, size=clean.size)
        sampled_clean = clean[sampled_cases]
        sampled_shifted = shifted[:, sampled_cases].ravel()
        draws[index] = roc_auc_score(
            np.r_[np.zeros(sampled_clean.size), np.ones(sampled_shifted.size)],
            np.r_[sampled_clean, sampled_shifted],
        )
    return point, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def run_stress_test(config: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Shift selected features by k train-set standard deviations; never fit on test."""
    data = load_breast_cancer_data()
    seed = int(config["stress_test"]["seed"])
    split = stratified_split(
        data.targets,
        seed=seed,
        test_fraction=float(config["data"]["test_fraction"]),
        validation_fraction_of_remainder=float(config["data"]["validation_fraction_of_remainder"]),
    )
    system = fit_system(
        data.features, data.targets, split.train, split.validation, config, seed=seed
    )
    train_std = data.features[split.train].std(axis=0, ddof=0)
    clean_x = data.features[split.test]
    clean_scores = anomaly_score(system.anomaly_model, clean_x)
    rng = np.random.default_rng(int(config["stress_test"]["seed"]))
    selected_order = rng.permutation(data.features.shape[1])
    shifted_score_groups: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    ci_seed = int(config["evaluation"]["bootstrap_seed"])
    reps = int(config["evaluation"]["bootstrap_replicates"])
    for subset_size in config["stress_test"]["feature_subset_sizes"]:
        columns = selected_order[: int(subset_size)]
        for multiplier in config["stress_test"]["shift_multipliers"]:
            shifted_x = clean_x.copy()
            shifted_x[:, columns] += float(multiplier) * train_std[columns]
            scores = anomaly_score(system.anomaly_model, shifted_x)
            shifted_score_groups.append(scores)
            auc, low, high = _paired_auc_ci(
                clean_scores, scores[None, :], seed=ci_seed, replicates=reps
            )
            rows.append(
                {
                    "feature_subset_size": int(subset_size),
                    "shift_sigma": float(multiplier),
                    "shifted_feature_indices": ",".join(map(str, columns)),
                    "clean_vs_perturbed_auroc": auc,
                    "ci95_low": low,
                    "ci95_high": high,
                    "clean_count": int(clean_x.shape[0]),
                    "perturbed_count": int(shifted_x.shape[0]),
                }
            )
            batch = system.predict_batch(shifted_x)
            levels = batch.level
            policy_rows.append(
                {
                    "feature_subset_size": int(subset_size),
                    "shift_sigma": float(multiplier),
                    "automatic_fraction": float(np.mean(levels == "Automatic")),
                    "assisted_fraction": float(np.mean(levels == "Assisted")),
                    "human_review_fraction": float(np.mean(levels == "Human Review")),
                    "escalated_fraction": float(np.mean(levels != "Automatic")),
                }
            )
    pooled_shifted = np.vstack(shifted_score_groups)
    pooled_auc, pooled_low, pooled_high = _paired_auc_ci(
        clean_scores, pooled_shifted, seed=ci_seed, replicates=reps
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plot_stress_roc(clean_scores, pooled_shifted, output / "stress_roc.png")
    _write_rows(output / "stress_test.csv", rows)
    _write_rows(output / "stress_policy.csv", policy_rows)
    result = {
        "seed": seed,
        "test_count": int(clean_x.shape[0]),
        "recipe": "Add positive k * training standard deviation to a seeded random feature subset; "
        "score clean and perturbed held-out test rows with training-fitted Isolation Forest.",
        "confidence_interval_method": (
            "Paired bootstrap over held-out test case IDs; all perturbation variants "
            "for a sampled case stay in the same resample."
        ),
        "pooled_clean_vs_perturbed_auroc": pooled_auc,
        "pooled_auroc_ci95": [pooled_low, pooled_high],
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
