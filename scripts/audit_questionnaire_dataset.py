"""Check whether the public Duke BRCA table supports the proposed questionnaire."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score

from raa.config import load_config
from raa.data import stratified_split
from raa.pipeline import fit_system

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Fit the full RAA pipeline on TRAIN/validation and report held-out test evidence."""
    raw = np.loadtxt(ROOT / "data" / "brca.txt", dtype=np.int64)
    features = raw[:, 4:10].astype(np.float64)
    # The project's class convention is 0=cancer outcome, 1=no cancer outcome.
    targets = (1 - raw[:, 1]).astype(np.int64)
    seed = 42
    split = stratified_split(targets, seed=seed)
    config = load_config()
    config["classifier"]["class_weight"] = "balanced_subsample"
    system = fit_system(features, targets, split.train, split.validation, config, seed=seed)
    batch = system.predict_batch(features[split.test])
    test_targets = targets[split.test]
    matrix = confusion_matrix(test_targets, batch.predicted_class, labels=(0, 1))
    metrics = {
        "run_id": "duke-brca-questionnaire-seed-42",
        "dataset_rows": int(len(targets)),
        "cancer_outcome_rows": int((targets == 0).sum()),
        "no_cancer_outcome_rows": int((targets == 1).sum()),
        "train_rows": int(len(split.train)),
        "validation_rows": int(len(split.validation)),
        "test_rows": int(len(split.test)),
        "test_cancer_outcomes": int((test_targets == 0).sum()),
        "test_no_cancer_outcomes": int((test_targets == 1).sum()),
        "test_confusion_matrix_labels": ["cancer within 12 months", "no cancer within 12 months"],
        "test_confusion_matrix": matrix.tolist(),
        "test_cancer_sensitivity": float(matrix[0, 0] / max(int((test_targets == 0).sum()), 1)),
        "test_specificity": float(matrix[1, 1] / max(int((test_targets == 1).sum()), 1)),
        "test_roc_auc": float(roc_auc_score(test_targets == 0, batch.malignant_probability)),
        "automatic_test_cases": int(np.count_nonzero(batch.level == "Automatic")),
        "assisted_test_cases": int(np.count_nonzero(batch.level == "Assisted")),
        "human_review_test_cases": int(np.count_nonzero(batch.level == "Human Review")),
        "classifier": "RandomForestClassifier(class_weight=balanced_subsample, n_estimators=300)",
        "policy": "RAA pipeline; thresholds fitted on validation at p70/p90",
        "seed": seed,
        "warning": (
            "One historical screening cohort and one held-out split; not clinical validation."
        ),
    }
    output = ROOT / "results" / "clinical_candidate_audit" / "metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    LOGGER.warning("Questionnaire candidate metrics (not for clinical use): %s", metrics)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
