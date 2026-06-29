import pytest
import numpy as np
from subsetmatrix.engine import generateMatrix

# ---
# Generation tests
# ---

def test_generate_matrix_n3_shape():
    matrix = generateMatrix(3)
    assert matrix.shape == (6, 3)

def test_generate_matrix_n4_shape():
    matrix = generateMatrix(4)
    assert matrix.shape == (14, 4)

def test_generate_matrix_n20_shape():
    matrix = generateMatrix(20)
    assert matrix.shape == ((1 << 20) - 2, 20)

# ---
# Output format tests
# ---

def test_generate_matrix_n3_exact_output():
    expected = np.array(
        [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
        ],
        dtype=np.uint32,
    )

    result = generateMatrix(3)

    np.testing.assert_array_equal(result, expected)

# ---
# Cardinality grouping tests
# ---

def test_generate_matrix_grouped_by_cardinality():
    matrix = generateMatrix(4)
    row_sums = matrix.sum(axis=1).tolist()

    assert row_sums == [
        1, 1, 1, 1,        # k = 1
        2, 2, 2, 2, 2, 2,  # k = 2
        3, 3, 3, 3,        # k = 3
    ]

# ---
# No empty or full rows test
# ---

def test_generate_matrix_excludes_empty_and_full_rows():
    matrix = generateMatrix(5)

    row_sums = matrix.sum(axis=1)

    assert row_sums.min() > 0
    assert row_sums.max() < 5

# ---
# N validation tests
# ---

def test_generate_matrix_rejects_small_n():
    with pytest.raises(ValueError):
        generateMatrix(2)
