# selecting_subsets.py

from math import comb
from operator import index

import numpy as np
import numpy.typing as npt


def validate_k(k: int, n: int) -> int:
    """Validate and normalize k against an n-observation matrix."""
    if isinstance(k, bool):
        raise TypeError(f"k must be an integer, not bool. Received {k}.")

    try:
        k = index(k)
    except TypeError as exc:
        raise TypeError(f"k must be an integer. Received {k}.") from exc

    if not 0 < k < n:
        raise ValueError(f"k must satisfy 0 < k < n. Received k={k}, n={n}.")

    return k


def normalize_k_values(k: int | list[int], n: int) -> list[int]:
    """Normalize k input into a sorted list of valid integer k values."""
    if isinstance(k, list):
        if not k:
            raise ValueError("k cannot be an empty list.")

        k_values = [validate_k(value, n) for value in k]
        return sorted(k_values)

    return [validate_k(k, n)]


def k_group_start(k: int, n: int) -> int:
    """Return the starting row for the k-sized group."""
    k = validate_k(k, n)
    return sum(comb(n, i) for i in range(1, k))


def total_window_size(k_values: list[int], n: int) -> int:
    """Calculate the total row count for a list of k values."""
    if not k_values:
        raise ValueError("k_values cannot be empty.")

    return sum(comb(n, k) for k in k_values)


def extract_k_window(
    matrix: npt.NDArray[np.uint32],
    k: int | list[int],
) -> npt.NDArray[np.uint32]:
    """
    Extract one or more k-sized subset groups from a generated subset matrix.

    If k is a list, groups are returned in ascending k order.
    """
    if matrix.ndim != 2:
        raise ValueError("matrix must be a 2D array.")

    n = matrix.shape[1]
    k_values = normalize_k_values(k, n)

    window_size = total_window_size(k_values, n)
    base = np.empty((window_size, n), dtype=matrix.dtype)

    current_row = 0

    for current_k in k_values:
        start = k_group_start(current_k, n)
        size = comb(n, current_k)
        end = start + size

        base[current_row: current_row + size] = matrix[start:end]
        current_row += size

    return base