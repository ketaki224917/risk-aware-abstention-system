"""Build/load the cached seed-42 demo artifact; loading never trains models."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn

from raa.config import load_config
from raa.data import DataSplit, load_breast_cancer_data, stratified_split
from raa.inference import InferenceContext, select_guided_features
from raa.pipeline import DecisionSystem, fit_system

from .examples import ExampleCase, select_example_cases

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEMO_DIR = PROJECT_ROOT / "results" / "demo"
DEFAULT_RUN_DIR = PROJECT_ROOT / "results" / "runs" / "raa-20261026-paper-aligned-01"
ARTIFACT_NAME = "model_bundle.joblib"
ARTIFACT_VERSION = 1


@dataclass(frozen=True)
class DemoArtifact:
    """Pre-fitted model, train-only preprocessing, and held-out case catalog."""

    artifact_version: int
    run_seed: int
    feature_names: tuple[str, ...]
    guided_features: tuple[str, ...]
    feature_importances: tuple[float, ...]
    test_indices: tuple[int, ...]
    system: DecisionSystem
    inference_context: InferenceContext
    examples: dict[str, ExampleCase]


def build_demo_artifact(output_dir: str | Path = DEFAULT_DEMO_DIR) -> DemoArtifact:
    """Fit once offline on TRAIN/validation and write the reusable bundle/results tables."""
    config = load_config()
    data = load_breast_cancer_data()
    seed = int(config["data"]["main_split_seed"])
    split = stratified_split(data.targets, seed=seed)
    system = fit_system(
        data.features, data.targets, split.train, split.validation, config, seed=seed
    )
    x_train = data.features[split.train]
    context = InferenceContext.fit_from_training(system, x_train, data.feature_names, neighbors=5)
    importances = np.asarray(system.classifier.feature_importances_, dtype=float)
    guided = select_guided_features(data.feature_names, importances, count=6)
    test_records = system.predict(data.features[split.test])
    examples = select_example_cases(data, split, test_records)
    artifact = DemoArtifact(
        artifact_version=ARTIFACT_VERSION,
        run_seed=seed,
        feature_names=data.feature_names,
        guided_features=guided,
        feature_importances=tuple(float(value) for value in importances),
        test_indices=tuple(int(index) for index in split.test),
        system=system,
        inference_context=context,
        examples=examples,
    )
    _write_artifact(artifact, data, split, output_dir)
    return artifact


def load_demo_artifact(path: str | Path | None = None) -> DemoArtifact:
    """Load the committed bundle; raise if absent or incompatible, never fit a model."""
    artifact_path = Path(path) if path is not None else DEFAULT_DEMO_DIR / ARTIFACT_NAME
    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Saved demo model is missing at {artifact_path}. Run `make demo-artifact` once."
        )
    artifact = joblib.load(artifact_path)
    if not isinstance(artifact, DemoArtifact) or artifact.artifact_version != ARTIFACT_VERSION:
        raise ValueError(f"Unsupported RAA demo artifact: {artifact_path}")
    if artifact.feature_names != load_breast_cancer_data().feature_names:
        raise ValueError("Demo artifact feature order does not match the WDBC dataset")
    if artifact.inference_context.system is not artifact.system:
        raise ValueError("Demo artifact does not share its fitted decision system")
    if artifact.inference_context.imputer is None:
        raise ValueError("Demo artifact is missing the train-only partial-feature imputer")
    return artifact


def load_paper_results(run_dir: str | Path = DEFAULT_RUN_DIR) -> dict[str, Any]:
    """Read aggregate numbers for the Why abstain page from the canonical result files."""
    path = Path(run_dir) / "metrics.json"
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_artifact(
    artifact: DemoArtifact, data: Any, split: DataSplit, output_dir: str | Path
) -> None:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, directory / ARTIFACT_NAME, compress=3)

    ranked = sorted(
        enumerate(zip(artifact.feature_names, artifact.feature_importances, strict=True)),
        key=lambda item: (-item[1][1], item[0]),
    )
    with (directory / "feature_importance.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("rank", "feature", "importance", "fit_partition", "split_seed"))
        for rank, (_, (name, value)) in enumerate(ranked, start=1):
            writer.writerow((rank, name, f"{value:.12g}", "train", artifact.run_seed))

    catalog = {
        key: {
            "title": case.title,
            "description": case.description,
            "test_position": case.test_position,
            "dataset_row": case.dataset_row,
        }
        for key, case in artifact.examples.items()
    }
    (directory / "example_cases.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "artifact": ARTIFACT_NAME,
        "dataset": "Wisconsin Diagnostic Breast Cancer (scikit-learn)",
        "run_seed": artifact.run_seed,
        "train_rows": int(len(split.train)),
        "validation_rows": int(len(split.validation)),
        "held_out_test_rows": int(len(split.test)),
        "feature_count": int(data.features.shape[1]),
        "guided_features": list(artifact.guided_features),
        "model": "seed-42 RAA pipeline; fit on TRAIN, policy fit on validation",
        "imputer": "five-neighbor distance-weighted KNN; fit on TRAIN only",
        "scikit_learn_version": sklearn.__version__,
        "example_cases": catalog,
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
