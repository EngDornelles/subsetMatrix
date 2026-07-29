"""Benchmark subsetmatrix_rs (the PyO3 native extension) against
itertools.combinations, both for raw index generation and for the
full assembled [[X,Y],...]-per-subset output.

Run with:
    .\\.venv\\Scripts\\python.exe benchmarks\\bench_subsetmatrix_rs.py
"""
import sys
import os
import timeit
from itertools import combinations

sys.path.insert(0, os.path.dirname(__file__))
from bench_generate_matrix import itertools_get_subsets, time_it, REPEATS  # noqa: E402

import subsetmatrix_rs
from subsetmatrix.native_backend import get_subsets_native


def check_correctness():
    print("=" * 72)
    print("correctness: combinations_indices vs itertools.combinations")
    print("=" * 72)
    for n in (1, 5, 8, 12, 20):
        for k in range(1, n + 1):
            got = {tuple(sorted(r)) for r in subsetmatrix_rs.combinations_indices(n, k)}
            want = set(combinations(range(n), k))
            assert got == want, f"MISMATCH n={n} k={k}: got {len(got)} want {len(want)}"
    print("all match, n=1..20, all valid k")
    print()


def bench_generation_only():
    print("=" * 72)
    print("combinations_indices (Rust) vs itertools.combinations -- generation only")
    print("=" * 72)
    header = f"{'n':>4} {'k':>4} {'subsets':>10} {'rust (s)':>14} {'itertools (s)':>14} {'ratio':>8}"
    print(header)
    print("-" * len(header))

    n = 20
    for k in (14, 15, 16):
        rows = len(list(combinations(range(n), k)))
        t_rust = time_it(subsetmatrix_rs.combinations_indices, n, k, repeats=REPEATS)
        t_iter = time_it(lambda: list(combinations(range(n), k)), repeats=REPEATS)
        ratio = t_iter / t_rust if t_rust else float("inf")
        print(f"{n:>4} {k:>4} {rows:>10} {t_rust:>14.6f} {t_iter:>14.6f} {ratio:>7.2f}x")
    print()


def bench_end_to_end():
    print("=" * 72)
    print("get_subsets_native (Rust-backed) vs itertools_get_subsets -- full assembled output")
    print("=" * 72)
    header = f"{'n':>4} {'k':>4} {'subsets':>10} {'native (s)':>14} {'itertools (s)':>14} {'ratio':>8}"
    print(header)
    print("-" * len(header))

    n = 20
    Y = list(range(n))
    X = list(range(1, n + 1))
    for k in (14, 15, 16):
        rows = len(list(combinations(range(n), k)))
        t_native = time_it(get_subsets_native, X, Y, k, repeats=REPEATS)
        t_iter = time_it(itertools_get_subsets, X, Y, [k], repeats=REPEATS)
        ratio = t_iter / t_native if t_native else float("inf")
        print(f"{n:>4} {k:>4} {rows:>10} {t_native:>14.6f} {t_iter:>14.6f} {ratio:>7.2f}x")
    print()


if __name__ == "__main__":
    check_correctness()
    bench_generation_only()
    bench_end_to_end()
