import pytest
from itertools import combinations

from subsetmatrix.dataset_payload import ObservationSet


def test_observation_set_default_x_one_based():
    obs = ObservationSet({"Y": [10, 20, 30]})

    assert obs.X == [1, 2, 3]


def test_observation_set_default_x_zero_based():
    obs = ObservationSet({"Y": [10, 20, 30]}, indexing_as_one=False)

    assert obs.X == [0, 1, 2]


def test_observation_set_rejects_missing_y():
    with pytest.raises(ValueError):
        ObservationSet({"X": ["A", "B", "C"]})


def test_observation_set_rejects_bad_x_length():
    with pytest.raises(ValueError):
        ObservationSet({"Y": [10, 20, 30], "X": ["A", "B"]})


def test_get_subsets_k2():
    obs = ObservationSet(
        {
            "Y": [10, 20, 30, 40],
            "X": ["A", "B", "C", "D"],
        }
    )

    result = obs.get_subsets(2)

    assert result == [
        [["A", 10], ["B", 20]],
        [["A", 10], ["C", 30]],
        [["B", 20], ["C", 30]],
        [["A", 10], ["D", 40]],
        [["B", 20], ["D", 40]],
        [["C", 30], ["D", 40]],
    ]


def test_get_subsets_full_set_k_equal_n():
    obs = ObservationSet({"Y": [10, 20, 30], "X": ["A", "B", "C"]})

    assert obs.get_subsets(3) == [[["A", 10], ["B", 20], ["C", 30]]]


@pytest.mark.parametrize("n", [4, 5, 6, 7])
def test_get_subsets_matches_itertools_combinations_across_all_k(n):
    X = [f"x{i}" for i in range(n)]
    Y = list(range(n))
    obs = ObservationSet({"Y": Y, "X": X})
    K = list(range(1, n + 1))

    result = obs.get_subsets(K)

    got = {frozenset(tuple(pair) for pair in subset) for subset in result}
    expected = {
        frozenset((X[i], Y[i]) for i in combo)
        for k in K
        for combo in combinations(range(n), k)
    }
    assert got == expected
    assert len(result) == len(expected)