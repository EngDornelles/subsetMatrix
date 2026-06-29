import pytest

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