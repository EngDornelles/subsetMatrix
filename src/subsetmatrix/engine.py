import numpy as np
import numpy.typing as npt
from typing import Iterator

def iter_k_masks(n: int, k: int) -> Iterator[int]:
    """Generator yielding subsets with the same ammount
of points (k) to the limit of observations on the set."""
    if not 0 < k < n:
        raise ValueError("K must satisfy 0 < k < n")
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


def generateMatrix(n:int) -> npt.NDArray[np.uint32]:
    """The matrix won't follow the cardinal order of growth, but the k-sized groups."""
    if n < 3:
        raise ValueError("The number of observations should be > 2.")
    if n > 20:
        raise ValueError("Dense uint32 generation is temporarily capped at n <=20")

    matr = np.empty(((1 << n) - 2, n), dtype=np.uint32) # 2**n -2 is due to the fact that empty and full need no calculations.
    bits = np.arange(n, dtype=np.uint32)
    c = 0
    for i in range(1, n):
        gen = iter_k_masks(n, i)
        for j in gen:
            matr[c] = ((np.uint32(j) >> bits) & 1)
            c += 1
    return matr


# if __name__ == "__main__":
#     generateMatrix(3)
