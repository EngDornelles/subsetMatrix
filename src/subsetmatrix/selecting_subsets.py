import numpy as np
import numpy.typing as npt
from math import comb
from operator import index

def total_window_size(k_values:list[int], n:int) -> int:
    """Calculates the window size for a list of k values. Mainly for array building purposes."""
    if not k_values:
        raise ValueError("k_values cannot be empty.")
    return sum(comb(n, k) for k in k_values)

def validate_k(k: int, n: int) -> int:
    """Validates k, and normalizes it in cases like np.int64(3), against an n-observation matrix."""
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

        k_values = [validate_k(x, n) for x in k]
        return sorted(set(k_values))

    return [validate_k(k, n)]

def extract_k_window(
    matrix: npt.NDArray[np.uint32],
    k: int | list[int],
) -> npt.NDArray[np.uint32]:
    """
    Extract one or more k-sized subset groups from a generated subset matrix.

    If k is a list, groups are returned in ascending k order.
    """
    if matrix.ndim != 2:
        raise ValueError("matrix must be a 2D array filled with integers.")

    n = matrix.shape[1]
    k_values = normalize_k_values(k, n)
    window_size = total_window_size(k_values, n)
    base = np.empty((window_size, n), dtype=matrix.dtype)
    current_row = 0
    for i in k_values:
        start = sum(comb(n, j) for j in range(1, i))
        size = comb(n, i)
        end = start + size

        base[current_row: current_row + size] = matrix[start:end]
        current_row += size

    return base
