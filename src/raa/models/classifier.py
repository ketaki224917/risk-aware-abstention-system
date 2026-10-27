"""Random Forest classifier for malignant probability estimation."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.ensemble import RandomForestClassifier

FloatArray = NDArray[np.float64]


def fit_classifier(
    features: ArrayLike,
    targets: ArrayLike,
    *,
    n_estimators: int = 300,
    random_state: int = 0,
    class_weight: str | dict[int, float] | None = None,
) -> RandomForestClassifier:
    """Fit a deterministic Random Forest on training data only."""
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,
        class_weight=class_weight,
    )
    model.fit(features, targets)
    return model


def malignant_probability(model: RandomForestClassifier, features: ArrayLike) -> FloatArray:
    """Return class-0 (malignant) probability independent of class order."""
    classes = np.asarray(model.classes_)
    positions = np.flatnonzero(classes == 0)
    if positions.size != 1:
        raise ValueError("Classifier must be fitted with the malignant class encoded as 0")
    return np.asarray(model.predict_proba(features)[:, int(positions[0])], dtype=np.float64)
