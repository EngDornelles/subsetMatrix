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

## 2026-08-05 — v0.2.0 published

- `master` fast-forwarded to `functional`'s tip (`be67b57`) -- was 7
  commits behind, no unique commits of its own, so a clean fast-forward.
  `v0.2.0` tagged and released off `master`, restoring the convention
  from `v0.1.0`/`v0.1.1` (both released off `master`) rather than tagging
  off `functional` directly.
- First real run of the rewritten `publish.yml`: all six jobs (Linux
  x86_64/aarch64, Windows, macOS x86_64/aarch64, sdist) succeeded, ~1-1.5
  min each, then published via the existing trusted-publisher `pypi`
  environment -- no new PyPI-side setup was needed, confirming the
  bundle-not-dependency correction was the right call.
- Verified against the real index (not a local build): fresh venv,
  `pip install subsetmatrix==0.2.0`, confirmed `get_subsets_native` and
  the rest of the public API work from an actual PyPI install.
- `v0.1.*` is now superseded.

## 2026-08-05 — Correction: bundle subsetmatrix_rs into subsetmatrix's own wheel, not a separate PyPI package

- Follow-up/correction to the entry below. Lucas's actual intent:
  `subsetmatrix_rs` was never meant to be an independent package with its
  own PyPI identity and a version-pinned dependency relationship -- it's
  "just some subfolder inside the project," meant to be adjoined into
  `subsetmatrix`'s own wheel, one project, one install.
- Reworked: root `pyproject.toml`'s `build-system` switched from
  `setuptools.build_meta` to `maturin`, with a `[tool.maturin]` mixed
  Python/Rust config (`python-source = "src"`,
  `manifest-path = "rust/subsetmatrix_rs/Cargo.toml"`,
  `module-name = "subsetmatrix.subsetmatrix_rs"`). The compiled extension
  now lands *inside* the `subsetmatrix` package directory
  (`subsetmatrix/subsetmatrix_rs.pyd` alongside `__init__.py`,
  `engine.py`, etc.) as part of the same wheel -- confirmed by inspecting
  the built wheel's file list. Removed the `subsetmatrix_rs>=0.2.0,<0.3`
  dependency line entirely; there's nothing external to depend on anymore.
  `native_backend.py`'s import changed from `import subsetmatrix_rs` to
  a relative `from . import subsetmatrix_rs` (avoids any ambiguity with
  `subsetmatrix/__init__.py`'s own partial-init state during import).
- This is a strictly better outcome than the separate-package approach
  for the PyPI-side blocker flagged earlier: no new project registration
  or trusted-publisher setup needed, since it's still just the one
  existing `subsetmatrix` project on PyPI, same trusted-publisher
  environment (`pypi`) as before.
- Deleted the vestigial standalone-package files created for the
  (wrong) separate-package approach: `rust/subsetmatrix_rs/pyproject.toml`,
  `LICENSE`, `README.md`, and `.github/workflows/publish-rust.yml`.
  `rust/subsetmatrix_rs/Cargo.toml`/`Cargo.lock`/`src/lib.rs` stay --
  still needed, now referenced via `manifest-path` from the root.
- Rewrote `.github/workflows/publish.yml` itself: the old version ran
  plain `python -m build` on a single Ubuntu runner, which would have
  produced a single Linux-only wheel now that the package contains
  compiled code (previously fine, since the old wheel was pure Python
  and "universal"). Replaced with a `maturin-action` matrix (Linux
  x86_64/aarch64, Windows x64, macOS x86_64/aarch64) plus an sdist job,
  merged and published together -- same job shape as the (now-deleted)
  `publish-rust.yml` drafted for the wrong architecture, retargeted at
  the root project. Same environment name and PyPI project as before, so
  the existing trusted-publisher config should keep working unchanged --
  still **unverified on real CI**, no runner access from this session.
- Also caught and fixed: `maturin develop` drops the compiled
  `subsetmatrix_rs.pyd`/`.pdb` directly into `src/subsetmatrix/` for the
  editable install to work. Added `src/subsetmatrix/*.pyd`,
  `*.pdb`, `*.so` to `.gitignore` before committing -- these are
  per-machine build output, not source, and were about to get
  accidentally staged.
- **Verified end-to-end, the real way this time**: built the actual
  wheel (`maturin build --release`), inspected its contents directly
  (confirmed `subsetmatrix/subsetmatrix_rs.pyd` is inside the
  `subsetmatrix/` directory in the wheel, not a separate package), then
  installed *that exact wheel file* (not editable, not `--find-links`)
  into a brand-new venv and ran the full public API from it --
  `get_subsets_native`, `ObservationSet`, `generateMatrix`,
  `iter_k_masks`, `cardinality`, `extract_k_window` all confirmed
  working. `pytest` clean (71 passed) in the main dev venv throughout.
- Net state: ready to push and publish. No new PyPI-side setup required
  -- the existing `subsetmatrix` trusted publisher should just work, but
  the multi-platform CI has not run for real yet, so the first release
  after this change is worth watching rather than trusting blind.

## 2026-08-05 — v0.2.0 release prep: ship the native backend for real, lean README, dead-file cleanup

- Lucas's direction: `pip install subsetmatrix` should give the full
  package -- fast numeric path included -- not "a chewed up version
  using only numpy." Decided against building `subsetmatrix_rs` into
  `subsetmatrix`'s own wheel (would mean switching the whole package's
  build backend to maturin and a mixed Rust/Python layout); instead
  published `subsetmatrix_rs` as its **own small PyPI package**, and
  `subsetmatrix` now declares it as a real dependency
  (`subsetmatrix_rs>=0.2.0,<0.3`). `rust/subsetmatrix_rs/pyproject.toml`
  already existed as a proper maturin project (from the original
  `going_4_rust.md` scaffolding) -- filled in its metadata (description,
  license, readme, classifiers; dropped the inherited PyPy classifier
  since abi3 wheels are CPython-specific) rather than restructuring
  anything.
- `Cargo.toml`: added `pyo3`'s `abi3-py310` feature. One compiled wheel
  per (OS, arch) now covers every Python `subsetmatrix` supports
  (`>=3.10`), instead of a wheel per Python-version-per-platform. Kept
  `u128` masks (not `u64`) despite the earlier open item in
  `going_4_rust.md` -- Lucas: the direction is toward *larger* `n` for
  quenching huge datasets, not smaller, so trading mask width for a
  hardware-division win now would cut against where this is headed.
- New `.github/workflows/publish-rust.yml`: builds `subsetmatrix_rs`
  wheels via `maturin-action` across Linux (x86_64/aarch64), Windows
  (x64), and macOS (x86_64/aarch64), plus an sdist, then publishes via
  PyPI trusted publishing on GitHub Release. Mirrors the existing
  `publish.yml` pattern (same `release: published` trigger, same OIDC
  approach). **Not verified on real CI** -- written from the standard
  maturin-action pattern, sanity-checked for syntax, but this repo has
  no CI runner access from this session. First real run should happen
  under supervision.
- `__init__.py`: added `get_subsets_native` to the public exports
  (additive -- nothing existing removed or renamed, so this doesn't
  break the current PyPI public API contract).
- **Verified end-to-end, not just configured**: built an actual
  `subsetmatrix_rs` wheel locally (`maturin build --release`), created a
  brand-new venv from scratch, and ran
  `pip install --find-links rust/subsetmatrix_rs/dist .` against the
  repo root -- exactly what `pip install subsetmatrix` will do once both
  packages are on PyPI. Both packages installed, `import subsetmatrix`
  worked, and both `generateMatrix` and `get_subsets_native` ran
  correctly from the fresh environment. `pytest` also re-run clean (71
  passed) throughout.
- Dead-file cleanup (delegated, verified): removed
  `src/subsetmatrix/functional.py` (zero references anywhere -- an
  abandoned duplicate of `engine.iter_k_masks`) and the
  `functional_pipeline.py` / `bench_functional_pipeline.py` /
  `test_functional_pipeline.py` trio (a self-contained SQLite-persistence
  prototype, explicitly documented as "kept deliberately separate," never
  exported, never wired to anything real). Confirmed via grep that no
  code still imports either; historical prose mentions in
  `going_4_rust.md` left untouched.
- `README.md` rewritten from scratch: 723 lines -> 88. Cut the padded
  "why this exists" bullet list, the redundant "design notes" prose, the
  repository-structure tree, and duplicate examples -- all the stuff an
  outside reader (or an AI skimming the package) would reasonably read as
  bloat. Kept: what it is, install, one example per path (native +
  general), a compact API table, and the three notes that actually matter
  (ordering, memory, the `extract_k_window` layout footgun). Caught and
  fixed two of my own inaccuracies while proof-testing the examples
  against a real install before finalizing: `get_subsets_native`'s return
  shape has an extra per-k nesting level I'd glossed over in the first
  draft, and the "15-30x faster" performance claim only holds for
  `python_typed=False` (raw array) -- the default (`python_typed=True`)
  lands close to itertools' own speed, per the python_typed finding
  already on record from the original `going_4_rust.md` benchmarking.
  Both fixed before landing, not left in.
- **Not done this session, requires Lucas directly**: registering
  `subsetmatrix_rs` as a project on PyPI and configuring trusted
  publishing for it (PyPI-side, tied to his account -- cannot be done via
  CLI/API from here) and running the actual GitHub Release that triggers
  both publish workflows. Nothing was pushed, tagged, or published this
  session.

## 2026-08-05 — combinations_values: boolean-bulk-as-transformer attempt tested, reverted

- Second follow-up to the v0.2.0 entry below (see the entry above this
  one for the first). Lucas clarified the original "crank it up a knot"
  idea wasn't about skipping initialization at all (that was my
  misreading, corrected in the entry above) -- it was about not
  materializing a full **boolean membership matrix** (like the old,
  removed `generate_matrix`: one row per subset, one column per
  observation, 1/0 per cell) and only afterward "validating"/transforming
  it into X/Y pairs as a separate reallocating pass. The proposed fix:
  still zero-init-and-bulk-generate the boolean membership data per
  k-group (as before), but instead of that boolean matrix being the
  final artifact requiring a later separate transform-and-reallocate
  step, use it directly as a read-only "transformer" to gather X[j]/Y[j]
  into an already-preallocated (count, k, 2) output, both buffers sized
  once upfront, no reallocation in between. Estimated as a minor win,
  "about 1%, maybe 2%."
- Implemented literally as `combinations_values_boolbulk` (added
  alongside `combinations_values`, not replacing it, so both could be
  benchmarked in the same build): a (count, n) zero-init'd `Vec<u8>`
  boolean bulk filled via the same Gosper-hack mask-decode loop, then a
  second pass scanning each row's `n` boolean columns to gather
  `x[j]`/`y[j]` into a separately pre-allocated (count, k, 2) `Vec<f64>`.
- Benchmarked head-to-head against `combinations_values`, plus each
  against `itertools`, across a wide k range (n=20, k=2/5/8/10/14/15/16/19,
  25 reps, min-of-N) to see how the boolean-scan-vs-bit-decode tradeoff
  moves with the k/n ratio. Correctness matched exactly at every k
  tested (not a bug) -- the ratios did not:

  ```
     k    subsets    itertools  current (s)  cur ratio  boolbulk (s)  bb ratio   bb/cur
     2        190     0.000029     0.000002     16.94x      0.000004     8.00x    2.12x
     5      15504     0.005731     0.000271     21.18x      0.000963     5.95x    3.56x
     8     125970     0.087139     0.003123     27.90x      0.010006     8.71x    3.20x
    10     184756     0.172695     0.005673     30.44x      0.015799    10.93x    2.79x
    14      38760     0.044245     0.001644     26.91x      0.003517    12.58x    2.14x
    15      15504     0.016218     0.000709     22.86x      0.001414    11.47x    1.99x
    16       4845     0.004461     0.000240     18.58x      0.000458     9.75x    1.91x
    19         20     0.000020     0.000001     18.09x      0.000002    12.44x    1.45x
  ```

  The boolean-bulk variant was **1.45x-3.56x slower** than the current
  implementation at every k tested, worst around k=5..10 (where `count`
  is largest and the n/k ratio is still substantial), best (but still
  clearly worse) at k near n, where scanning n columns approaches
  scanning k. Not a 1-2% win in either direction -- a real, order-of-
  magnitude-relevant regression.
- Diagnosis: decoding straight from the mask register only ever touches
  the `k` set bits (Gosper's hack skips the zero bits entirely by
  construction). Materializing a boolean row and scanning it touches all
  `n` columns per row, most of which are zero for typical `k << n`
  cases -- strictly more work, not less. The extra `(count, n)` buffer
  is also frequently larger than the `(count, k, 2)` output it feeds
  (e.g. at k=2, n=20: 20 boolean bytes generated to find 2 values).
- Action: removed `combinations_values_boolbulk` from `lib.rs` --
  correctness was fine, but shipping a slower, unused alternate
  implementation contradicts the "squeezer-only, no dead weight" premise
  the crate was just trimmed down to. `combinations_values` itself is
  unchanged from the previous entry. Both attempts (this one and the
  `uget_raw` one) are recorded in `lib.rs`'s module-level doc comment so
  neither gets retried without new evidence.
- Verified: `pytest` (82 passed) against the final build (no
  `combinations_values_boolbulk` present).

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
