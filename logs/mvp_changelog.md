# MVP Changelog

This log tracks notable changes during the pre-1.0 / MVP phase of
`subsetMatrix`. Once the product bumps past MVP, new entries move to
[`CHANGELOG.md`](CHANGELOG.md) and this file is kept as historical
record only.

Format: newest entries at the top.

```markdown
## YYYY-MM-DD — short title

- What changed.
```

---

## 2026-08-05 — combinations_values: uninitialized-array write attempt reverted

- Follow-up to the v0.2.0 entry below. The hardening described there
  (allocate the output numpy array uninitialized via `PyArray3::new`,
  write each value directly via `uget_raw(..).write(..)`, skip the
  zero-init'd `Vec<f64>` buffer entirely) was committed, then tested
  head-to-head against the original zero-init-Vec-then-move
  implementation on Lucas's request, after he flagged the measured ~16x
  itertools ratio as suspiciously low against `going_4_rust.md`'s
  original ~20-37x claim.
- Method: committed the hardened version first (so it wasn't lost),
  temporarily restored the pre-hardening `lib.rs` from commit `17d490a`,
  rebuilt with `maturin develop --release`, benchmarked
  `combinations_values` directly against `itertools` (n=20, k=14/15/16,
  25 reps, min-of-N) with a plain non-numpy itertools baseline (matching
  ObservationSet — this is a `subsetmatrix_rs` internal function, not
  the `ObservationSet` OOP path). Then restored the hardened version and
  ran the identical benchmark back-to-back, same process, same machine
  state, to rule out load/variance as the explanation.
- Result: the **old (zero-init Vec) version was consistently faster**.
  Two back-to-back A/B runs:
  - Old: 29.48x / 27.58x / 19.30x (k=14/15/16)
  - New (hardened): 18.75x / 19.71x / 13.98x (k=14/15/16)
  Confirmed by a third pair of runs through the full
  `bench_subsetmatrix_rs.py` script (25 reps): old version's raw-array
  path lands at 23.42x / 21.45x / 16.00x.
- Diagnosis (not fully isolated, but consistent with the numbers):
  `uget_raw([row, col, 0/1])` computes a stride-based offset via
  `NpyIndex::get_unchecked` on every single element write — two calls
  per decoded member, each recomputing a 3D-index-to-offset
  transformation through the numpy array's stride metadata. The old
  version does the equivalent offset math (`base + col*2`) directly on a
  plain contiguous `Vec<f64>` with no indirection through the array
  abstraction. The per-element stride computation apparently costs more
  than the zero-init + bulk `into_pyarray` move it was meant to save —
  the theory that "avoid storing an intermediate buffer, write directly"
  would be strictly faster didn't hold in practice for this API.
- Action: `combinations_values` reverted to the zero-init-Vec
  implementation. `lib.rs` keeps the trimmed squeezer-only surface from
  the v0.2.0 entry below (that part of the decision is independent of
  this and still holds); only the internal write strategy inside
  `combinations_values` changed back. Doc comments in `lib.rs` updated
  to record the attempt and the measured result, so it isn't retried
  blind. `README.md` softened one sentence that implied a
  write-straight-into-the-final-array claim.
- Verified: `pytest` (82 passed) and `bench_subsetmatrix_rs.py`
  correctness check both pass against the reverted build.

## 2026-08-05 — v0.2.0: Rust crate narrowed to the numeric squeezer

- Lucas's positioning call: SubsetMatrix's native/Rust deliverable narrows
  away from general-purpose subset ergonomics toward one thing done as
  fast as possible — numeric `[X, Y]` subset arrays for downstream engine
  work (Multinterp). Prior broader state (this session's starting point):
  `rust/subsetmatrix_rs/src/lib.rs` had five real functions plus two
  throwaway diagnostics — `combinations_indices`, `generate_matrix`,
  `combinations_indices_array`, `combinations_values`,
  `combinations_indices_hand_built`, `_count_combinations`,
  `_generate_masks_only` — documented in full (including benchmark
  numbers per function) in [`../going_4_rust.md`](../going_4_rust.md) §7.
  Only `combinations_values` ever beat `itertools.combinations`
  end-to-end; the rest converged back to itertools' cost or slightly
  behind it once real Python objects had to come back out.
- `lib.rs` trimmed to `gosper_next`, `comb`, and `combinations_values`
  only. The four retired functions were never wired into
  `native_backend.py`'s real path and were never part of the published
  PyPI wheel (the crate isn't in the wheel's build step at all), so this
  is not a public API change.
- `combinations_values` hardened: previously allocated a zero-initialized
  `Vec<f64>` buffer, wrote into it, then converted to a numpy array
  (`Array3::from_shape_vec` + `into_pyarray`). Now allocates the output
  numpy array directly via `PyArray3::new` (uninitialized) and writes
  each `x[j]`/`y[j]` value straight into it via `uget_raw(..).write(..)`
  as each mask's set bits are decoded — no intermediate Rust-side Vec, no
  zero-init of cells that were always going to be overwritten, no
  separate conversion pass. Every cell is written exactly once (each of
  the `count` masks has exactly `k` set bits by construction), so no
  uninitialized element is ever read or exposed to Python.
- `native_backend.get_subsets_native` simplified: dropped the
  `numbers_only` toggle and the generic index-based branch (which called
  the now-removed `combinations_indices`). The function is numeric-only
  now, matching the trimmed crate.
- `benchmarks/bench_subsetmatrix_rs.py` rewritten against the trimmed
  surface: the old `combinations_indices`-based correctness check and
  "generation only" benchmark are gone (there's no separate generation
  step to isolate anymore — generation and the value lookup are the same
  Rust pass); correctness and benchmarking now go through
  `get_subsets_native` directly. Also fixes a latent bug in the old
  `bench_end_to_end`: it called `get_subsets_native(X, Y, k)` without
  `numbers_only=True`, so it was silently exercising the generic
  `combinations_indices` branch instead of the fused numeric path the
  benchmark's own header claimed to measure.
- `pyproject.toml` and `rust/subsetmatrix_rs/Cargo.toml` bumped to
  0.2.0. This is a version/documentation marker for the positioning
  change, not a PyPI publish — the native crate still isn't part of the
  built wheel.
- `README.md` rewritten: new "v0.2 direction" section up top states the
  numeric-deliverable focus; new "Native backend (experimental)" section
  documents `get_subsets_native`, its build-from-source requirement, and
  points to `going_4_rust.md`/this changelog for the retired functions'
  history instead of re-describing them.

## 2026-07-24 — v0.1.1: top-level imports

- `src/subsetmatrix/__init__.py` now re-exports `ObservationSet`,
  `generateMatrix`, `iter_k_masks`, `cardinality`, and
  `extract_k_window`, so `from subsetmatrix import ObservationSet`
  works without the submodule path. Bumped version to 0.1.1 to ship
  it (0.1.0 is already on PyPI and immutable).

## 2026-07-24 — PyPI-shipping readiness pass

- Verified the package builds cleanly (`python -m build`), passes
  `twine check` on both sdist and wheel, contains only the intended
  4 modules (no test/benchmark leakage), and installs/imports
  correctly from a fresh venv (not just editable install).
- Confirmed `subsetmatrix` is unclaimed on PyPI.
- Switched `license = { file = "LICENSE" }` + the MIT classifier to
  PEP 639's `license = "MIT"` / `license-files = ["LICENSE"]`,
  clearing a `SetuptoolsDeprecationWarning`. Bumped the
  `build-system.requires` setuptools floor to `>=77` accordingly.
- Added `dist/` and `build/` to `.gitignore`.
- Not done (requires the user's own PyPI account/API token):
  the actual `twine upload`.

## 2026-07-24 — engineTest.py promoted to engine.py (old engine.py removed)

- `engineTest.py` renamed to `engine.py`, replacing the original
  engine module entirely; `dataset_payload.py` and
  `benchmarks/bench_generate_matrix.py` import updated accordingly.
- Removed the now-superseded `tests/test_engine.py` (tested the old
  module's bare-call defaults, which no longer exist); the former
  `tests/test_engineTest.py` renamed to `tests/test_engine.py`.
- Fixed `tests/test_selecting_subsets.py`: its `extract_k_window`
  fixtures relied on `generateMatrix(n)`'s old bare-call default
  (full k=1..n-1 sweep); updated to pass that range explicitly, since
  `extract_k_window`'s offset math assumes that specific layout and
  doesn't verify it. Documented that assumption on
  `extract_k_window`'s docstring.
- Updated `README.md` examples that documented the old default output
  shape/values.

## 2026-07-24 — Vectorized generateMatrix + bulk-nonzero get_subsets

- `engineTest.generateMatrix` now expands masks to rows in one
  broadcasted numpy call per k-group instead of one call per row.
  ~8-11x faster than the previous version; now beats
  `itertools.combinations` by 2-5x (previously lost to it by 2-3x).
- `ObservationSet.get_subsets` now does a single bulk `np.nonzero`
  over the whole matrix (reshaped per k-block) instead of one
  `np.flatnonzero` per row, plus a bulk `.tolist()` before the final
  Python assembly loop. ~4x faster than before; gap to itertools
  narrowed from 6-16x slower to ~1.5-2.5x slower.
- `selecting_subsets.validate_k` now allows `k == n` (full-set
  subsets), matching `generateMatrix`'s new default range. Updated
  `tests/test_input_validation.py` accordingly (old test asserted the
  now-obsolete rejection).
- Dropped dead code in `dataset_payload.py` (commented-out old
  `extract_k_window` branch, unused import).
- `benchmarks/bench_generate_matrix.py` updated to reflect the shipped
  state.

## 2026-07-24 — engineTest.generateMatrix bug fix + K-range default change

- Fixed a bug in `engineTest.generateMatrix`: the output array was
  always allocated at the full `(1<<n) - 2` row count regardless of
  which `K` was requested, leaving uninitialized (garbage) rows
  whenever `K` was a strict subset of all k-values. This corrupted
  `ObservationSet.get_subsets` output for any non-full k selection.
  Now sized to `sum(comb(n, k) for k in K)`.
- Changed `generateMatrix`'s default `K` (when called with none) from
  `range(3, n)` to `range(2, n + 1)` — excludes singletons (k=1),
  includes the full set (k=n).
- Extended `iter_k_masks` to accept `k == n` (was `0 < k < n`, now
  `0 < k <= n`) to support the full-set case.
- Added `tests/test_engineTest.py` and `benchmarks/bench_generate_matrix.py`.
- Known gap: `selecting_subsets.validate_k` (used by
  `ObservationSet.get_subsets`) still rejects `k == n`, so the new
  full-set support in `generateMatrix` isn't reachable through
  `get_subsets` yet — out of scope for this change, left for a
  follow-up.

## 2026-07-24 — Governance scaffolding

- Added `.agents/` (prompts.md, observations.md), root `CLAUDE.md` /
  `AGENTS.md` pointers, and this changelog structure. No library code
  changed.
