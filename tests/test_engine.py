import pytest
import numpy as np
from itertools import combinations
from subsetmatrix.engine import generateMatrix, iter_k_masks

# ---
# Generation tests (default K)
# ---

def test_generate_matrix_default_k_skips_singletons_includes_full_set():
    matrix = generateMatrix(4)
    row_sums = matrix.sum(axis=1).tolist()

    # k=1 (singletons) excluded, k=2..4 included, k=n (full set) included
    assert row_sums == [
        2, 2, 2, 2, 2, 2,  # k = 2
        3, 3, 3, 3,        # k = 3
        4,                 # k = 4 (full set)
    ]

def test_generate_matrix_default_k_shape():
    # sum(comb(4,2), comb(4,3), comb(4,4)) = 6 + 4 + 1 = 11
    matrix = generateMatrix(4)
    assert matrix.shape == (11, 4)

# ---
# Explicit K tests
# ---

def test_generate_matrix_explicit_k_shape_matches_requested_k_only():
    matrix = generateMatrix(4, [2])
    assert matrix.shape == (6, 4)
    assert matrix.sum(axis=1).tolist() == [2, 2, 2, 2, 2, 2]

def test_generate_matrix_explicit_k_no_garbage_rows():
    # regression test: matrix used to be allocated at full (2**n - 2) size
    # regardless of K, leaving uninitialized rows past the actually-written
    # count when K was a strict subset of all possible k values.
    matrix = generateMatrix(5, [2])
    expected_rows = {frozenset(np.flatnonzero(row).tolist()) for row in matrix}
    expected = {frozenset(c) for c in combinations(range(5), 2)}
    assert expected_rows == expected

def test_generate_matrix_explicit_full_set_k_equals_n():
    matrix = generateMatrix(4, [4])
    assert matrix.shape == (1, 4)
    np.testing.assert_array_equal(matrix, np.array([[1, 1, 1, 1]], dtype=np.uint32))

def test_generate_matrix_multiple_k_values():
    matrix = generateMatrix(4, [2, 4])
    assert matrix.shape == (7, 4)
    assert matrix.sum(axis=1).tolist() == [2, 2, 2, 2, 2, 2, 4]

# ---
# iter_k_masks bounds tests
# ---

def test_iter_k_masks_rejects_k_zero():
    with pytest.raises(ValueError):
        list(iter_k_masks(5, 0))

def test_iter_k_masks_rejects_k_greater_than_n():
    with pytest.raises(ValueError):
        list(iter_k_masks(5, 6))

def test_iter_k_masks_accepts_k_equal_n():
    masks = list(iter_k_masks(4, 4))
    assert masks == [0b1111]

# ---
# Cross-check against itertools.combinations
# ---

@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_generate_matrix_matches_itertools_combinations(n):
    K = list(range(2, n + 1))
    matrix = generateMatrix(n, K)

    got = {frozenset(np.flatnonzero(row).tolist()) for row in matrix}
    expected = {
        frozenset(c)
        for k in K
        for c in combinations(range(n), k)
    }
    assert got == expected
    assert len(got) == matrix.shape[0]  # no duplicate/garbage rows

# ---
# N validation tests
# ---

def test_generate_matrix_rejects_small_n():
    with pytest.raises(ValueError):
        generateMatrix(2)
