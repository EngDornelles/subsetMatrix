import numpy as np
from math import comb
from subsetmatrix.engine import generateMatrix
from subsetmatrix.selecting_subsets import normalize_k_values
from typing import Any
from subsetmatrix.payload_args_validation import validate_args, validate_kwargs

class ObservationSet:
    """This class instantiates objects with a set of points and keeps a
matrix with all possible combinations for subsets, the main dataset and
performs methods on them for several usecases.
### properties:
- X is a list of labels for the observations. They might come as small strings
or numbers, dates or whatever else picks your fancy, or not come at all, case
in which we will generate a list of integers as index to the observations;
- Y is a list of observations. For scientific ends, this one should be some
type of numeric value, but since this tool is here to answer diversefied needs,
no use limiting its reach through that, so it might also be a list of anything.
"""
    def __init__(self, *args, **kwargs) -> None:
        # grabbing the first significant argument
        args_dict = validate_args(*args) if args else {}
        kwargs_dict = validate_kwargs(
            **{k:v for k, v in kwargs.items() if k != "indexing_as_one"}
        ) if kwargs else {}
        
        if not args_dict and not kwargs_dict:
            raise ValueError("No data was detected while initiating this object.")
        
        self.Y = args_dict.get("Y")
        if self.Y is None:
            self.Y = kwargs_dict.get("Y")

        if self.Y is None:
            raise ValueError("No values for Y were detected while initiating this object.")

        self.n = len(self.Y)

        self.X = args_dict.get("X")
        if self.X is None:
            self.X = kwargs_dict.get("X")
        
        if self.X is None:
            self.indexing_as_one = bool(kwargs.get("indexing_as_one", True))
            start = 1 if self.indexing_as_one else 0
            self.X = list(range(start, self.n + start))
        
        if len(self.X) != len(self.Y):
            raise ValueError(f"The length of the X set and of the Y set are of different sizes: X: {len(self.X)} and Y: {len(self.Y)}")
    
    def get_subsets(self, k:int|list[int]) -> list[list[list[Any]]]:
        k_values = normalize_k_values(k, self.n)
        temp_matrix = generateMatrix(self.n, k_values)

        # one bulk nonzero pass over the whole matrix instead of one
        # np.flatnonzero call per row: rows are grouped by k in k_values
        # order and every row within a k-group has exactly k ones, so the
        # flat column-index stream can be reshaped per group without
        # re-touching numpy per row.
        _, col_idx = np.nonzero(temp_matrix)

        res = []
        pos = 0
        for k_val in k_values:
            count = comb(self.n, k_val)
            # .tolist() converts the whole block in one bulk C call; iterating
            # a numpy array element-by-element boxes each entry into a numpy
            # scalar, which is far costlier than plain-int indexing below.
            block = col_idx[pos:pos + count * k_val].reshape(count, k_val).tolist()
            pos += count * k_val
            for combo in block:
                res.append([[self.X[j], self.Y[j]] for j in combo]) # type: ignore
        return res

