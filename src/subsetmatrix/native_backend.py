"""Glue between the Rust `subsetmatrix_rs` extension and this package.

Default path: `subsetmatrix_rs.combinations_indices(n, k)` only ever
generates index tuples -- it never touches X or Y, so it never has to
deal with X's type (numbers, strings, dates, whatever). Assembly into
`[[X[j], Y[j]], ...]`-per-subset stays here in Python, on the same
lines already benchmarked as fast enough in `benchmarks/bench_generate_matrix.py`.

numbers_only=True path: for numeric X/Y (the Multinterp use case),
`subsetmatrix_rs.combinations_values` does generation AND the X[j]/Y[j]
lookup in one fused Rust pass, returning one (comb(n,k_val), k_val, 2)
float64 numpy array per k value -- no intermediate index structure, no
second Python-side assembly loop. Trades the index-only architecture's
type-agnosticism for numeric-only speed, deliberately, only when asked.

python_typed=True (default, only relevant when numbers_only=True):
converts each returned array to a plain Python list of floats via
`.tolist()` before handing it back, for interop with code that expects
native Python numbers rather than a numpy array. python_typed=False
skips that conversion and returns the raw array.
"""

from subsetmatrix.selecting_subsets import normalize_k_values
import subsetmatrix_rs


def get_subsets_native(
    X: list,
    Y: list,
    k: int | list[int],
    numbers_only: bool = False,
    python_typed: bool = True,
) -> list[list[list]] | list:
    n = len(Y)
    k_values = normalize_k_values(k, n)

    if numbers_only:
        x = [float(v) for v in X]
        y = [float(v) for v in Y]
        arrays = [subsetmatrix_rs.combinations_values(k_val, x, y) for k_val in k_values]
        if python_typed:
            return [arr.tolist() for arr in arrays]
        return arrays

    res = []
    for k_val in k_values:
        for combo in subsetmatrix_rs.combinations_indices(n, k_val):
            res.append([[X[j], Y[j]] for j in combo])
    return res
