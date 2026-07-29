use pyo3::prelude::*;

#[pymodule]
mod subsetmatrix_rs {
    use numpy::ndarray::{Array2, Array3};
    use numpy::{IntoPyArray, PyArray2, PyArray3};
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    /// Gosper's hack: next integer with the same number of set bits.
    fn gosper_next(mask: u128) -> u128 {
        let c = mask & mask.wrapping_neg();
        let r = mask + c;
        (((r ^ mask) >> 2) / c) | r
    }

    /// Decode a mask into its set bit positions (ascending), i.e. the
    /// member indices of the subset it represents.
    fn mask_to_indices(mask: u128, k: usize) -> Vec<usize> {
        let mut m = mask;
        let mut out = Vec::with_capacity(k);
        while m != 0 {
            let low = m & m.wrapping_neg();
            out.push(low.trailing_zeros() as usize);
            m ^= low;
        }
        out
    }

    /// Multiplicative binomial coefficient, used only to pre-size the
    /// output Vec before generation.
    fn comb(n: usize, k: usize) -> usize {
        let k = k.min(n - k);
        let mut result: usize = 1;
        for i in 0..k {
            result = result * (n - i) / (i + 1);
        }
        result
    }

    #[pyfunction]
    fn combinations_indices(n: usize, k: usize) -> PyResult<Vec<Vec<usize>>> {
        if k == 0 || k > n {
            return Err(PyValueError::new_err(format!(
                "k must satisfy 0 < k <= n. Received k={k}, n={n}."
            )));
        }

        let count = comb(n, k);
        let mut out = Vec::with_capacity(count);

        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;

        while mask < limit {
            out.push(mask_to_indices(mask, k));
            mask = gosper_next(mask);
        }

        Ok(out)
    }

    /// Dense membership matrix, built and filled entirely in Rust: one
    /// pre-allocated buffer (all zero), one write per (subset, member) pair
    /// directly into its row slice, ONE conversion back to Python (a numpy
    /// array wrapping the buffer) instead of one per subset. This is the
    /// fix for what combinations_indices's per-subset Vec<Vec<usize>> ->
    /// Python-list conversion was paying for.
    #[pyfunction]
    fn generate_matrix<'py>(
        py: Python<'py>,
        n: usize,
        k_values: Vec<usize>,
    ) -> PyResult<Bound<'py, PyArray2<u8>>> {
        for &k in &k_values {
            if k == 0 || k > n {
                return Err(PyValueError::new_err(format!(
                    "k must satisfy 0 < k <= n. Received k={k}, n={n}."
                )));
            }
        }

        let total_rows: usize = k_values.iter().map(|&k| comb(n, k)).sum();
        let mut flat = vec![0u8; total_rows * n];

        let mut row = 0usize;
        for &k in &k_values {
            let limit: u128 = 1u128 << n;
            let mut mask: u128 = (1u128 << k) - 1;
            while mask < limit {
                let base = row * n;
                let mut m = mask;
                while m != 0 {
                    let low = m & m.wrapping_neg();
                    let j = low.trailing_zeros() as usize;
                    flat[base + j] = 1;
                    m ^= low;
                }
                mask = gosper_next(mask);
                row += 1;
            }
        }

        let arr = Array2::from_shape_vec((total_rows, n), flat)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(arr.into_pyarray(py))
    }

    /// Packed index matrix: shape (comb(n,k), k), every column real (no
    /// wasted n-k "off" columns like generate_matrix, no np.nonzero pass
    /// needed downstream). One pre-allocated buffer, one write per member,
    /// ONE conversion back to Python -- the hybrid of generate_matrix's
    /// "write directly into a big buffer" fix and combinations_indices'
    /// "only touch the k real members" shape.
    #[pyfunction]
    fn combinations_indices_array<'py>(
        py: Python<'py>,
        n: usize,
        k: usize,
    ) -> PyResult<Bound<'py, PyArray2<usize>>> {
        if k == 0 || k > n {
            return Err(PyValueError::new_err(format!(
                "k must satisfy 0 < k <= n. Received k={k}, n={n}."
            )));
        }

        let count = comb(n, k);
        let mut flat = vec![0usize; count * k];

        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;
        let mut row = 0usize;
        while mask < limit {
            let base = row * k;
            let mut m = mask;
            let mut col = 0usize;
            while m != 0 {
                let low = m & m.wrapping_neg();
                flat[base + col] = low.trailing_zeros() as usize;
                col += 1;
                m ^= low;
            }
            mask = gosper_next(mask);
            row += 1;
        }

        let arr = Array2::from_shape_vec((count, k), flat)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(arr.into_pyarray(py))
    }

    /// Floats-only fused path: generation AND the [X[j], Y[j]] lookup happen
    /// in the same Rust pass, straight into one pre-allocated (count, k, 2)
    /// f64 buffer -- no intermediate index structure, no second Python-side
    /// assembly loop. This is the numbers_only=True path: X/Y must already
    /// be numeric, in exchange for skipping the marshal-then-reassemble
    /// round trip that the index-only approach always pays somewhere.
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

    /// Experiment: hand-build each tuple/list via the raw CPython C API
    /// (pyo3::ffi), the same calls itertools' own C source uses internally
    /// (PyTuple_New/PyTuple_SetItem, PyList_New/PyList_SetItem), bypassing
    /// PyO3's generic/automatic Vec<Vec<T>>->Python conversion entirely.
    /// This is the "what if we hand-tune object construction like C/itertools
    /// does" test -- answers how much of combinations_indices's slowdown was
    /// PyO3's convenience-layer tax vs something more fundamental.
    #[pyfunction]
    fn combinations_indices_hand_built<'py>(
        py: Python<'py>,
        n: usize,
        k: usize,
    ) -> PyResult<Bound<'py, PyAny>> {
        use pyo3::ffi;

        if k == 0 || k > n {
            return Err(PyValueError::new_err(format!(
                "k must satisfy 0 < k <= n. Received k={k}, n={n}."
            )));
        }

        let count = comb(n, k);

        unsafe {
            let list_ptr = ffi::PyList_New(count as ffi::Py_ssize_t);
            if list_ptr.is_null() {
                return Err(PyErr::fetch(py));
            }

            let limit: u128 = 1u128 << n;
            let mut mask: u128 = (1u128 << k) - 1;
            let mut row: ffi::Py_ssize_t = 0;

            while mask < limit {
                let tuple_ptr = ffi::PyTuple_New(k as ffi::Py_ssize_t);
                if tuple_ptr.is_null() {
                    ffi::Py_DECREF(list_ptr);
                    return Err(PyErr::fetch(py));
                }

                let mut m = mask;
                let mut col: ffi::Py_ssize_t = 0;
                while m != 0 {
                    let low = m & m.wrapping_neg();
                    let j = low.trailing_zeros() as usize;
                    let item = ffi::PyLong_FromSize_t(j);
                    // PyTuple_SetItem steals the reference to item, same as
                    // itertoolsmodule.c's own PyTuple_SET_ITEM usage.
                    ffi::PyTuple_SetItem(tuple_ptr, col, item);
                    col += 1;
                    m ^= low;
                }

                // PyList_SetItem steals the reference to tuple_ptr.
                ffi::PyList_SetItem(list_ptr, row, tuple_ptr);
                mask = gosper_next(mask);
                row += 1;
            }

            Ok(Bound::from_owned_ptr(py, list_ptr))
        }
    }

    /// Diagnostic only, not part of the plan's contract: walks the exact
    /// same mask loop but discards the result instead of decoding/returning
    /// it, to isolate pure generation cost from Python-object marshalling
    /// cost. Remove once the mechanism behind Phase 1's numbers is understood.
    #[pyfunction]
    fn _count_combinations(n: usize, k: usize) -> usize {
        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;
        let mut count: usize = 0;
        while mask < limit {
            count += 1;
            mask = gosper_next(mask);
        }
        count
    }

    /// Diagnostic only: same as combinations_indices but skips
    /// mask_to_indices entirely -- isolates the bit-decode step's cost.
    #[pyfunction]
    fn _generate_masks_only(n: usize, k: usize) -> Vec<u64> {
        let limit: u128 = 1u128 << n;
        let mut mask: u128 = (1u128 << k) - 1;
        let count = comb(n, k);
        let mut out = Vec::with_capacity(count);
        while mask < limit {
            out.push(mask as u64);
            mask = gosper_next(mask);
        }
        out
    }
}
