import copy

import numpy as np

from raa.config import load_config
from raa.data import load_breast_cancer_data, stratified_split
from raa.models.consequence import consequence_score
from raa.pipeline import fit_system


def small_config():
    config = copy.deepcopy(load_config())
    config["classifier"]["n_estimators"] = 8
    config["uncertainty"]["ensemble_members"] = 3
    config["uncertainty"]["trees_per_member"] = 4
    config["anomaly"]["n_estimators"] = 8
    return config


def test_consequence_assumption_weights_benign_prediction_more():
    assert consequence_score([0, 1]).tolist() == [0.0, 1.0]


def test_test_partition_cannot_affect_fitted_models_or_validation_thresholds():
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=12)
    config = small_config()
    system_a = fit_system(
        data.features, data.targets, split.train, split.validation, config, seed=12
    )
    changed = data.features.copy()
    changed[split.test] += 100_000
    system_b = fit_system(changed, data.targets, split.train, split.validation, config, seed=12)
    assert system_a.thresholds == system_b.thresholds
    assert system_a.normalizer == system_b.normalizer
    assert system_a.classifier.n_estimators == 8
    records = system_a.predict(data.features[split.test[:3]])
    assert len(records) == 3
    assert all(0 <= record.risk <= 1 for record in records)
    assert np.all(system_a.thresholds.automatic_max <= system_a.thresholds.assisted_max)


def test_train_validation_overlap_is_rejected():
    data = load_breast_cancer_data()
    config = small_config()
    try:
        fit_system(data.features, data.targets, [0, 1, 2], [2, 3], config, seed=0)
    except ValueError as error:
        assert "overlap" in str(error)
    else:
        raise AssertionError("Overlapping train and validation rows were accepted")
