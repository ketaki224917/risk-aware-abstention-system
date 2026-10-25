"""Wisconsin Diagnostic Breast Cancer data access and leakage-safe splits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class BreastCancerData:
    """Dataset matrix and its source labels (0 malignant, 1 benign)."""

    features: FloatArray
    targets: IntArray
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class DataSplit:
    """Index-only 60/20/20 split; indexing is explicit for overlap checks."""

    train: IntArray
    validation: IntArray
    test: IntArray


def load_breast_cancer_data() -> BreastCancerData:
    """Load sklearn's Wisconsin Diagnostic Breast Cancer dataset."""
    source = load_breast_cancer()
    return BreastCancerData(
        features=np.asarray(source.data, dtype=np.float64),
        targets=np.asarray(source.target, dtype=np.int64),
        feature_names=tuple(str(name) for name in source.feature_names),
    )


def stratified_split(
    targets: IntArray,
    *,
    seed: int,
    test_fraction: float = 0.20,
    validation_fraction_of_remainder: float = 0.25,
) -> DataSplit:
    """Create a stratified split with 60% train, 20% validation, 20% test."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    if not 0 < validation_fraction_of_remainder < 1:
        raise ValueError("validation fraction must be between 0 and 1")
    indices = np.arange(targets.shape[0], dtype=np.int64)
    train_validation, test = train_test_split(
        indices,
        test_size=test_fraction,
        random_state=seed,
        stratify=targets,
    )
    train, validation = train_test_split(
        train_validation,
        test_size=validation_fraction_of_remainder,
        random_state=seed + 1,
        stratify=targets[train_validation],
    )
    split = DataSplit(
        train=np.asarray(train, dtype=np.int64),
        validation=np.asarray(validation, dtype=np.int64),
        test=np.asarray(test, dtype=np.int64),
    )
    assert_no_overlap(split)
    return split


def assert_no_overlap(split: DataSplit) -> None:
    """Raise when any sample index appears in more than one partition."""
    groups = (split.train, split.validation, split.test)
    if any(np.intersect1d(groups[i], groups[j]).size for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Train, validation, and test partitions overlap")
