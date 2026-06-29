# subsetMatrix

`subsetMatrix` is a small Python library for generating, selecting, and materializing subsets from an observation set.

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

### Generate a subset matrix

```python
from subsetmatrix.engine import generateMatrix

matrix = generateMatrix(3)

print(matrix)
```

Output:

```text
[[1 0 0]
 [0 1 0]
 [0 0 1]
 [1 1 0]
 [1 0 1]
 [0 1 1]]
```

---

## User-facing dataset workflow

The easiest way to use the library is through `ObservationSet`.

```python
from subsetmatrix.dataset_payload import ObservationSet

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

```python
from subsetmatrix.engine import generateMatrix
from subsetmatrix.selecting_subsets import extract_k_window

matrix = generateMatrix(4)

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

### `generateMatrix(n: int)`

Generates the full non-empty, non-full subset membership matrix.

```python
from subsetmatrix.engine import generateMatrix

matrix = generateMatrix(4)
```

For `n = 4`, the shape is:

```text
(14, 4)
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

## Repository structure

```text
subsetMatrix/
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── subsetmatrix/
│       ├── __init__.py
│       ├── engine.py
│       ├── selecting_subsets.py
│       └── dataset_payload.py
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

`subsetMatrix` is in early development.

Current stable layers:

```text
engine.py
→ generate subset matrix

selecting_subsets.py
→ extract k-window slices

dataset_payload.py
→ materialize dataset subsets
```

Planned improvements may include:

* snake_case aliases;
* chunked matrix generation;
* mask-first public workflows;
* memory estimation helpers;
* optional pandas helpers;
* optional export utilities;
* expanded documentation;
* performance benchmarks.

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
