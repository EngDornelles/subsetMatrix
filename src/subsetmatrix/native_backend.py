"""Glue between the Rust `subsetmatrix_rs` extension and this package.

v0.2: numeric-only squeezer. `subsetmatrix_rs.combinations_values` does
generation AND the X[j]/Y[j] lookup in one fused Rust pass, writing
straight into one (comb(n,k_val), k_val, 2) float64 numpy array per k
value -- no intermediate index structure, no Python-side assembly loop.
X/Y must already be numeric (the Multinterp use case).

The prior index-only path (`subsetmatrix_rs.combinations_indices`,
type-agnostic X/Y, no fused lookup) is retired as of this version --
see `going_4_rust.md` and `logs/mvp_changelog.md` for why it never beat
this fused path and was cut rather than kept as a slower fallback.

python_typed=True (default): converts each returned array to a plain
Python list of floats via `.tolist()` before handing it back, for
interop with code that expects native Python numbers rather than a
numpy array. python_typed=False skips that conversion and returns the
raw array.
"""

from subsetmatrix.selecting_subsets import normalize_k_values
import subsetmatrix_rs


def get_subsets_native(
    X: list,
    Y: list,
    k: int | list[int],
    python_typed: bool = True,
) -> list[list]:
    n = len(Y)
    k_values = normalize_k_values(k, n)

    x = [float(v) for v in X]
    y = [float(v) for v in Y]
    arrays = [subsetmatrix_rs.combinations_values(k_val, x, y) for k_val in k_values]
    if python_typed:
        return [arr.tolist() for arr in arrays]
    return arrays
