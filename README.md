# subsetMatrix

Generate, select, and materialize subsets of an observation set.

Given `n` observations, `subsetmatrix` builds every k-sized subset without
you writing the combinatorics yourself, in two flavors:

- **`get_subsets_native`** -- numeric `X`/`Y` only, backed by a Rust/PyO3
  extension. With `python_typed=False` (raw numpy array out), 15-30x
  faster than `itertools.combinations` end-to-end at n=20. The default
  (`python_typed=True`, converts to native Python lists) lands close to
  itertools' own speed -- the conversion to Python objects is the real
  cost, not generation, so use `python_typed=False` if you're feeding
  the result to numpy/pandas anyway.
- **`ObservationSet` / `generateMatrix`** -- pure Python/NumPy, works with
  any `X` type (strings, dates, labels, whatever). Slower, more flexible.

Both ship in the box. `pip install subsetmatrix` installs the compiled
extension too -- nothing extra to build.

## Install

```bash
pip install subsetmatrix
```

## Quick start

Fast path, numeric data:

```python
from subsetmatrix import get_subsets_native

X = [1.0, 2.0, 3.0, 4.0]
Y = [10.0, 20.0, 30.0, 40.0]

subsets = get_subsets_native(X, Y, k=2)
# subsets is a list with one entry per k value requested -- subsets[0]:
# [[1.0, 10.0], [2.0, 20.0]], [[1.0, 10.0], [3.0, 30.0]], ...
```

`k` can be a single int or a list of ints; the return is always a list
with one entry per `k` value, in ascending `k` order. Pass
`python_typed=False` to get raw numpy arrays instead of nested Python
lists (faster if you're just going to hand them to numpy again anyway).

General path, any data:

```python
from subsetmatrix import ObservationSet

obs = ObservationSet({"X": ["A", "B", "C", "D"], "Y": [10, 20, 30, 40]})
obs.get_subsets(2)
# [[["A", 10], ["B", 20]], [["A", 10], ["C", 30]], ...]
```

If `X` is omitted, `ObservationSet` generates integer labels for you
(1-indexed by default; pass `indexing_as_one=False` for 0-indexed).

## API

| | |
|---|---|
| `get_subsets_native(X, Y, k, python_typed=True)` | Fast, numeric-only. Returns a list with one entry per `k` value; each entry is `[[x, y], ...]` per subset. |
| `ObservationSet({"X": ..., "Y": ...}).get_subsets(k)` | General-purpose, any `X` type. Returns one flat list of `[[x, y], ...]` per subset across all `k` values -- not grouped per `k` like the native path. |
| `generateMatrix(n, K=[], n_max=20)` | Dense `0/1` membership matrix, shape `(rows, n)`, one row per subset. `K` defaults to `range(2, n+1)` (skips singletons, includes the full set). `n_max` is the ceiling on `n` -- raise it to go past 20. |
| `iter_k_masks(n, k)` | Generator of integer bitmasks with exactly `k` set bits -- what everything above is built on. |
| `cardinality(mask)` | Number of set bits in a mask. |
| `extract_k_window(matrix, k)` | Pulls the rows for one or more `k` values out of a `generateMatrix` result. Assumes `matrix` was built with the full `K=list(range(1, n))` sweep -- pass that explicitly to `generateMatrix` if you're going to window it, since `generateMatrix`'s own default `K` doesn't match. |

## Notes

- **Ordering**: rows/subsets come out in ascending-bitmask order within
  each `k` group (an artifact of the generation algorithm), not
  `itertools.combinations`'s lexicographic order. Same members, different
  sequence -- matters if you're diffing against `itertools` output.
- **Memory**: `generateMatrix` materializes a dense `(rows, n)` array;
  `rows` grows like `2^n` on the default `K`. `n_max` (default 20) is the
  ceiling, and it is a courtesy, not a law -- pass a bigger one and the
  matrix is yours to afford. A narrow `K` stays cheap well past 20
  (`n=30, K=[3]` is 4,060 rows, under half a megabyte); the default `K` at
  the same `n` is over a billion rows and will take the process down.
  Nothing checks this for you. Rows are `uint32`, so `n <= 32` is a hard
  representation ceiling whatever `n_max` says -- above it the mask
  overflows with an `OverflowError`. `get_subsets_native` and
  `ObservationSet.get_subsets` don't have this cap for reasonable `k`, but
  the output itself still grows combinatorially -- `comb(n, k)` subsets,
  however you generate them.
- **Bitmasks without the matrix**: `iter_k_masks(n, k)` has no cap at all
  and never allocates -- it yields one Python int per subset. If you only
  need subset *identity*, that mask is it, at `1/n` the footprint of a
  dense row, and it stays valid past every ceiling above.
- Full engineering history (why the Rust path exists, what it beat, what
  didn't work) is in [`going_4_rust.md`](going_4_rust.md) and
  [`logs/mvp_changelog.md`](logs/mvp_changelog.md).

## License

MIT -- see [`LICENSE`](LICENSE).

Lucas Dornelles Cherobim -- [EngDornelles](https://github.com/EngDornelles)
