"""Isolation Forest anomaly score, with larger values meaning more unusual."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.ensemble import IsolationForest


def fit_anomaly_detector(
    features: ArrayLike,
    *,
    n_estimators: int = 200,
    random_state: int = 0,
) -> IsolationForest:
    """Fit Isolation Forest on training rows only."""
    detector = IsolationForest(
        n_estimators=n_estimators,
        contamination="auto",
        random_state=random_state,
        n_jobs=1,
    )
    detector.fit(features)
    return detector


def anomaly_score(detector: IsolationForest, features: ArrayLike) -> NDArray[np.float64]:
    """Negate sklearn's normality score so larger values indicate anomalies."""
    return np.asarray(-detector.decision_function(features), dtype=np.float64)
