"""Prediction consequence values; values are design assumptions, not clinical costs."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def consequence_score(
    predicted_class: ArrayLike,
    *,
    predicted_malignant: float = 0.4,
    predicted_benign: float = 1.0,
) -> NDArray[np.float64]:
    """Assign greater design consequence to a benign prediction as specified."""
    labels = np.asarray(predicted_class)
    if not 0 <= predicted_malignant <= 1 or not 0 <= predicted_benign <= 1:
        raise ValueError("Consequence values must be in [0, 1]")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Class labels must be 0 (malignant) or 1 (benign)")
    return np.where(labels == 0, predicted_malignant, predicted_benign).astype(np.float64)
