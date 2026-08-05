"""Benchmark subsetmatrix_rs (the PyO3 native extension) against
itertools.combinations, for the full fused generate+lookup output.

v0.2: the crate is squeezer-only (combinations_values, numeric X/Y fused
into one pass -- see rust/subsetmatrix_rs/src/lib.rs and going_4_rust.md
for why the bare index-generation variants were cut). There is no more
"generation only" benchmark to run separately -- generation and the
X[j]/Y[j] lookup are the same Rust pass now, so end-to-end is the only
number that means anything for this function.

Run with:
    .\\.venv\\Scripts\\python.exe benchmarks\\bench_subsetmatrix_rs.py
"""
import sys
import os
from itertools import combinations

sys.path.insert(0, os.path.dirname(__file__))
from bench_generate_matrix import itertools_get_subsets, time_it  # noqa: E402

from subsetmatrix.native_backend import get_subsets_native

# Overrides bench_generate_matrix's REPEATS=5: this file benchmarks only
# the native squeezer against itertools (no ObservationSet/OOP comparison
# here), and 5 reps was too few to trust a single ratio number against.
REPEATS = 25


def check_correctness():
    print("=" * 72)
    print("correctness: get_subsets_native vs itertools_get_subsets")
    print("=" * 72)
    for n in (1, 5, 8, 12):
        X = [float(i) for i in range(1, n + 1)]
        Y = [float(i) for i in range(n)]
        for k in range(1, n + 1):
            got_by_k = get_subsets_native(X, Y, k)
            got = {
                tuple(sorted(tuple(pair) for pair in subset))
                for subset in got_by_k[0]
            }
            want = {
                tuple(sorted((X[j], Y[j]) for j in combo))
                for combo in combinations(range(n), k)
            }
            assert got == want, f"MISMATCH n={n} k={k}: got {len(got)} want {len(want)}"
    print("all match, n=1..12, all valid k")
    print()


def bench_end_to_end():
    print("=" * 72)
    print(f"get_subsets_native (Rust-backed squeezer) vs itertools_get_subsets -- {REPEATS} reps, min-of-N")
    print("=" * 72)
    header = (
        f"{'n':>4} {'k':>4} {'subsets':>10} {'itertools (s)':>14} "
        f"{'native raw (s)':>15} {'raw ratio':>10} "
        f"{'native tolist (s)':>18} {'tolist ratio':>13}"
    )
    print(header)
    print("-" * len(header))

    n = 20
    Y = [float(i) for i in range(n)]
    X = [float(i) for i in range(1, n + 1)]
    for k in (14, 15, 16):
        rows = len(list(combinations(range(n), k)))
        t_iter = time_it(itertools_get_subsets, X, Y, [k], repeats=REPEATS)
        t_raw = time_it(get_subsets_native, X, Y, k, False, repeats=REPEATS)
        t_typed = time_it(get_subsets_native, X, Y, k, True, repeats=REPEATS)
        raw_ratio = t_iter / t_raw if t_raw else float("inf")
        typed_ratio = t_iter / t_typed if t_typed else float("inf")
        print(
            f"{n:>4} {k:>4} {rows:>10} {t_iter:>14.6f} "
            f"{t_raw:>15.6f} {raw_ratio:>9.2f}x "
            f"{t_typed:>18.6f} {typed_ratio:>12.2f}x"
        )
    print()
    print(
        "raw = python_typed=False (returns the numpy array as-is); "
        "tolist = python_typed=True, the default (converts to native Python "
        "floats via .tolist() before returning). Both compared only against "
        "itertools_get_subsets -- no ObservationSet/OOP path in this file."
    )


if __name__ == "__main__":
    check_correctness()
    bench_end_to_end()
