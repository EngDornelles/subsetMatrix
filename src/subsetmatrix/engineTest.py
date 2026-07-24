import numpy as np
import numpy.typing as npt
from math import comb
from typing import Iterator

def iter_k_masks(n: int, k: int) -> Iterator[int]:
    """Generator yielding subsets with the same ammount
of points (k) to the limit of observations on the set."""
    if not 0 < k <= n:
        raise ValueError("K must satisfy 0 < k <= n")
    limit = (1 << n) # assuming n = 3, we would have 1 -> 2 -> 4 -> 8, thus the limit is 8
    mask = (1 << k) - 1 # assuming k = 2, first k would be 1 -> 2 -> 4, 4 - 1 = 3

    while mask < limit:
        yield mask

        # Gosper's hack: next integer with the same number of set bits, implying subsets of the same size
        c = mask & -mask
        r = mask + c
        mask = (((r ^ mask) >> 2) // c) | r

def cardinality(mask: int) -> int:
    """Useful if you're getting a mask outside of context and needs to know where it belongs."""
    return mask.bit_count()

def generateMatrix(n:int, K:list=[]) -> npt.NDArray[np.uint32]:
    """The matrix won't follow the cardinal order of growth, but the k-sized groups."""
    if not K:
        K = list(range(2, n + 1)) # skip singletons (k=1); include the full set (k=n)
    if n < 3:
        raise ValueError("The number of observations should be > 2.")
    if n > 20:
        raise ValueError("Dense uint32 generation is temporarily capped at n <=20")

    total_rows = sum(comb(n, k) for k in K) # sized to whatever K actually requests, not the full 2**n - 2 span
    matr = np.empty((total_rows, n), dtype=np.uint32)
    bits = np.arange(n, dtype=np.uint32)
    row_start = 0
    for k in K:
        # mask generation stays a plain-Python loop (cheap); the mask -> row
        # expansion is done ONCE per k-group via broadcasting instead of once
        # per row, since numpy's per-call dispatch overhead otherwise dwarfs
        # the actual work on rows this small.
        count = comb(n, k)
        masks = np.fromiter(iter_k_masks(n, k), dtype=np.uint32, count=count)
        matr[row_start:row_start + count] = (masks[:, None] >> bits[None, :]) & 1
        row_start += count
    return matr


# if __name__ == "__main__":
#     generateMatrix(3)
