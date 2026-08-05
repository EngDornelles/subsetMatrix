# subsetMatrix

`subsetMatrix` is a small Python library for generating, selecting, and materializing subsets from an observation set.

## v0.2 direction

As of v0.2, the project's primary target is **fast numeric `[X, Y]` subset
deliverables** — the shape needed by downstream engine work (Multinterp) —
produced through a bare-bone Rust/PyO3 fused generator, not general-purpose
subset ergonomics for arbitrary data types.

The Python/NumPy engine documented below (`generateMatrix`, `ObservationSet`,
etc.) remains the shipped PyPI public API and is unchanged — it still
handles any `X` type (labels, strings, dates, whatever). The new native
backend is numeric-only (`X`/`Y` must be floats) and is not yet part of the
published wheel; see [Native backend](#native-backend-experimental) below
for what it is, why it exists, and how to build it locally. See
[`going_4_rust.md`](going_4_rust.md) and
[`logs/mvp_changelog.md`](logs/mvp_changelog.md) for the full benchmark
trail behind this decision and the v0.2 entry specifically.

It starts with a simple idea:

> Given `n` observations, generate a binary matrix where each row represents one subset.

Each column represents one observation.
Each row represents one subset.
A value of `1` means the observation belongs to that subset.
A value of `0` means it does not.

For `n = 3`, the generated matrix is:

```text
[[1 0 0]
 [0 1 0]
 [0 0 1]
 [1 1 0]
 [1 0 1]
 [0 1 1]]
```

The empty subset `[0 0 0]` and the full subset `[1 1 1]` are excluded by default.

---

## Why this exists

Many workflows need to explore combinations of observations, points, features, candidates, or records.

`subsetMatrix` provides a deterministic substrate for that kind of work.

It can be useful for:

* combinatorial analysis;
* subset generation;
* fixed-size subset selection;
* dataset slicing;
* candidate generation;
* research prototypes;
* model experimentation;
* matrix-based workflows;
* observation-subset analysis.

The library intentionally keeps interpretation out of the core.

It does not decide what a subset means.
It only helps generate, select, and materialize subsets.

---

## Core behavior

For `n` observations, there are:

```text
2^n
```

possible subsets.

`subsetMatrix` excludes the empty and full subsets, so the generated matrix has:

```text
2^n - 2
```

rows.

The matrix shape is:

```text
(2^n - 2, n)
```

Examples:

```text
n = 3  → 6 rows
n = 4  → 14 rows
n = 20 → 1,048,574 rows
```

Rows are grouped by subset size `k`.

For `n = 4`, rows are ordered as:

```text
k = 1 → subsets with one active observation
k = 2 → subsets with two active observations
k = 3 → subsets with three active observations
```

The groups `k = 0` and `k = n` are skipped.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/EngDornelles/subsetMatrix.git
cd subsetMatrix
```

Create a virtual environment.

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

Install the package in editable mode:

```powershell
py -m pip install -e .
```

Install test dependencies:

```powershell
py -m pip install pytest
```

Run tests:

```powershell
py -m pytest -v
```

---

## Quick start

The full public API (`ObservationSet`, `generateMatrix`, `iter_k_masks`,
`cardinality`, `extract_k_window`) is importable directly from the
top-level package, e.g. `from subsetmatrix import ObservationSet`.
Examples below import from the submodules to show where each symbol
actually lives, but either form works.

### Generate a subset matrix

```python
from subsetmatrix.engine import generateMatrix

matrix = generateMatrix(3)

print(matrix)
```

By default (no `K` given), rows are grouped by k, skipping singletons
(k=1) and including the full set (k=n):

Output:

```text
[[1 1 0]
 [1 0 1]
 [0 1 1]
 [1 1 1]]
```

To include singletons or restrict to specific subset sizes, pass `K`
explicitly:

```python
matrix = generateMatrix(3, [1, 2, 3])
```

---

## User-facing dataset workflow

The easiest way to use the library is through `ObservationSet`.

```python
from subsetmatrix import ObservationSet

obs = ObservationSet(
    {
        "Y": [10, 20, 30, 40],
        "X": ["A", "B", "C", "D"],
    }
)

subsets = obs.get_subsets(2)

print(subsets)
```

Output:

```python
[
    [["A", 10], ["B", 20]],
    [["A", 10], ["C", 30]],
    [["B", 20], ["C", 30]],
    [["A", 10], ["D", 40]],
    [["B", 20], ["D", 40]],
    [["C", 30], ["D", 40]],
]
```

`X` contains labels.
`Y` contains observations.

If `X` is not provided, labels are generated automatically.

```python
obs = ObservationSet(
    {
        "Y": [10, 20, 30, 40],
    }
)

print(obs.X)
```

Output:

```python
[1, 2, 3, 4]
```

By default, generated labels are one-based.

To use zero-based labels:

```python
obs = ObservationSet(
    {
        "Y": [10, 20, 30, 40],
    },
    indexing_as_one=False,
)

print(obs.X)
```

Output:

```python
[0, 1, 2, 3]
```

---

## Selecting subset windows by `k`

You can extract only the rows for a specific subset size.

`extract_k_window` computes row offsets assuming `matrix` was built
with the full k=1..n-1 sweep, so pass that explicit `K` to
`generateMatrix` — its own default (no `K`) skips k=1 and includes
k=n, which no longer matches those offsets. If you just want specific
k-sized subsets, prefer calling `generateMatrix(n, K)` directly (see
above) instead of going through `extract_k_window`.

```python
from subsetmatrix.engine import generateMatrix
from subsetmatrix.selecting_subsets import extract_k_window

matrix = generateMatrix(4, list(range(1, 4)))

k2_matrix = extract_k_window(matrix, 2)

print(k2_matrix)
```

Output:

```text
[[1 1 0 0]
 [1 0 1 0]
 [0 1 1 0]
 [1 0 0 1]
 [0 1 0 1]
 [0 0 1 1]]
```

You can also extract multiple `k` groups:

```python
selected = extract_k_window(matrix, [1, 3])
```

The list is normalized, sorted, and deduplicated.

So this:

```python
extract_k_window(matrix, [3, 1, 1])
```

behaves like:

```python
extract_k_window(matrix, [1, 3])
```

---

## Fixed-size mask generation

`subsetMatrix` uses integer masks internally to generate subset rows.

You can generate masks directly for a fixed subset size `k`:

```python
from subsetmatrix.engine import iter_k_masks

for mask in iter_k_masks(n=4, k=2):
    print(mask)
```

Output:

```text
3
5
6
9
10
12
```

Those masks correspond to:

```text
0011
0101
0110
1001
1010
1100
```

Each mask has exactly two active bits.

---

## Cardinality

You can check how many active observations a mask contains:

```python
from subsetmatrix.engine import cardinality

print(cardinality(5))
```

Output:

```text
2
```

Because:

```text
5 = 0101
```

has two active bits.

---

## Current API

### `generateMatrix(n: int, K: list[int] = [])`

Generates the subset membership matrix for the requested subset sizes,
grouped by k. If `K` is omitted, defaults to `range(2, n + 1)` —
singletons (k=1) are skipped and the full set (k=n) is included.

```python
from subsetmatrix.engine import generateMatrix

matrix = generateMatrix(4)
```

For `n = 4`, the shape is:

```text
(11, 4)
```

Pass `K` explicitly to select specific subset sizes:

```python
matrix = generateMatrix(4, [2])       # only pairs
matrix = generateMatrix(4, [1, 2, 3]) # the pre-1.0 default: full k=1..n-1 sweep
```

---

### `iter_k_masks(n: int, k: int)`

Yields integer masks with exactly `k` active observations.

```python
from subsetmatrix.engine import iter_k_masks

masks = list(iter_k_masks(4, 2))
```

---

### `cardinality(mask: int)`

Returns how many active bits exist in a mask.

```python
from subsetmatrix.engine import cardinality

cardinality(12)
```

---

### `extract_k_window(matrix, k)`

Extracts rows for one or more subset sizes.

```python
from subsetmatrix.selecting_subsets import extract_k_window

k2 = extract_k_window(matrix, 2)
mixed = extract_k_window(matrix, [1, 3])
```

---

### `ObservationSet(points).get_subsets(k)`

Materializes actual dataset subsets.

```python
from subsetmatrix.dataset_payload import ObservationSet

obs = ObservationSet(
    {
        "Y": [10, 20, 30, 40],
        "X": ["A", "B", "C", "D"],
    }
)

obs.get_subsets(2)
```

---

## Native backend (experimental)

For numeric `X`/`Y`, `subsetmatrix` also ships a Rust/PyO3 extension
(`rust/subsetmatrix_rs`) that fuses subset generation and the `X[j]`/`Y[j]`
lookup into a single pass, writing straight into the output numpy array as
each subset is decoded — no intermediate Python objects, no boolean/index
matrix round-trip. This is the v0.2 focus described above.

**This backend is not part of the published PyPI wheel.** It only works
when built from source, inside this repo:

```powershell
py -m pip install maturin
cd rust\subsetmatrix_rs
..\..\.venv\Scripts\maturin.exe develop --release
```

Once built, `subsetmatrix_rs` is importable in the active venv, and
`subsetmatrix.native_backend.get_subsets_native` wraps it:

```python
from subsetmatrix.native_backend import get_subsets_native

X = [1.0, 2.0, 3.0, 4.0]
Y = [10.0, 20.0, 30.0, 40.0]

subsets = get_subsets_native(X, Y, k=2)
```

Unlike `ObservationSet.get_subsets`, this path requires `X` and `Y` to
already be numeric (they're coerced to `float`) — it deliberately gives up
type-agnosticism for speed. It returns one list per requested `k` value,
each a nested `[[x, y], ...]`-per-subset list (or a raw numpy array with
`python_typed=False`).

An earlier iteration of this crate also had general-purpose, type-agnostic
functions (a dense boolean membership matrix, plain index tuples). None of
them beat `itertools.combinations` end-to-end once real values had to come
back out as Python objects — only the fused float path did, decisively. As
of v0.2 the crate is trimmed down to that one function; the retired
functions and their benchmark numbers are preserved in
[`going_4_rust.md`](going_4_rust.md) and
[`logs/mvp_changelog.md`](logs/mvp_changelog.md), not deleted from history.

---

## Repository structure

```text
subsetMatrix/
├── LICENSE
├── README.md
├── pyproject.toml
├── going_4_rust.md
├── src/
│   └── subsetmatrix/
│       ├── __init__.py
│       ├── engine.py
│       ├── selecting_subsets.py
│       ├── dataset_payload.py
│       └── native_backend.py      # wraps the Rust extension, not in __init__'s public exports
├── rust/
│   └── subsetmatrix_rs/           # PyO3 extension; build from source, not on PyPI (see above)
│       └── src/lib.rs
├── benchmarks/
│   ├── bench_generate_matrix.py
│   └── bench_subsetmatrix_rs.py
└── tests/
    ├── test_engine.py
    ├── test_selecting_subsets.py
    └── test_dataset_payload.py
```

---

## Design notes

### Matrix generation

The generated matrix is a binary membership matrix.

Each row is a subset.
Each column is an observation.

Example:

```text
[1 0 1 0]
```

means:

```text
include observation 0
exclude observation 1
include observation 2
exclude observation 3
```

---

### Cardinality grouping

Rows are grouped by subset size `k`.

This makes it possible to extract all subsets of a specific size without scanning the whole matrix.

For example, if you only need subsets with `k = 3`, you can extract only that window.

---

### Empty and full subsets

The empty subset and full subset are excluded.

They are usually not useful for workflows where subsets are being compared, sampled, scored, or transformed.

Excluded rows:

```text
[0 0 0 ... 0]
[1 1 1 ... 1]
```

---

### Dense matrix warning

The full dense matrix grows quickly.

```text
n = 20 → 1,048,574 rows
n = 26 → 67,108,862 rows
```

Future versions may add:

* mask-only output;
* chunked generation;
* memory estimation;
* packed storage;
* optional export formats;
* lazy payload materialization.

The current version prioritizes clarity and deterministic behavior.

---

## Testing

Run:

```powershell
py -m pytest -v
```

Current test coverage validates:

* matrix shape;
* exact output for `n = 3`;
* cardinality grouping;
* exclusion of empty and full rows;
* invalid `n`;
* k-window extraction;
* sorted and deduplicated `k` lists;
* rejection of invalid `k`;
* NumPy integer support;
* dataset payload materialization;
* default generated labels;
* custom labels;
* invalid input handling.

Example current test result:

```text
18 passed
```

---

## Development status

`subsetMatrix` is in early development. The Python/NumPy engine is
published and stable; the native backend is the active area of work.

Current stable layers:

```text
engine.py
→ generate subset matrix

selecting_subsets.py
→ extract k-window slices

dataset_payload.py
→ materialize dataset subsets

native_backend.py + rust/subsetmatrix_rs/
→ fast numeric [X, Y] subset deliverables (build-from-source, see above)
```

Planned improvements may include:

* snake_case aliases;
* chunked matrix generation;
* mask-first public workflows;
* memory estimation helpers;
* optional pandas helpers;
* optional export utilities;
* expanded documentation;
* shipping the native backend as part of the published wheel.

---

## Naming

The GitHub repository is named:

```text
subsetMatrix
```

The Python package is imported as:

```python
import subsetmatrix
```

This follows Python package naming conventions while preserving the repository’s public name.

---

## License

This project is licensed under the MIT License.

See:

```text
LICENSE
```

---

## Author

Created by Lucas Dornelles Cherobim.

GitHub: [EngDornelles](https://github.com/EngDornelles)
