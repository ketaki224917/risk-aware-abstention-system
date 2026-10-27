import numpy as np

from raa.inference import synthetic_shift_case


def test_paper_stress_shift_is_reproducible_signed_and_clipped():
    row = np.ones(30)
    std = np.ones(30)
    first, indices = synthetic_shift_case(row, std)
    second, second_indices = synthetic_shift_case(row, std)

    assert indices == second_indices
    assert len(indices) == 8
    assert np.array_equal(first, second)
    assert np.count_nonzero(first != row) == 8
    assert np.all(first >= 0)
    assert set(first[list(indices)]) == {0.0, 4.0}
