"""Command-line entry points for reproduction and focused evaluations."""

from __future__ import annotations

import argparse
import csv
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from raa.config import load_config
from raa.data import load_breast_cancer_data, stratified_split
from raa.eval.explanation_eval import evaluate_explanation_checker
from raa.eval.metrics import (
    binary_classification_metrics,
    expected_calibration_error,
    malignant_brier_score,
    selective_metrics,
)
from raa.eval.run_experiments import run_experiments
from raa.eval.stress_test import run_stress_test
from raa.explain.checker import check_explanation
from raa.explain.templates import generate_explanation
from raa.pipeline import fit_system
from raa.viz.plots import plot_reliability, plot_result_artifacts

logger = logging.getLogger("raa")


def _run_id(value: str | None) -> str:
    return value or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_explanation_results(output: Path, config: dict[str, Any]) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    data = load_breast_cancer_data()
    seed = int(config["data"]["main_split_seed"])
    split = stratified_split(
        data.targets,
        seed=seed,
        test_fraction=float(config["data"]["test_fraction"]),
        validation_fraction_of_remainder=float(config["data"]["validation_fraction_of_remainder"]),
    )
    system = fit_system(
        data.features, data.targets, split.train, split.validation, config, seed=seed
    )
    test_x, test_y = data.features[split.test], data.targets[split.test]
    batch = system.predict_batch(test_x)
    records = system.predict(test_x)
    metrics = evaluate_explanation_checker(records)
    (output / "explanation_checker.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    rows = [{"fault_type": name, **values} for name, values in metrics["per_fault"].items()]
    with (output / "explanation_faults.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    record_rows = []
    for row_index, (case_id, target, record) in enumerate(
        zip(split.test, test_y, records, strict=True)
    ):
        explanation = generate_explanation(record)
        record_rows.append(
            {
                "test_row": row_index,
                "dataset_row": int(case_id),
                "true_class": int(target),
                "predicted_class": record.predicted_label,
                "confidence": record.confidence,
                "uncertainty": record.uncertainty,
                "anomaly": record.anomaly,
                "consequence": record.consequence,
                "risk": record.risk,
                "decision_level": record.level.value,
                "referral_reason": record.referral_reason,
                "explanation": explanation,
                "checker_passed": check_explanation(record, explanation).passed,
            }
        )
    with (output / "main_split_records.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(record_rows[0]))
        writer.writeheader()
        writer.writerows(record_rows)
    baseline = binary_classification_metrics(test_y, batch.predicted_class)
    selected = selective_metrics(test_y, batch.predicted_class, batch.level)
    automatic = batch.level == "Automatic"
    selected["false_negative_routed_away_rate"] = (
        selected["false_negatives_routed_away"] / baseline["false_negatives"]
        if baseline["false_negatives"]
        else None
    )
    (output.parent / "main_split_metrics.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "test_cases": int(len(test_y)),
                "baseline": baseline,
                "risk_aware": selected,
                "ece_all": expected_calibration_error(
                    test_y,
                    batch.malignant_probability,
                    bins=int(config["evaluation"]["reliability_bins"]),
                ),
                "ece_automatic": expected_calibration_error(
                    test_y[automatic],
                    batch.malignant_probability[automatic],
                    bins=int(config["evaluation"]["reliability_bins"]),
                ),
                "brier_score_all": malignant_brier_score(test_y, batch.malignant_probability),
                "thresholds": {
                    "automatic": system.thresholds.automatic_max,
                    "assisted": system.thresholds.assisted_max,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics


def _add_parser(subparsers: Any, name: str, help_text: str) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("--config", default=None, help="YAML configuration file")
    parser.add_argument("--run-id", default=None, help="Optional fixed output run ID")
    return parser


def main() -> None:
    """Run one of the supported experiment groups."""
    parser = argparse.ArgumentParser(prog="raa")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_parser(subparsers, "reproduce", "Run all experiments and write tables/figures")
    _add_parser(subparsers, "ablate", "Run the 30-split experiment and ablations")
    _add_parser(subparsers, "stress", "Run synthetic feature-shift stress test")
    _add_parser(subparsers, "explain-eval", "Evaluate explanation checker fault detection")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    config = load_config(args.config)
    run_id = _run_id(args.run_id)
    run_dir = Path("results/runs") / run_id
    if args.command in {"reproduce", "ablate"}:
        output = run_experiments(config, run_id=run_id)
        if args.command == "reproduce":
            run_stress_test(config, output / "stress")
            _write_explanation_results(output / "explanations", config)
            diagnostic_rows = []
            with (output / "diagnostics.csv").open(newline="", encoding="utf-8") as stream:
                diagnostic_rows = list(csv.DictReader(stream))
            plot_reliability(
                [int(row["target"]) for row in diagnostic_rows],
                [float(row["malignant_probability"]) for row in diagnostic_rows],
                int(config["evaluation"]["reliability_bins"]),
                output / "reliability.png",
            )
            plot_result_artifacts(output)
        logger.info("Results are in %s", output)
    elif args.command == "stress":
        run_stress_test(config, run_dir / "stress")
    elif args.command == "explain-eval":
        result = _write_explanation_results(run_dir / "explanations")
        logger.info("Explanation fault detection rate: %.3f", result["overall_detection_rate"])


if __name__ == "__main__":
    main()
