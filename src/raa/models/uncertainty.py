"""Bootstrap Random Forest ensemble disagreement signal."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.ensemble import RandomForestClassifier

FloatArray = NDArray[np.float64]


@dataclass
class BootstrapUncertainty:
    """Bootstrap ensemble; disagreement is a signal, not calibrated error risk."""

    members: list[RandomForestClassifier]
    seed: int

    @classmethod
    def fit(
        cls,
        features: ArrayLike,
        targets: ArrayLike,
        *,
        members: int = 30,
        trees_per_member: int = 50,
        seed: int = 0,
        class_weight: str | dict[int, float] | None = None,
    ) -> BootstrapUncertainty:
        """Fit one smaller Random Forest per bootstrap sample of training rows."""
        x = np.asarray(features)
        y = np.asarray(targets)
        rng = np.random.default_rng(seed)
        fitted: list[RandomForestClassifier] = []
        for index in range(members):
            sample = rng.integers(0, len(y), size=len(y))
            model = RandomForestClassifier(
                n_estimators=trees_per_member,
                random_state=seed + index,
                n_jobs=1,
                class_weight=class_weight,
            )
            model.fit(x[sample], y[sample])
            fitted.append(model)
        return cls(members=fitted, seed=seed)

    def member_probabilities(self, features: ArrayLike) -> FloatArray:
        """Return malignant probabilities for each ensemble member and row."""
        x = np.asarray(features)
        probabilities: list[NDArray[np.float64]] = []
        for model in self.members:
            positions = np.flatnonzero(np.asarray(model.classes_) == 0)
            if positions.size != 1:
                raise ValueError("Bootstrap sample omitted the malignant class")
            probabilities.append(model.predict_proba(x)[:, int(positions[0])])
        return np.vstack(probabilities)

    def disagreement(self, features: ArrayLike) -> FloatArray:
        """Return population standard deviation of member P(malignant)."""
        return np.asarray(np.std(self.member_probabilities(features), axis=0), dtype=np.float64)
