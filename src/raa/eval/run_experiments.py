"""Resumable 30-split evaluation and machine-readable result generation."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from raa.data import load_breast_cancer_data, stratified_split
from raa.eval.ablations import evaluate_ablations
from raa.eval.metrics import (
    binary_classification_metrics,
    expected_calibration_error,
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
    row = {"seed": seed, **baseline, **{f"full_{k}": v for k, v in selected.items() if k != "n"}}
    row.update(uncertainty_diagnostics(y, test.predicted_class, test.uncertainty))
    row["ece"] = expected_calibration_error(
        y, test.malignant_probability, bins=int(config["evaluation"]["reliability_bins"])
    )
    ablations = evaluate_ablations(
        validation,
        test,
        y,
        system.weights,
        automatic_percentile=float(config["policy"]["automatic_percentile"]),
        assisted_percentile=float(config["policy"]["assisted_percentile"]),
    )
    sensitivity = evaluate_sensitivity(validation, test, y, system.weights)
    curve_rows: list[dict[str, Any]] = []
    distribution_rows = [
        {"seed": seed, "risk": float(value), "decision_level": str(level)}
        for value, level in zip(test.risk, test.level, strict=True)
    ]
    diagnostics_rows = [
        {
            "seed": seed,
            "target": int(target),
            "malignant_probability": float(probability),
            "uncertainty": float(uncertainty),
            "error": int(target != prediction),
        }
        for target, probability, uncertainty, prediction in zip(
            y, test.malignant_probability, test.uncertainty, test.predicted_class, strict=True
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
    pooled_errors = sum(
        int(row["n"]) - int(round(float(row["accuracy"]) * int(row["n"]))) for row in metrics_rows
    )
    pooled_fn = sum(int(row["false_negatives"]) for row in metrics_rows)
    pooled_fp = sum(int(row["false_positives"]) for row in metrics_rows)
    automatic_n = sum(int(row["full_automatic_count"]) for row in metrics_rows)
    automatic_errors = sum(
        int(round(float(row["full_selective_error_rate"]) * int(row["full_automatic_count"])))
        for row in metrics_rows
    )
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
        "pooled_case_metrics": pooled,
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
        ],
    }
    (output / "metrics.json").write_text(
        json.dumps(_to_jsonable(metrics_json), indent=2), encoding="utf-8"
    )
    logger.info("Wrote 30-split results to %s", output)
    return output
