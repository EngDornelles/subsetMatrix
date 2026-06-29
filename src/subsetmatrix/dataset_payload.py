import numpy as np
from subsetmatrix.engine import generateMatrix
from subsetmatrix.selecting_subsets import extract_k_window, validate_k, normalize_k_values
from typing import Any

class ObservationSet:
    """This class instantiates objects with a set of points and keeps a
matrix with all possible combinations for subsets, the main dataset and
performs methods on them for several usecases.

## Arguments
For now only a dict in the format
{
    "Y": [*observations],
    "X": [*labels]
}
where len(Y) == len(X) if you enter values for X

### properties:
- X is a list of labels for the observations. They might come as small strings
or numbers, dates or whatever else picks your fancy;
- Y is a list of observations. For scientific ends, this one should be some
type of numeric value, but since this tool is here to answer to some diverse
need, no use limiting its reach through that, so it might also be a list of
anything that picks your fancy.
"""
    def __init__(self, points:dict[str,list[Any]],*args, **kwargs) -> None:
        self.indexing_as_one = bool(kwargs.get("indexing_as_one", True))
        if not isinstance((a := points.get("Y")), list) or len(a) <= 2:
            raise ValueError("points['Y'] must be a list with more than 2 observations.")
        self.Y = a
        self.n = len(self.Y)
        x = points.get("X")
        if x is not None:
            if not isinstance(x, list):
                raise TypeError("points['X'] must be a list.")
            if len(x) != self.n:
                raise ValueError("points['x'] must have the same length as points['Y'].")
            self.X = x
        else:
            start = 1*self.indexing_as_one
            self.X = list(range(start, len(self.Y) + start)) # index[0] as 1 as default to be friendlier to a broader public
        # self.subset_matrix = generateMatrix(self.n) # not using this for now, it would just occupy memory in the scope for no good reason
        # This place here has space for a buttload of validation logic, so I won't bother with this right now.
        # TODO: implement other ways for consuming args and kwargs, with more positional args and more suggested kwargs.
        # It would be simpler to just limit admission to one simple door, but that isn't very pythonic nor user friendly
        # For now I'll work with the hipotesys that self.Y works and self.X doesn't come with a different size than Y
        # We can validate all of that later

        # from here on we will assume Y and X behave well and are source of truth.
    
    def get_subsets(self, k:int|list[int]) -> list[list[Any]]:
        k_values = normalize_k_values(k, self.n) # normalizing here to test if the set is the same as the set that contains all possible k
        if k_values == list(range(1, self.n)):
            temp_matrix = generateMatrix(self.n)
        else:
            temp_matrix = extract_k_window(generateMatrix(self.n),k_values)

        res = []
        for i in temp_matrix:
            indices = np.flatnonzero(i)
            subset = [[self.X[j], self.Y[j]] for j in indices]
            res.append(subset)
        return res

