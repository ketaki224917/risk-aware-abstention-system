import numpy as np

from raa.risk.engine import weighted_risk
from raa.risk.normalization import ComponentNormalizer
from raa.risk.policy import DecisionLevel, PolicyThresholds


def test_validation_normalization_is_bounded_and_clips_future_values():
    normalizer = ComponentNormalizer.fit([1, 2, 3], [10, 20, 30])
    components = normalizer.transform([0, 2, 4], [0, 20, 40], [0, 0.5, 1])
    assert np.all((components["uncertainty"] >= 0) & (components["uncertainty"] <= 1))
    assert np.all((components["anomaly"] >= 0) & (components["anomaly"] <= 1))
    assert components["uncertainty"].tolist() == [0, 0.5, 1]
    assert components["consequence"].tolist() == [0, 0.5, 1]


def test_weighted_risk_and_policy_boundary_routing():
    components = {
        "uncertainty": np.array([0.0, 1.0]),
        "anomaly": np.array([0.0, 1.0]),
        "consequence": np.array([0.0, 1.0]),
    }
    risk = weighted_risk(components)
    assert risk.tolist() == [0.0, 1.0]
    thresholds = PolicyThresholds(0.2, 0.8)
    levels = thresholds.route([0.2, 0.21, 0.8, 0.81])
    assert levels.tolist() == [
        DecisionLevel.AUTOMATIC,
        DecisionLevel.ASSISTED,
        DecisionLevel.ASSISTED,
        DecisionLevel.HUMAN_REVIEW,
    ]


def test_percentile_thresholds_are_ordered():
    thresholds = PolicyThresholds.fit(np.linspace(0, 1, 101))
    assert thresholds.automatic_max <= thresholds.assisted_max
