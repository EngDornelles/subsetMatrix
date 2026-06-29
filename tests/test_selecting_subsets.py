import numpy as np
import pytest

from subsetmatrix.engine import generateMatrix
from subsetmatrix.selecting_subsets import extract_k_window


def test_extract_k_window_single_k():
    matrix = generateMatrix(4)
    result = extract_k_window(matrix, 2)

    assert result.shape == (6, 4)
    assert result.sum(axis=1).tolist() == [2, 2, 2, 2, 2, 2]


def test_extract_k_window_sorted_list():
    matrix = generateMatrix(4)
    result = extract_k_window(matrix, [3, 1])

    assert result.shape == (8, 4)
    assert result[:4].sum(axis=1).tolist() == [1, 1, 1, 1]
    assert result[4:].sum(axis=1).tolist() == [3, 3, 3, 3]

def test_extract_k_window_deduplicates_k_values():
    matrix = generateMatrix(4)
    result = extract_k_window(matrix, [2, 2])

    assert result.shape == (6, 4)
    assert result.sum(axis=1).tolist() == [2, 2, 2, 2, 2, 2]

def test_extract_k_window_rejects_bool():
    matrix = generateMatrix(4)

    with pytest.raises(TypeError):
        extract_k_window(matrix, True)


def test_extract_k_window_accepts_np_int():
    matrix = generateMatrix(4)
    result = extract_k_window(matrix, np.int64(2))

    assert result.shape == (6, 4)


def test_extract_k_window_rejects_zero():
    matrix = generateMatrix(4)

    with pytest.raises(ValueError):
        extract_k_window(matrix, 0)