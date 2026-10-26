"""Leakage-safe training and decision inference."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from raa.explain.record import DecisionRecord
from raa.models.anomaly import anomaly_score, fit_anomaly_detector
from raa.models.classifier import fit_classifier, malignant_probability
from raa.models.consequence import consequence_score
from raa.models.uncertainty import BootstrapUncertainty
from raa.risk.engine import weighted_risk
from raa.risk.normalization import ComponentNormalizer
from raa.risk.policy import DecisionLevel, PolicyThresholds


@dataclass(frozen=True)
class BatchDecisions:
    """Vectorized prediction and routing fields for evaluation."""

    predicted_class: NDArray[np.int64]
    malignant_probability: NDArray[np.float64]
    confidence_risk: NDArray[np.float64]
    uncertainty: NDArray[np.float64]
    anomaly: NDArray[np.float64]
    consequence: NDArray[np.float64]
    risk: NDArray[np.float64]
    level: NDArray[np.object_]


@dataclass
class DecisionSystem:
    """Models and validation-fitted policy state."""

    classifier: RandomForestClassifier
    uncertainty_model: BootstrapUncertainty
    anomaly_scaler: StandardScaler
    anomaly_model: IsolationForest
    normalizer: ComponentNormalizer
    thresholds: PolicyThresholds
    weights: dict[str, float]
    consequence_values: dict[str, float]

    def predict(self, features: ArrayLike) -> tuple[DecisionRecord, ...]:
        """Return immutable structured records for the supplied rows."""
        batch = self.predict_batch(features)
        return tuple(
            DecisionRecord(
                predicted_class=int(batch.predicted_class[i]),
                malignant_probability=float(batch.malignant_probability[i]),
                uncertainty=float(batch.uncertainty[i]),
                anomaly=float(batch.anomaly[i]),
                consequence=float(batch.consequence[i]),
                risk=float(batch.risk[i]),
                level=DecisionLevel(str(batch.level[i])),
                automatic_threshold=self.thresholds.automatic_max,
                assisted_threshold=self.thresholds.assisted_max,
                referral_reason=_referral_reason(
                    float(batch.uncertainty[i]),
                    float(batch.anomaly[i]),
                    float(batch.consequence[i]),
                    DecisionLevel(str(batch.level[i])),
                    self.weights,
                ),
            )
            for i in range(len(batch.predicted_class))
        )

    def predict_batch(self, features: ArrayLike) -> BatchDecisions:
        """Compute predictions and routing; explanation code is not invoked."""
        x = np.asarray(features, dtype=np.float64)
        predicted = np.asarray(self.classifier.predict(x), dtype=np.int64)
        probability = malignant_probability(self.classifier, x)
        uncertainty = self.uncertainty_model.disagreement(x)
        anomaly = self.score_anomaly(x)
        consequence = consequence_score(predicted, **self.consequence_values)
        components = self.normalizer.transform(uncertainty, anomaly, consequence)
        risk = weighted_risk(components, self.weights)
        return BatchDecisions(
            predicted,
            probability,
            1.0 - np.maximum(probability, 1.0 - probability),
            components["uncertainty"],
            components["anomaly"],
            components["consequence"],
            risk,
            self.thresholds.route(risk),
        )

    def score_anomaly(self, features: ArrayLike) -> NDArray[np.float64]:
        """Score rows after the training-fitted anomaly feature standardization."""
        return anomaly_score(self.anomaly_model, self.anomaly_scaler.transform(features))


def fit_system(
    features: ArrayLike,
    targets: ArrayLike,
    train_indices: ArrayLike,
    validation_indices: ArrayLike,
    config: dict,
    *,
    seed: int,
) -> DecisionSystem:
    """Fit models on train rows and risk normalizer/thresholds on validation rows.

    Test data is deliberately not accepted by this function.
    """
    x, y = np.asarray(features, dtype=float), np.asarray(targets, dtype=np.int64)
    train, val = (
        np.asarray(train_indices, dtype=np.int64),
        np.asarray(validation_indices, dtype=np.int64),
    )
    if np.intersect1d(train, val).size:
        raise ValueError("Training and validation indices overlap")
    cc, uc, ac = config["classifier"], config["uncertainty"], config["anomaly"]
    classifier = fit_classifier(
        x[train],
        y[train],
        n_estimators=int(cc["n_estimators"]),
        random_state=seed + int(cc["random_state_offset"]),
    )
    ensemble = BootstrapUncertainty.fit(
        x[train],
        y[train],
        members=int(uc["ensemble_members"]),
        trees_per_member=int(uc["trees_per_member"]),
        seed=seed + int(uc["random_state_offset"]),
    )
    anomaly_scaler = StandardScaler().fit(x[train])
    anomaly_train = anomaly_scaler.transform(x[train])
    detector = fit_anomaly_detector(
        anomaly_train,
        n_estimators=int(ac["n_estimators"]),
        random_state=seed + int(ac["random_state_offset"]),
    )
    vx = x[val]
    vu = ensemble.disagreement(vx)
    va_train = anomaly_score(detector, anomaly_train)
    va = anomaly_score(detector, anomaly_scaler.transform(vx))
    vc = consequence_score(
        classifier.predict(vx),
        **{key: float(value) for key, value in config["consequence"].items()},
    )
    normalizer = ComponentNormalizer.fit(vu, va_train)
    components = normalizer.transform(vu, va, vc)
    weights = {key: float(value) for key, value in config["risk"]["weights"].items()}
    risk = weighted_risk(components, weights)
    pc = config["policy"]
    thresholds = PolicyThresholds.fit(
        risk,
        automatic_percentile=float(pc["automatic_percentile"]),
        assisted_percentile=float(pc["assisted_percentile"]),
    )
    return DecisionSystem(
        classifier,
        ensemble,
        anomaly_scaler,
        detector,
        normalizer,
        thresholds,
        weights,
        {key: float(value) for key, value in config["consequence"].items()},
    )


def _referral_reason(
    uncertainty: float,
    anomaly: float,
    consequence: float,
    level: DecisionLevel,
    weights: dict[str, float],
) -> str:
    """Name the largest weighted risk contributor for referred cases."""
    if level is DecisionLevel.AUTOMATIC:
        return ""
    contributions = {
        "ensemble disagreement (uncertainty)": weights["uncertainty"] * uncertainty,
        "anomaly evidence": weights["anomaly"] * anomaly,
        "the consequence term": weights["consequence"] * consequence,
    }
    return max(contributions, key=contributions.get)
