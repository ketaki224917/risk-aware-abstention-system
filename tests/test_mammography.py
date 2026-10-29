import numpy as np
import pytest

from raa.data import stratified_split
from raa.mammography import (
    FEATURE_NAMES,
    explain_mammography_case,
    load_mammographic_data,
    load_mammography_artifact,
    predict_mammography_case,
)
from raa.risk.policy import DecisionLevel


def _mode(values):
    present = values[np.isfinite(values)]
    labels, counts = np.unique(present, return_counts=True)
    return float(labels[np.argmax(counts)])


def test_public_dataset_schema_counts_and_target_mapping():
    data = load_mammographic_data()
    assert data.features.shape == (961, 4)
    assert FEATURE_NAMES == ("Age", "Shape", "Margin", "Density")
    assert int(np.sum(data.targets == 0)) == 445
    assert int(np.sum(data.targets == 1)) == 516


def test_saved_preprocessing_statistics_are_training_only():
    data = load_mammographic_data()
    split = stratified_split(data.targets, seed=42)
    train = data.features[split.train]
    artifact = load_mammography_artifact()
    expected = [float(np.nanmedian(train[:, 0]))]
    expected.extend(_mode(train[:, index]) for index in (1, 2, 3))
    assert np.allclose(artifact.reference_values, expected)
    assert artifact.dataset_sha256
    assert len(artifact.validation_risks) == len(split.validation)


def test_full_and_partial_inputs_run_actual_pipeline_with_sensible_routes():
    artifact = load_mammography_artifact()
    full = {"Age": 43, "Shape": 1, "Margin": 1, "Density": 3}
    incomplete = {"Age": 58, "Shape": 4, "Margin": None, "Density": 1}
    full_record = predict_mammography_case(full, artifact)
    partial_record = predict_mammography_case(incomplete, artifact)
    explanation = explain_mammography_case(full, full_record, artifact)
    assert full_record.predicted_label == "benign"
    assert full_record.measured_feature_count == 4
    assert full_record.estimated_feature_count == 0
    assert partial_record.level is DecisionLevel.HUMAN_REVIEW
    assert partial_record.measured_feature_count == 3
    assert partial_record.estimated_feature_count == 1
    assert partial_record.risk >= 0
    assert any("one-field comparison" in line for line in explanation)
    assert any("not a calibrated chance" in line for line in explanation)


def test_out_of_range_age_and_invalid_report_values_are_handled():
    artifact = load_mammography_artifact()
    out_of_range = predict_mammography_case(
        {"Age": 110, "Shape": 4, "Margin": 5, "Density": 1}, artifact
    )
    assert any("outside the range" in warning for warning in out_of_range.input_warnings)
    with pytest.raises(ValueError, match="age from 1 to 120"):
        predict_mammography_case({"Age": 121, "Shape": 4, "Margin": 5, "Density": 1}, artifact)
    with pytest.raises(ValueError, match="Shape does not match"):
        predict_mammography_case({"Age": 58, "Shape": 8, "Margin": 5, "Density": 1}, artifact)


def test_model_inference_does_not_write_user_inputs(tmp_path):
    artifact = load_mammography_artifact()
    before = set(tmp_path.iterdir())
    predict_mammography_case({"Age": 43, "Shape": 1, "Margin": 1, "Density": 3}, artifact)
    assert set(tmp_path.iterdir()) == before
