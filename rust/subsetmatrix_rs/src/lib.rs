use pyo3::prelude::*;

/// Squeezer-only surface (v0.2): this crate shipped five functions through
/// the `functional` branch's Rust exploration (see `going_4_rust.md` and
/// `logs/mvp_changelog.md` for the full trail and benchmark numbers). Only
/// `combinations_values` ever beat `itertools.combinations` end-to-end --
/// every index/matrix-returning variant (`generate_matrix`,
/// `combinations_indices`, `combinations_indices_array`,
/// `combinations_indices_hand_built`) converged back to itertools' own cost
/// or slightly behind it, because handing back individually-addressable
/// Python objects is the actual bottleneck, not generation. v0.2 narrows the
/// crate to the one function that won and pushes it further, instead of
/// carrying four dead-weight variants that were never wired into
/// `native_backend.py`'s real path and were never part of the published
/// PyPI wheel (this crate isn't built into the `subsetmatrix` distribution).
#[pymodule]
mod subsetmatrix_rs {
    use numpy::prelude::*;
    use numpy::PyArray3;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    /// Gosper's hack: next integer with the same number of set bits.
    fn gosper_next(mask: u128) -> u128 {
        let c = mask & mask.wrapping_neg();
        let r = mask + c;
        (((r ^ mask) >> 2) / c) | r
    }

    /// Multiplicative binomial coefficient, used only to pre-size the
    /// output array before generation.
    fn comb(n: usize, k: usize) -> usize {
        let k = k.min(n - k);
        let mut result: usize = 1;
        for i in 0..k {
            result = result * (n - i) / (i + 1);
        }
        result
    }

    /// Floats-only fused path: generation AND the [X[j], Y[j]] lookup happen
    /// in the same Rust pass, writing straight into a (count, k, 2) f64
    /// numpy array as each mask's set bits are decoded -- no intermediate
    /// index structure, no intermediate Rust-side Vec, no second Python-side
    /// assembly loop, and no wasted zero-initialization: the array is
    /// allocated uninitialized and every one of its cells is written
    /// exactly once by this loop before Python ever sees it. This is the
    /// only path that beat itertools end-to-end in benchmarking (see
    /// `going_4_rust.md` #7.3) -- numeric X/Y only, the Multinterp use case,
    /// in exchange for never materializing a single per-subset Python
    /// object.
    #[pyfunction]
    fn combinations_values<'py>(
        py: Python<'py>,
        k: usize,
        x: Vec<f64>,
        y: Vec<f64>,
    ) -> PyResult<Bound<'py, PyArray3<f64>>> {
        let n = x.len();
        if y.len() != n {
            return Err(PyValueError::new_err(format!(
                "x and y must be the same length. x:{n} y:{}",
                y.len()
            )));
        }
        if k == 0 || k > n {
            return Err(PyValueError::new_err(format!(
                "k must satisfy 0 < k <= n. Received k={k}, n={n}."
            )));
        }

        let count = comb(n, k);

        // SAFETY: `PyArray3::new` returns uninitialized memory (see its
        // docs: forming a `&`/`&mut` over an element before it's written is
        // UB, so this writes through `uget_raw(..).write(..)` only, never
        // through a slice/array view). Every one of the count*k*2 cells is
        // written exactly once below: the Gosper walk visits exactly
        // `count` masks, each with exactly `k` set bits by construction
        // (starting mask is `(1<<k)-1`), so the (row, col, 0|1) writes
        // cover the whole array with no gaps and no double-writes before
        // `arr` is returned to Python.
        let arr = unsafe { PyArray3::<f64>::new(py, (count, k, 2), false) };

        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;
        let mut row = 0usize;
        while mask < limit {
            let mut m = mask;
            let mut col = 0usize;
            while m != 0 {
                let low = m & m.wrapping_neg();
                let j = low.trailing_zeros() as usize;
                unsafe {
                    arr.uget_raw([row, col, 0]).write(x[j]);
                    arr.uget_raw([row, col, 1]).write(y[j]);
                }
                col += 1;
                m ^= low;
            }
            mask = gosper_next(mask);
            row += 1;
        }

        Ok(arr)
    }
}
