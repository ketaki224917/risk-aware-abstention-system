import copy

import numpy as np

from raa.config import load_config
from raa.data import load_breast_cancer_data, stratified_split
from raa.inference import InferenceContext, predict_case
from raa.pipeline import fit_system


def test_predict_case_returns_the_real_pipeline_record():
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=42)
    config = copy.deepcopy(load_config())
    config["classifier"]["n_estimators"] = 8
    config["uncertainty"]["ensemble_members"] = 3
    config["uncertainty"]["trees_per_member"] = 4
    config["anomaly"]["n_estimators"] = 8
    system = fit_system(data.features, data.targets, split.train, split.validation, config, seed=42)
    context = InferenceContext(
        system,
        data.feature_names,
        tuple(data.features[split.train].min(axis=0)),
        tuple(data.features[split.train].max(axis=0)),
    )
    row = data.features[split.test[0]]

    result = predict_case(row, np.ones(row.size, dtype=bool), context=context)
    expected = system.predict(row.reshape(1, -1))[0]

    assert result.predicted_class == expected.predicted_class
    assert result.risk == expected.risk
    assert result.level == expected.level
    assert result.measured_feature_count == 30
    assert result.estimated_feature_count == 0
