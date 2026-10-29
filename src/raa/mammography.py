"""Leakage-safe UCI Mammographic Mass model and RAA inference."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from numpy.typing import NDArray
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from raa.config import load_config
from raa.data import stratified_split
from raa.explain.record import DecisionRecord
from raa.pipeline import DecisionSystem, fit_system
from raa.risk.policy import DecisionLevel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "mammographic_masses.data"
DEFAULT_ARTIFACT_DIR = PROJECT_ROOT / "results" / "mammographic_mass"
RAW_DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/mammographic-masses/mammographic_masses.data"
FEATURE_NAMES = ("Age", "Shape", "Margin", "Density")
SHAPE_CODES = {"Round": 1, "Oval": 2, "Lobulated": 3, "Irregular": 4}
MARGIN_CODES = {
    "Circumscribed (well-defined)": 1,
    "Microlobulated (small bumps)": 2,
    "Obscured (partly hidden)": 3,
    "Ill-defined (unclear edge)": 4,
    "Spiculated (spiky edge)": 5,
}
DENSITY_CODES = {
    "High": 1,
    "Similar to nearby tissue": 2,
    "Low": 3,
    "Mostly fat-containing": 4,
}
CATEGORY_CODES = [[1, 2, 3, 4], [1, 2, 3, 4, 5], [1, 2, 3, 4]]
ARTIFACT_VERSION = 1
ARTIFACT_NAME = "model_bundle.joblib"


@dataclass(frozen=True)
class MammographicData:
    """Dataset inputs and target encoded as 0 malignant / 1 benign."""

    features: NDArray[np.float64]
    targets: NDArray[np.int64]


@dataclass(frozen=True)
class MammographyArtifact:
    """Saved preprocessing and decision pipeline learned from train/validation only."""

    artifact_version: int
    run_seed: int
    feature_names: tuple[str, ...]
    transformed_feature_names: tuple[str, ...]
    preprocessor: ColumnTransformer
    system: DecisionSystem
    train_min: tuple[float, ...]
    train_max: tuple[float, ...]
    reference_values: tuple[float, ...]
    validation_risks: tuple[float, ...]
    dataset_sha256: str


def load_mammographic_data(path: str | Path = DEFAULT_DATA_PATH) -> MammographicData:
    """Read UCI's six-column data; omit BI-RADS and map severity to project class order."""
    rows: list[list[float]] = []
    labels: list[int] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        for row_number, row in enumerate(csv.reader(stream), start=1):
            if not row:
                continue
            if len(row) != 6:
                raise ValueError(f"Dataset row {row_number} must have six fields")
            fields = [np.nan if value.strip() == "?" else float(value) for value in row]
            if fields[5] not in (0, 1):
                raise ValueError(f"Dataset row {row_number} has invalid severity")
            rows.append(fields[1:5])  # Age, Shape, Margin, Density. BI-RADS is excluded.
            labels.append(0 if int(fields[5]) == 1 else 1)
    if not rows:
        raise ValueError("Mammographic Mass dataset is empty")
    return MammographicData(np.asarray(rows, dtype=np.float64), np.asarray(labels, dtype=np.int64))


def _make_preprocessor() -> ColumnTransformer:
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encode",
                OneHotEncoder(
                    categories=CATEGORY_CODES,
                    handle_unknown="ignore",
                    sparse_output=False,
                    dtype=np.float64,
                ),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("age", SimpleImputer(strategy="median"), [0]),
            ("findings", categorical, [1, 2, 3]),
        ],
        sparse_threshold=0.0,
        verbose_feature_names_out=False,
    )


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_mammography_artifact(
    output_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    *,
    dataset_path: str | Path = DEFAULT_DATA_PATH,
) -> MammographyArtifact:
    """Fit once offline, calculate held-out metrics and save the bundle."""
    config = load_config()
    data = load_mammographic_data(dataset_path)
    seed = int(config["data"]["main_split_seed"])
    split = stratified_split(data.targets, seed=seed)
    preprocessor = _make_preprocessor()
    preprocessor.fit(data.features[split.train])
    features = np.asarray(preprocessor.transform(data.features), dtype=np.float64)
    system = fit_system(features, data.targets, split.train, split.validation, config, seed=seed)
    validation_records = system.predict(features[split.validation])
    names = tuple(str(name) for name in preprocessor.get_feature_names_out())
    artifact = MammographyArtifact(
        ARTIFACT_VERSION,
        seed,
        FEATURE_NAMES,
        names,
        preprocessor,
        system,
        tuple(float(x) for x in np.nanmin(data.features[split.train], axis=0)),
        tuple(float(x) for x in np.nanmax(data.features[split.train], axis=0)),
        _training_reference_values(preprocessor),
        tuple(float(record.risk) for record in validation_records),
        _sha256(dataset_path),
    )
    test_records = system.predict(features[split.test])
    y = data.targets[split.test]
    predicted = np.asarray([record.predicted_class for record in test_records])
    score = np.asarray([record.malignant_probability for record in test_records])
    level = np.asarray([record.level.value for record in test_records], dtype=object)
    actual_malignant = y == 0
    predicted_malignant = predicted == 0
    false_negatives = actual_malignant & ~predicted_malignant
    automatic = level == DecisionLevel.AUTOMATIC.value
    metrics: dict[str, Any] = {
        "run_id": "mammographic-mass-seed-42-v1",
        "dataset": "UCI Mammographic Mass",
        "dataset_sha256": artifact.dataset_sha256,
        "seed": seed,
        "rows": len(data.targets),
        "class_counts": {
            "malignant": int(np.sum(data.targets == 0)),
            "benign": int(np.sum(data.targets == 1)),
        },
        "split_rows": {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        },
        "test": {
            "accuracy": float(accuracy_score(y, predicted)),
            "roc_auc_malignant": float(roc_auc_score(actual_malignant, score)),
            "sensitivity_malignant": float(recall_score(actual_malignant, predicted_malignant)),
            "specificity_benign": float(recall_score(~actual_malignant, ~predicted_malignant)),
            "decision_counts": {
                name: int(np.sum(level == name))
                for name in ("Automatic", "Assisted", "Human Review")
            },
            "automatic_coverage": float(np.mean(automatic)),
            "automatic_error_rate": float(np.mean(predicted[automatic] != y[automatic])),
            "malignant_false_negatives": int(false_negatives.sum()),
            "malignant_false_negatives_routed_away": int(np.sum(false_negatives & ~automatic)),
        },
        "model_features": list(FEATURE_NAMES),
        "encoded_features": list(names),
        "preprocessing": "TRAIN-only median/mode imputation and one-hot encoding",
        "scikit_learn_version": sklearn.__version__,
    }
    _write_artifacts(artifact, metrics, output_dir)
    return artifact


def _training_reference_values(preprocessor: ColumnTransformer) -> tuple[float, ...]:
    age = float(preprocessor.named_transformers_["age"].statistics_[0])
    findings = preprocessor.named_transformers_["findings"]
    categories = tuple(float(value) for value in findings.named_steps["imputer"].statistics_)
    return (age, *categories)


def _write_artifacts(
    artifact: MammographyArtifact, metrics: dict[str, Any], output_dir: str | Path
) -> None:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, directory / ARTIFACT_NAME, compress=3)
    (directory / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "artifact_version": artifact.artifact_version,
        "artifact": ARTIFACT_NAME,
        "dataset": "UCI Mammographic Mass",
        "source_url": RAW_DATA_URL,
        "doi": "10.24432/C53K6Z",
        "license": "CC BY 4.0",
        "excluded_input": "BI-RADS; UCI identifies it as non-predictive.",
        "model_features": list(FEATURE_NAMES),
        "dataset_sha256": artifact.dataset_sha256,
        "metrics_file": "metrics.json",
        "scikit_learn_version": sklearn.__version__,
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_mammography_artifact(
    path: str | Path | None = None, *, dataset_path: str | Path = DEFAULT_DATA_PATH
) -> MammographyArtifact:
    """Load the saved bundle; validate schema and data hash without retraining."""
    bundle_path = Path(path) if path else DEFAULT_ARTIFACT_DIR / ARTIFACT_NAME
    if not bundle_path.is_file():
        raise FileNotFoundError(
            f"Saved model missing: {bundle_path}. Run make mammography-artifact."
        )
    artifact = joblib.load(bundle_path)
    if (
        not isinstance(artifact, MammographyArtifact)
        or artifact.artifact_version != ARTIFACT_VERSION
    ):
        raise ValueError(f"Unsupported mammography model bundle: {bundle_path}")
    if artifact.feature_names != FEATURE_NAMES or artifact.dataset_sha256 != _sha256(dataset_path):
        raise ValueError("Saved mammogram model does not match its data or input schema")
    return artifact


def predict_mammography_case(
    values: dict[str, float | int | None], artifact: MammographyArtifact
) -> DecisionRecord:
    """Run inputs through classifier, uncertainty, anomaly, consequence, risk and policy."""
    raw = np.asarray(
        [values.get(name) if values.get(name) is not None else np.nan for name in FEATURE_NAMES],
        dtype=np.float64,
    )
    measured = np.isfinite(raw)
    if not measured[0] or not 1 <= raw[0] <= 120:
        raise ValueError("Enter an age from 1 to 120 years")
    for index, allowed in enumerate(CATEGORY_CODES, start=1):
        if measured[index] and raw[index] not in allowed:
            raise ValueError(f"{FEATURE_NAMES[index]} does not match a report option")
    transformed = np.asarray(artifact.preprocessor.transform(raw.reshape(1, -1)), dtype=np.float64)
    record = artifact.system.predict(transformed)[0]
    missing = int((~measured).sum())
    warnings: list[str] = []
    if raw[0] < artifact.train_min[0] or raw[0] > artifact.train_max[0]:
        warnings.append("Age is outside the range observed in the training records.")
    level, reason = record.level, record.referral_reason
    if missing:
        warnings.append(
            f"{missing} report field(s) marked Not sure were estimated from TRAIN-only values. "
            "The model was scored, but incomplete findings require Human Review."
        )
        level, reason = DecisionLevel.HUMAN_REVIEW, "incomplete mammogram report details"
    return replace(
        record,
        level=level,
        referral_reason=reason,
        measured_feature_count=int(measured.sum()),
        estimated_feature_count=missing,
        input_warnings=tuple(warnings),
    )


def explain_mammography_case(
    values: dict[str, float | int | None],
    record: DecisionRecord,
    artifact: MammographyArtifact,
) -> tuple[str, ...]:
    """Describe local score sensitivity to replacing each value with a TRAIN reference."""
    raw = np.asarray(
        [values.get(name) if values.get(name) is not None else np.nan for name in FEATURE_NAMES],
        dtype=np.float64,
    )

    def malignant_score(row: NDArray[np.float64]) -> float:
        transformed = np.asarray(artifact.preprocessor.transform(row.reshape(1, -1)))
        classes = np.asarray(artifact.system.classifier.classes_)
        malignant_index = int(np.flatnonzero(classes == 0)[0])
        return float(artifact.system.classifier.predict_proba(transformed)[0, malignant_index])

    current = malignant_score(raw)
    changes: list[tuple[float, int]] = []
    for index, reference in enumerate(artifact.reference_values):
        alternative = raw.copy()
        alternative[index] = reference
        changes.append((abs(current - malignant_score(alternative)), index))
    changes.sort(key=lambda item: (-item[0], item[1]))
    lines = []
    for difference, index in changes[:3]:
        name = FEATURE_NAMES[index]
        if difference < 0.005:
            lines.append(f"{name}: a one-field comparison barely changed the model score.")
        else:
            alternative = raw.copy()
            alternative[index] = artifact.reference_values[index]
            direction = (
                "toward malignant" if current > malignant_score(alternative) else "toward benign"
            )
            lines.append(
                f"{name}: this value moved the malignant-class score {difference * 100:.1f} "
                f"points {direction} versus a common training value."
            )
    lines.append(
        "These are model-sensitivity checks, not causes. "
        "The score is not a calibrated chance of cancer."
    )
    if record.estimated_feature_count:
        lines.append("Some report fields were estimated, so the route is Human Review.")
    return tuple(lines)
