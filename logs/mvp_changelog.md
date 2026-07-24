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
