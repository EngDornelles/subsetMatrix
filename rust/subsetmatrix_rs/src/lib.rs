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
/// crate to the one function that won, instead of carrying four dead-weight
/// variants that were never wired into `native_backend.py`'s real path and
/// were never part of the published PyPI wheel (this crate isn't built
/// into the `subsetmatrix` distribution).
///
/// A follow-up attempt to write directly into an uninitialized numpy array
/// via `PyArray3::new` + per-element `uget_raw(..).write(..)` (skipping the
/// zero-init'd `Vec<f64>` buffer below) was benchmarked head-to-head against
/// this version and measured consistently *slower* (~19-20x itertools vs.
/// this version's ~20-29x, n=20, k=14/15/16, 25 reps, both builds benchmarked
/// back-to-back) -- the per-element stride computation `uget_raw` does for
/// each 3D index apparently costs more than the zero-init + bulk move this
/// version pays instead. Reverted; see `logs/mvp_changelog.md`'s 2026-08-05
/// entries for both the attempt and the revert.
#[pymodule]
mod subsetmatrix_rs {
    use numpy::ndarray::Array3;
    use numpy::{IntoPyArray, PyArray3};
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
    /// in the same Rust pass, straight into one pre-allocated (count, k, 2)
    /// f64 buffer -- no intermediate index structure, no second Python-side
    /// assembly loop. This is the only path that beat itertools end-to-end
    /// in benchmarking (see `going_4_rust.md` #7.3) -- numeric X/Y only, the
    /// Multinterp use case, in exchange for never materializing a single
    /// per-subset Python object.
    ///
    /// The `Vec<f64>` buffer is zero-initialized before being filled, then
    /// moved (not copied) into the returned numpy array via
    /// `into_pyarray`. An uninitialized-array + per-element `uget_raw`
    /// write variant was tried and benchmarked slower than this -- see the
    /// module-level doc comment above.
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
        let mut flat = vec![0f64; count * k * 2];

        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;
        let mut row = 0usize;
        while mask < limit {
            let base = row * k * 2;
            let mut m = mask;
            let mut col = 0usize;
            while m != 0 {
                let low = m & m.wrapping_neg();
                let j = low.trailing_zeros() as usize;
                flat[base + col * 2] = x[j];
                flat[base + col * 2 + 1] = y[j];
                col += 1;
                m ^= low;
            }
            mask = gosper_next(mask);
            row += 1;
        }

        let arr = Array3::from_shape_vec((count, k, 2), flat)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(arr.into_pyarray(py))
    }
}
