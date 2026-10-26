"""Resumable 30-split evaluation and machine-readable result generation."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
from sklearn.metrics import roc_auc_score

from raa.data import load_breast_cancer_data, stratified_split
from raa.eval.ablations import evaluate_ablations
from raa.eval.metrics import (
    binary_classification_metrics,
    expected_calibration_error,
    malignant_brier_score,
    selective_metrics,
    uncertainty_diagnostics,
)
from raa.eval.sensitivity import evaluate_sensitivity
from raa.eval.stats import summarize
from raa.pipeline import fit_system
from raa.risk.policy import PolicyThresholds

logger = logging.getLogger(__name__)


def _source_fingerprint(source_root: Path) -> str:
    """Hash exact Python source so a cache cannot survive implementation changes."""
    digest = hashlib.sha256()
    for path in sorted(source_root.rglob("*.py")):
        digest.update(path.relative_to(source_root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _safe_roc_auc(targets: np.ndarray, scores: np.ndarray) -> float:
    """Return AUROC, or NaN if a test split contains only one outcome class."""
    if np.unique(targets).size < 2:
        return float("nan")
    return float(roc_auc_score(targets, scores))


def _metrics_for_split(config: dict[str, Any], seed: int, data: Any) -> dict[str, Any]:
    split = stratified_split(
        data.targets,
        seed=seed,
        test_fraction=float(config["data"]["test_fraction"]),
        validation_fraction_of_remainder=float(config["data"]["validation_fraction_of_remainder"]),
    )
    system = fit_system(
        data.features, data.targets, split.train, split.validation, config, seed=seed
    )
    validation = system.predict_batch(data.features[split.validation])
    test = system.predict_batch(data.features[split.test])
    y = data.targets[split.test]
    baseline = binary_classification_metrics(y, test.predicted_class)
    selected = selective_metrics(y, test.predicted_class, test.level)
    selected["false_negative_routed_away_rate"] = (
        selected["false_negatives_routed_away"] / baseline["false_negatives"]
        if baseline["false_negatives"]
        else float("nan")
    )
    for level_name in ("Automatic", "Assisted", "Human Review"):
        mask = test.level == level_name
        level_slug = level_name.lower().replace(" ", "_")
        count = int(mask.sum())
        error_mask = (y != test.predicted_class) & mask
        selected[f"{level_slug}_count"] = count
        selected[f"{level_slug}_error_count"] = int(error_mask.sum())
        selected[f"{level_slug}_error_rate"] = (
            float(error_mask.sum() / count) if count else float("nan")
        )
        selected[f"{level_slug}_false_negatives"] = int(
            np.sum((y == 0) & (test.predicted_class == 1) & mask)
        )
    row = {"seed": seed, **baseline, **{f"full_{k}": v for k, v in selected.items() if k != "n"}}
    error_targets = (y != test.predicted_class).astype(int)
    row.update(
        {
            "confidence_error_auroc": _safe_roc_auc(error_targets, test.confidence_risk),
            "anomaly_error_auroc": _safe_roc_auc(error_targets, test.anomaly),
            "uncertainty_anomaly_error_auroc": _safe_roc_auc(
                error_targets, 0.7 * test.uncertainty + 0.3 * test.anomaly
            ),
            "full_risk_error_auroc": _safe_roc_auc(error_targets, test.risk),
        }
    )
    row.update(uncertainty_diagnostics(y, test.predicted_class, test.uncertainty))
    row["ece"] = expected_calibration_error(
        y, test.malignant_probability, bins=int(config["evaluation"]["reliability_bins"])
    )
    row["brier_score"] = malignant_brier_score(y, test.malignant_probability)
    automatic = test.level == "Automatic"
    row["accepted_ece"] = (
        expected_calibration_error(
            y[automatic],
            test.malignant_probability[automatic],
            bins=int(config["evaluation"]["reliability_bins"]),
        )
        if automatic.any()
        else float("nan")
    )
    row["accepted_brier_score"] = (
        malignant_brier_score(y[automatic], test.malignant_probability[automatic])
        if automatic.any()
        else float("nan")
    )
    ablations = evaluate_ablations(
        validation,
        test,
        y,
        system.weights,
        automatic_percentile=float(config["policy"]["automatic_percentile"]),
        assisted_percentile=float(config["policy"]["assisted_percentile"]),
    )
    sensitivity = evaluate_sensitivity(
        validation, test, y, system.weights, system.consequence_values
    )
    curve_rows: list[dict[str, Any]] = []
    distribution_rows = [
        {
            "seed": seed,
            "risk": float(value),
            "uncertainty": float(uncertainty),
            "anomaly": float(anomaly),
            "consequence": float(consequence),
            "decision_level": str(level),
            "target": int(target),
            "prediction": int(prediction),
            "error": int(target != prediction),
            "false_negative": int(target == 0 and prediction == 1),
        }
        for value, uncertainty, anomaly, consequence, level, target, prediction in zip(
            test.risk,
            test.uncertainty,
            test.anomaly,
            test.consequence,
            test.level,
            y,
            test.predicted_class,
            strict=True,
        )
    ]
    diagnostics_rows = [
        {
            "seed": seed,
            "dataset_row": int(dataset_row),
            "target": int(target),
            "malignant_probability": float(probability),
            "confidence_risk": float(confidence_risk),
            "uncertainty": float(uncertainty),
            "anomaly": float(anomaly),
            "risk": float(risk),
            "error": int(target != prediction),
        }
        for (
            dataset_row,
            target,
            probability,
            confidence_risk,
            uncertainty,
            anomaly,
            risk,
            prediction,
        ) in zip(
            split.test,
            y,
            test.malignant_probability,
            test.confidence_risk,
            test.uncertainty,
            test.anomaly,
            test.risk,
            test.predicted_class,
            strict=True,
        )
    ]
    val_full_risk = validation.risk
    test_full_risk = test.risk
    for percentile in config["evaluation"]["risk_percentile_sweep"]:
        if float(percentile) > float(config["policy"]["assisted_percentile"]):
            continue
        policy = PolicyThresholds.fit(
            val_full_risk,
            automatic_percentile=float(percentile),
            assisted_percentile=float(config["policy"]["assisted_percentile"]),
        )
        curve = selective_metrics(y, test.predicted_class, policy.route(test_full_risk))
        curve_rows.append(
            {
                "seed": seed,
                "automatic_percentile": percentile,
                "assisted_percentile": config["policy"]["assisted_percentile"],
                "selected_operating_point": float(percentile) == 70.0
                and float(config["policy"]["assisted_percentile"]) == 90.0,
                **curve,
            }
        )
    return {
        "metrics": row,
        "ablations": [{"seed": seed, **item} for item in ablations],
        "risk_coverage": curve_rows,
        "risk_distribution": distribution_rows,
        "diagnostics": diagnostics_rows,
        "sensitivity": [{**item, "seed": seed} for item in sensitivity],
    }


def run_experiments(
    config: dict[str, Any], results_root: str | Path = "results/runs", run_id: str | None = None
) -> Path:
    """Run 30 stratified splits, resume per-split JSON cache, and write CSV/JSON."""
    data = load_breast_cancer_data()
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    project_root = Path(__file__).resolve().parents[3]
    output_root = Path(results_root)
    if not output_root.is_absolute():
        output_root = project_root / output_root
    output = output_root / run_id
    cache_dir = output / "splits"
    cache_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2]
    source_fingerprint = _source_fingerprint(source_root)
    lock_fingerprint = hashlib.sha256((project_root / "uv.lock").read_bytes()).hexdigest()
    run_identity = {
        "config": config,
        "source": source_fingerprint,
        "lock": lock_fingerprint,
        "python": list(sys.version_info[:3]),
    }
    fingerprint = hashlib.sha256(json.dumps(run_identity, sort_keys=True).encode()).hexdigest()
    metrics_rows: list[dict[str, Any]] = []
    ablation_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    distribution_rows: list[dict[str, Any]] = []
    diagnostics_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    base_seed, count = int(config["data"]["base_seed"]), int(config["data"]["split_count"])
    for index in range(count):
        seed = base_seed + index
        cache_path = cache_dir / f"split_{index:02d}.json"
        cached = None
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached is None or cached.get("config_fingerprint") != fingerprint:
            logger.info("Fitting split %d/%d (seed=%d)", index + 1, count, seed)
            result = _metrics_for_split(config, seed, data)
            cached = {"config_fingerprint": fingerprint, **result}
            cache_path.write_text(json.dumps(_to_jsonable(cached), indent=2), encoding="utf-8")
        metrics_rows.append(cached["metrics"])
        ablation_rows.extend(cached["ablations"])
        curve_rows.extend(cached["risk_coverage"])
        distribution_rows.extend(cached["risk_distribution"])
        diagnostics_rows.extend(cached["diagnostics"])
        sensitivity_rows.extend(cached["sensitivity"])
    _write_csv(output / "per_split.csv", metrics_rows)
    _write_csv(output / "ablations.csv", ablation_rows)
    _write_csv(output / "risk_coverage.csv", curve_rows)
    _write_csv(output / "risk_distribution.csv", distribution_rows)
    _write_csv(output / "diagnostics.csv", diagnostics_rows)
    _write_csv(output / "sensitivity.csv", sensitivity_rows)
    numeric_fields = [
        key
        for key, value in metrics_rows[0].items()
        if key != "seed" and isinstance(value, (int, float))
    ]
    summaries = {
        field: summarize(
            [row[field] for row in metrics_rows], seed=int(config["evaluation"]["bootstrap_seed"])
        )
        for field in numeric_fields
    }
    ablation_summary: dict[str, Any] = {}
    full_by_seed = {
        int(row["seed"]): float(row["selective_accuracy"])
        for row in ablation_rows
        if row["ablation"] == "full"
    }
    for name in sorted({str(row["ablation"]) for row in ablation_rows}):
        values = {
            int(row["seed"]): float(row["selective_accuracy"])
            for row in ablation_rows
            if row["ablation"] == name
        }
        stats = summarize(list(values.values()), seed=int(config["evaluation"]["bootstrap_seed"]))
        paired = summarize(
            [values[s] - full_by_seed[s] for s in values if s in full_by_seed],
            seed=int(config["evaluation"]["bootstrap_seed"]),
        )
        ablation_summary[name] = {"selective_accuracy": stats, "paired_difference_vs_full": paired}
    sensitivity_summary: dict[str, Any] = {}
    for scenario in sorted({str(row["scenario"]) for row in sensitivity_rows}):
        values = [row for row in sensitivity_rows if row["scenario"] == scenario]
        by_setting: dict[str, list[float]] = {}
        for row in values:
            signature = json.dumps(
                {
                    key: row[key]
                    for key in row
                    if key in {"scenario", "automatic_percentile", "assisted_percentile"}
                    or key.startswith(("weight_", "predicted_"))
                },
                sort_keys=True,
            )
            by_setting.setdefault(signature, []).append(float(row["selective_accuracy"]))
        sensitivity_summary[scenario] = {
            signature: summarize(scores, seed=int(config["evaluation"]["bootstrap_seed"]))
            for signature, scores in by_setting.items()
        }
    total_n = sum(int(row["n"]) for row in metrics_rows)
    pooled_errors = sum(int(row["error_count"]) for row in metrics_rows)
    pooled_fn = sum(int(row["false_negatives"]) for row in metrics_rows)
    pooled_fp = sum(int(row["false_positives"]) for row in metrics_rows)
    automatic_n = sum(int(row["full_automatic_count"]) for row in metrics_rows)
    automatic_errors = sum(int(row["full_accepted_error_count"]) for row in metrics_rows)
    fn_away = sum(int(row["full_false_negatives_routed_away"]) for row in metrics_rows)
    pooled = {
        "n": total_n,
        "accuracy": (total_n - pooled_errors) / total_n,
        "error_rate": pooled_errors / total_n,
        "false_negatives": pooled_fn,
        "false_positives": pooled_fp,
        "automatic_count": automatic_n,
        "automatic_coverage": automatic_n / total_n,
        "selective_accuracy": 1 - automatic_errors / automatic_n if automatic_n else None,
        "selective_error_rate": automatic_errors / automatic_n if automatic_n else None,
        "false_negatives_routed_away": fn_away,
        "false_negatives_routed_away_rate": fn_away / pooled_fn if pooled_fn else None,
    }
    decision_levels: dict[str, dict[str, Any]] = {}
    for level in ("Automatic", "Assisted", "Human Review"):
        selected_rows = [row for row in distribution_rows if row["decision_level"] == level]
        level_count = len(selected_rows)
        level_errors = sum(int(row["error"]) for row in selected_rows)
        decision_levels[level] = {
            "count": level_count,
            "share": level_count / total_n,
            "errors": level_errors,
            "error_rate": level_errors / level_count if level_count else None,
            "false_negatives": sum(int(row["false_negative"]) for row in selected_rows),
        }
    pooled_diagnostics: dict[str, float] = {}
    error_targets = np.asarray([int(row["error"]) for row in diagnostics_rows])
    for key in ("confidence_risk", "uncertainty", "anomaly", "risk"):
        pooled_diagnostics[f"{key}_error_auroc"] = _safe_roc_auc(
            error_targets, np.asarray([float(row[key]) for row in diagnostics_rows])
        )
    pooled_diagnostics["uncertainty_anomaly_error_auroc"] = _safe_roc_auc(
        error_targets,
        0.7 * np.asarray([float(row["uncertainty"]) for row in diagnostics_rows])
        + 0.3 * np.asarray([float(row["anomaly"]) for row in diagnostics_rows]),
    )
    metrics_json = {
        "run_id": run_id,
        "split_count": count,
        "test_cases": count
        * int(round(data.features.shape[0] * float(config["data"]["test_fraction"]))),
        "seed_range": [base_seed, base_seed + count - 1],
        "config_fingerprint": fingerprint,
        "source_fingerprint": source_fingerprint,
        "lock_fingerprint": lock_fingerprint,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "pooled_case_metrics": pooled,
        "pooled_error_ranking_auroc": pooled_diagnostics,
        "pooled_decision_level_metrics": decision_levels,
        "split_metric_mean_std_ci95": summaries,
        "ablation_summary": ablation_summary,
        "sensitivity_summary": sensitivity_summary,
        "files": [
            "per_split.csv",
            "ablations.csv",
            "risk_coverage.csv",
            "risk_distribution.csv",
            "diagnostics.csv",
            "sensitivity.csv",
            "main_split_metrics.json",
        ],
    }
    (output / "metrics.json").write_text(
        json.dumps(_to_jsonable(metrics_json), indent=2), encoding="utf-8"
    )
    logger.info("Wrote 30-split results to %s", output)
    return output
