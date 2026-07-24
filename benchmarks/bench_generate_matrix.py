"""Benchmark engine.generateMatrix / ObservationSet.get_subsets against
a pure itertools.combinations equivalent.

Run with:
    .\\.venv\\Scripts\\python.exe benchmarks\\bench_generate_matrix.py
"""
import timeit
from itertools import combinations

import numpy as np

from subsetmatrix.engine import generateMatrix
from subsetmatrix.dataset_payload import ObservationSet

REPEATS = 5


def itertools_generate_matrix(n: int, K: list[int]) -> np.ndarray:
    rows = []
    for k in K:
        for combo in combinations(range(n), k):
            row = [0] * n
            for idx in combo:
                row[idx] = 1
            rows.append(row)
    return np.array(rows, dtype=np.uint32)


def itertools_get_subsets(X: list, Y: list, K: list[int]) -> list:
    res = []
    for k in K:
        for combo in combinations(range(len(Y)), k):
            res.append([[X[j], Y[j]] for j in combo])
    return res


def time_it(fn, *args, repeats: int = REPEATS) -> float:
    return min(timeit.repeat(lambda: fn(*args), number=1, repeat=repeats))


def bench_generate_matrix():
    print("=" * 72)
    print("generateMatrix (engine) vs itertools.combinations")
    print("=" * 72)
    header = f"{'n':>4} {'K':>14} {'rows':>8} {'engine (s)':>16} {'itertools (s)':>16} {'ratio':>8}"
    print(header)
    print("-" * len(header))

    cases = [
        (8, list(range(2, 9))),   # default-style full sweep
        (12, list(range(2, 13))),
        (16, list(range(2, 17))),
        (18, [9]),                # single, wide middle k — worst case for a full allocation
        (18, [2]),                # single, narrow k — highlights the old garbage-row bug's waste
        (20, [10]),
    ]

    for n, K in cases:
        rows = sum(len(list(combinations(range(n), k))) for k in K)
        t_engine = time_it(generateMatrix, n, K)
        t_iter = time_it(itertools_generate_matrix, n, K)
        ratio = t_iter / t_engine if t_engine else float("inf")
        k_label = f"{K[0]}..{K[-1]}" if len(K) > 1 else str(K[0])
        print(f"{n:>4} {k_label:>14} {rows:>8} {t_engine:>16.6f} {t_iter:>16.6f} {ratio:>7.2f}x")


def bench_get_subsets():
    print()
    print("=" * 72)
    print("ObservationSet.get_subsets vs itertools.combinations")
    print("=" * 72)
    header = f"{'n':>4} {'K':>14} {'subsets':>8} {'get_subsets (s)':>16} {'itertools (s)':>16} {'ratio':>8}"
    print(header)
    print("-" * len(header))

    cases = [
        (8, list(range(2, 9))),   # k==n (full set) now valid via get_subsets too
        (12, list(range(2, 13))),
        (16, list(range(2, 17))),
        (18, [9]),
        (18, [2]),
    ]

    for n, K in cases:
        Y = list(range(n))
        X = list(range(1, n + 1))
        obs = ObservationSet({"Y": Y, "X": X})
        n_subsets = sum(len(list(combinations(range(n), k))) for k in K)

        t_obs = time_it(obs.get_subsets, K)
        t_iter = time_it(itertools_get_subsets, X, Y, K)
        ratio = t_iter / t_obs if t_obs else float("inf")
        k_label = f"{K[0]}..{K[-1]}" if len(K) > 1 else str(K[0])
        print(f"{n:>4} {k_label:>14} {n_subsets:>8} {t_obs:>16.6f} {t_iter:>16.6f} {ratio:>7.2f}x")


if __name__ == "__main__":
    bench_generate_matrix()
    bench_get_subsets()
