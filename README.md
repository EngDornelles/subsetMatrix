# subsetMatrix

`subsetMatrix` is a small Python utility for generating subset membership matrices.

Given a set with `n` observations, the project generates a binary matrix representing the non-empty and non-full subsets of that set.

Each row represents one subset.
Each column represents one observation.
A value of `1` means the observation belongs to that subset.
A value of `0` means it does not.

For example, with `n = 3`:

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

Many analytical workflows need to explore combinations of observations, features, points, candidates, or entities.

`subsetMatrix` provides a deterministic way to represent those combinations as a matrix.

This can be useful for:

* combinatorial analysis;
* subset-based experimentation;
* model candidate generation;
* sampling strategies;
* subset scoring;
* path or anchor exploration;
* matrix-based transformations;
* research prototypes involving combinations of observations.

The project is intentionally small. It only generates the subset substrate. It does not impose any scoring, modeling, or interpretation layer.

---

## Core idea

For `n` observations, the full number of possible subsets is:

```text
2^n
```

This project excludes the empty and full subsets, so the default number of generated rows is:

```text
2^n - 2
```

The matrix shape is therefore:

```text
(2^n - 2, n)
```

Example:

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

## Ordering

Rows are grouped by subset size.

For `n = 4`, the generated rows are grouped as:

```text
k = 1  → subsets with one active observation
k = 2  → subsets with two active observations
k = 3  → subsets with three active observations
```

The empty group `k = 0` and the full group `k = n` are skipped.

This makes the output easier to analyze by subset cardinality.

---

## Installation for local development

Clone the repository:

```bash
git clone https://github.com/EngDornelles/subsetMatrix.git
cd subsetMatrix
```

Create and activate a virtual environment.

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
py -m pytest
```

---

## Usage

### Generate a subset membership matrix

```python
from subsetmatrix.engine import generateMatrix

matrix = generateMatrix(4)

print(matrix)
print(matrix.shape)
```

Expected shape:

```text
(14, 4)
```

Because:

```text
2^4 - 2 = 14
```

---

### Generate masks for subsets of fixed size

The project also exposes a generator for masks with exactly `k` active observations.

```python
from subsetmatrix.engine import iter_k_masks

for mask in iter_k_masks(n=4, k=2):
    print(mask)
```

Each mask is an integer representation of a subset.

For example:

```text
3  → 0011
5  → 0101
6  → 0110
9  → 1001
10 → 1010
12 → 1100
```

This is useful because integer masks are compact and can be expanded into matrix rows later.

---

### Check mask cardinality

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

```python
generateMatrix(n: int)
```

Generates the full non-empty, non-full subset membership matrix for `n` observations.

```python
iter_k_masks(n: int, k: int)
```

Yields integer masks with exactly `k` active observations.

```python
cardinality(mask: int)
```

Returns the number of active bits in a mask.

---

## Design notes

`subsetMatrix` is based on the idea that subset membership can be represented compactly as integer masks.

A dense matrix is useful for inspection and downstream numerical workflows, but it can become large quickly.

For example:

```text
n = 20 → 1,048,574 rows
n = 26 → 67,108,862 rows
```

Because of that, future versions may expand mask-first workflows, chunked generation, storage helpers, and memory estimation tools.

The current version focuses on a simple, deterministic, inspectable matrix generator.

---

## Development status

This project is in early development.

Current focus:

* deterministic subset matrix generation;
* cardinality-grouped ordering;
* mask-based generation;
* small and readable implementation;
* local development and testing.

Planned improvements may include:

* snake_case API aliases;
* chunked matrix generation;
* mask-only output;
* memory estimation helpers;
* optional export formats;
* optional packed storage;
* better documentation and examples.

---

## Testing

Run:

```powershell
py -m pytest
```

Current tests validate basic matrix shapes, including:

```text
n = 3  → shape (6, 3)
n = 4  → shape (14, 4)
n = 20 → shape (1,048,574, 20)
```

---

## Repository structure

```text
subsetMatrix/
├── README.md
├── pyproject.toml
├── src/
│   └── subsetmatrix/
│       ├── __init__.py
│       └── engine.py
└── tests/
    └── test_engine.py
```

---

## Notes on naming

The GitHub repository is named:

```text
subsetMatrix
```

The Python import package uses lowercase naming:

```python
import subsetmatrix
```

This follows normal Python package naming conventions while preserving the repository name.

---

## License

License not defined yet.

Before using this project in production or redistributing it, check the repository license.

---

## Author

Created by Lucas Dornelles Cherobim.

GitHub: [EngDornelles](https://github.com/EngDornelles)

---

## Minimal example

```python
from subsetmatrix.engine import generateMatrix

if __name__ == "__main__":
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
