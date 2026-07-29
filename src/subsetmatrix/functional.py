import numpy as np
from math import comb
from typing import Iterator

# Ideas: Persisting the data should be optional. Multithreading as well

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

def get_subsets(*Y, K:list|tuple=[], X:list|tuple=[], memory_only:bool=False) -> None|tuple:
    # validating Y
    Y = list(Y) # if not isinstance(Y, list|tuple) else Y # later on I can fix this to be more inclusive
    n = len(Y)
    if memory_only:
        total_rows = sum(comb(n, k) for k in K)
        res = np.empty((total_rows, n), dtype=np.uint32)
        bits = np.arange(n, dtype=np.uint32)
        row_start = 0

    # starting the loop
    for k in K:
        count = comb(n, k)
        masks = np.fromiter(iter_k_masks(n, k), dtype=np.uint32, count=count)
        res[row_start:row_start + count] = (masks[:, None] >> bits[None, :]) & 1
        if memory_only:
            row_start += count

    if memory_only:
        return res
    return None
