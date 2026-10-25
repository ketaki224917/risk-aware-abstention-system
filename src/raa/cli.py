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
from raa.eval.explanation_eval import evaluate_explanation_checker
from raa.eval.run_experiments import run_experiments
from raa.eval.stress_test import run_stress_test
from raa.viz.plots import plot_reliability, plot_result_artifacts

logger = logging.getLogger("raa")


def _run_id(value: str | None) -> str:
    return value or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_explanation_results(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    metrics = evaluate_explanation_checker()
    (output / "explanation_checker.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    rows = [{"fault_type": name, **values} for name, values in metrics["per_fault"].items()]
    with (output / "explanation_faults.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
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
            _write_explanation_results(output / "explanations")
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
