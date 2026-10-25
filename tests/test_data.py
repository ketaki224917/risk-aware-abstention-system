import numpy as np

from raa.data import assert_no_overlap, load_breast_cancer_data, stratified_split


def test_dataset_and_split_have_expected_dimensions_and_sizes():
    data = load_breast_cancer_data()
    assert data.features.shape == (569, 30)
    assert np.bincount(data.targets).tolist() == [212, 357]
    split = stratified_split(data.targets, seed=42)
    assert (len(split.train), len(split.validation), len(split.test)) == (341, 114, 114)
    assert_no_overlap(split)
    for indices in (split.train, split.validation, split.test):
        assert abs(np.mean(data.targets[indices] == 0) - np.mean(data.targets == 0)) < 0.03


def test_invalid_split_fractions_are_rejected():
    data = load_breast_cancer_data()
    try:
        stratified_split(data.targets, seed=1, test_fraction=1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid test fraction was accepted")
