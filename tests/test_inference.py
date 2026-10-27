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


def test_guided_feature_selection_uses_only_top_mean_importances():
    from raa.inference import select_guided_features

    names = (
        "mean radius",
        "mean texture",
        "mean perimeter",
        "mean area",
        "mean smoothness",
        "mean compactness",
        "mean concavity",
        "mean concave points",
        "mean symmetry",
        "mean fractal dimension",
        "worst radius",
    )
    importance = np.array([0.5, 0.3, 0.7, 0.6, 0.1, 0.2, 0.8, 0.9, 0.05, 0.01, 99.0])

    selected = select_guided_features(names, importance)

    assert selected == (
        "mean concave points",
        "mean concavity",
        "mean perimeter",
        "mean area",
        "mean radius",
        "mean texture",
    )
    assert "worst radius" not in selected


def test_partial_case_uses_train_fitted_imputer_and_reports_estimation():
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=42)
    config = copy.deepcopy(load_config())
    config["classifier"]["n_estimators"] = 8
    config["uncertainty"]["ensemble_members"] = 3
    config["uncertainty"]["trees_per_member"] = 4
    config["anomaly"]["n_estimators"] = 8
    system = fit_system(data.features, data.targets, split.train, split.validation, config, seed=42)
    x_train = data.features[split.train]
    context = InferenceContext.fit_from_training(system, x_train, data.feature_names, neighbors=5)
    assert np.array_equal(context.imputer._fit_X, x_train)
    assert np.array_equal(context.training_min, x_train.min(axis=0))
    assert np.array_equal(context.training_max, x_train.max(axis=0))

    names = (
        "mean concave points",
        "mean concavity",
        "mean radius",
        "mean perimeter",
        "mean area",
        "mean compactness",
    )
    row = np.full(len(data.feature_names), np.nan)
    mask = np.zeros(len(data.feature_names), dtype=bool)
    test_row = data.features[split.test[0]]
    for name in names:
        index = data.feature_names.index(name)
        row[index] = test_row[index]
        mask[index] = True

    result = predict_case(row, mask, context=context)

    assert result.measured_feature_count == 6
    assert result.estimated_feature_count == 24
    assert 0 <= result.risk <= 1
    assert any("TRAIN-only KNN imputer" in warning for warning in result.input_warnings)
