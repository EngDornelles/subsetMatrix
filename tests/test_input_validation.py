import pytest
from subsetmatrix.dataset_payload import ObservationSet
# ---------------------------------------------------------------------
# Positional Y-only input
# ---------------------------------------------------------------------
def test_accepts_single_list_as_y_values_with_default_one_based_x():
    obs = ObservationSet([10, 20, 30])
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]

def test_accepts_single_tuple_as_y_values_with_default_one_based_x():
    obs = ObservationSet((10, 20, 30))
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]

def test_accepts_single_list_as_y_values_with_zero_based_x():
    obs = ObservationSet([10, 20, 30], indexing_as_one=False)
    assert obs.Y == [10, 20, 30]
    assert obs.X == [0, 1, 2]

def test_accepts_positional_scalar_values_as_y_values():
    obs = ObservationSet(10, 20, 30)
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]

def test_rejects_too_few_positional_scalar_values():
    with pytest.raises(ValueError): ObservationSet(10, 20)
# ---------------------------------------------------------------------
# Positional dict input: {"Y": ..., "X": ...}
# ---------------------------------------------------------------------
def test_accepts_dict_with_y_only():
    obs = ObservationSet({"Y": [10, 20, 30]})
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]
    
def test_accepts_dict_with_y_only_zero_based_default_x():
    obs = ObservationSet({"Y": [10, 20, 30]}, indexing_as_one=False)
    assert obs.Y == [10, 20, 30]
    assert obs.X == [0, 1, 2]

def test_accepts_dict_with_y_and_x_lists():
    obs = ObservationSet({"Y": [10, 20, 30], "X": ["A", "B", "C"]})
    assert obs.Y == [10, 20, 30]
    assert obs.X == ["A", "B", "C"]

def test_accepts_dict_with_y_and_x_tuples():
    obs = ObservationSet({"Y": (10, 20, 30), "X": ("A", "B", "C")})
    assert obs.Y == [10, 20, 30]
    assert obs.X == ["A", "B", "C"]

def test_preserves_user_provided_zero_based_x():
    obs = ObservationSet({"Y": [10, 20, 30], "X": [0, 1, 2]})
    assert obs.Y == [10, 20, 30]
    assert obs.X == [0, 1, 2]
    
def test_rejects_dict_with_x_length_mismatch():
    with pytest.raises(ValueError): ObservationSet({"Y": [10, 20, 30], "X": ["A", "B"]})

# --------------------------------------------------------------------- 
# Positional paired input
# ---------------------------------------------------------------------
def test_accepts_list_of_xy_pairs():
    obs = ObservationSet([["A", 10], ["B", 20], ["C", 30]])
    assert obs.X == ["A", "B", "C"]
    assert obs.Y == [10, 20, 30]

def test_accepts_tuple_of_xy_pairs():
    obs = ObservationSet((("A", 10), ("B", 20), ("C", 30)))
    assert obs.X == ["A", "B", "C"]
    assert obs.Y == [10, 20, 30]
    
def test_accepts_dict_y_as_xy_pairs():
    obs = ObservationSet({"Y": [["A", 10], ["B", 20], ["C", 30]]})
    assert obs.X == ["A", "B", "C"]
    assert obs.Y == [10, 20, 30]
    
def test_rejects_dict_y_as_mapping_from_x_to_y():
    with pytest.raises(ValueError):
        ObservationSet({"Y": {"A": 10, "B": 20, "C": 30}})

# ---------------------------------------------------------------------
# Keyword input: Y=..., X=...
# ---------------------------------------------------------------------
def test_accepts_y_kwarg_with_default_one_based_x():
    obs = ObservationSet(Y=[10, 20, 30])
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]

def test_accepts_y_kwarg_with_zero_based_default_x():
    obs = ObservationSet(Y=[10, 20, 30], indexing_as_one=False)
    assert obs.Y == [10, 20, 30]
    assert obs.X == [0, 1, 2]

def test_accepts_y_and_x_kwargs():
    obs = ObservationSet(Y=[10, 20, 30], X=["A", "B", "C"])
    assert obs.Y == [10, 20, 30]
    assert obs.X == ["A", "B", "C"]
    
def test_preserves_zero_based_x_kwarg():
    obs = ObservationSet(Y=[10, 20, 30], X=[0, 1, 2])
    assert obs.Y == [10, 20, 30]
    assert obs.X == [0, 1, 2]

def test_rejects_x_kwarg_length_mismatch():
    with pytest.raises(ValueError): ObservationSet(Y=[10, 20, 30], X=["A", "B"])

# ---------------------------------------------------------------------
# Keyword input: points={...}
# ---------------------------------------------------------------------
def test_accepts_points_kwarg_with_y_only():
    obs = ObservationSet(points={"Y": [10, 20, 30]})
    assert obs.Y == [10, 20, 30]
    assert obs.X == [1, 2, 3]

def test_accepts_points_kwarg_with_y_and_x():
    obs = ObservationSet(points={"Y": [10, 20, 30], "X": ["A", "B", "C"]})
    assert obs.Y == [10, 20, 30]
    assert obs.X == ["A", "B", "C"]

def test_rejects_points_kwarg_y_as_mapping_from_x_to_y():
    with pytest.raises(ValueError):
        ObservationSet(Y={"A": 10, "B": 20, "C": 30})
    
def test_rejects_points_kwarg_that_is_not_dict():
    with pytest.raises(ValueError): ObservationSet(points=[10, 20, 30])

# ---------------------------------------------------------------------
# Mapping-style kwargs: A=10, B=20, C=30
# ---------------------------------------------------------------------
def test_accepts_arbitrary_keyword_mapping_from_x_to_y():
    obs = ObservationSet(A=10, B=20, C=30)
    assert obs.X == ["A", "B", "C"]
    assert obs.Y == [10, 20, 30]
    
def test_rejects_arbitrary_keyword_mapping_with_too_few_values():
    with pytest.raises(ValueError): ObservationSet(A=10, B=20)

# --------------------------------------------------------------------- 
# get_subsets behavior after default X generation
# ---------------------------------------------------------------------

def test_get_subsets_works_with_default_x_from_list_input():
    obs = ObservationSet([10, 20, 30, 40])
    assert obs.get_subsets(2) == [ [[1, 10], [2, 20]], [[1, 10], [3, 30]], [[2, 20], [3, 30]], [[1, 10], [4, 40]], [[2, 20], [4, 40]], [[3, 30], [4, 40]], ]

def test_get_subsets_works_with_default_zero_based_x_from_list_input():
    obs = ObservationSet([10, 20, 30, 40], indexing_as_one=False)
    assert obs.get_subsets(2) == [ [[0, 10], [1, 20]], [[0, 10], [2, 30]], [[1, 20], [2, 30]], [[0, 10], [3, 40]], [[1, 20], [3, 40]], [[2, 30], [3, 40]], ]

def test_get_subsets_works_with_user_provided_x():
    obs = ObservationSet({"Y": [10, 20, 30, 40], "X": ["A", "B", "C", "D"]})
    assert obs.get_subsets(2) == [ [["A", 10], ["B", 20]], [["A", 10], ["C", 30]], [["B", 20], ["C", 30]], [["A", 10], ["D", 40]], [["B", 20], ["D", 40]], [["C", 30], ["D", 40]], ]
    
def test_get_subsets_accepts_multiple_k_values_with_default_x():
    obs = ObservationSet([10, 20, 30])
    assert obs.get_subsets([1, 2]) == [ [[1, 10]], [[2, 20]], [[3, 30]], [[1, 10], [2, 20]], [[1, 10], [3, 30]], [[2, 20], [3, 30]], ]
    
def test_get_subsets_deduplicates_and_sorts_k_values():
    obs = ObservationSet([10, 20, 30])
    assert obs.get_subsets([2, 1, 2]) == [ [[1, 10]], [[2, 20]], [[3, 30]], [[1, 10], [2, 20]], [[1, 10], [3, 30]], [[2, 20], [3, 30]], ]
# ---------------------------------------------------------------------
# Invalid / empty input
# ---------------------------------------------------------------------
def test_rejects_no_input():
    with pytest.raises(ValueError): ObservationSet()
    
def test_rejects_empty_y_list():
    with pytest.raises(ValueError): ObservationSet([])
    
def test_rejects_two_item_y_list():
    with pytest.raises(ValueError): ObservationSet([10, 20])

def test_rejects_dict_without_y_or_valid_mapping():
    with pytest.raises(ValueError): ObservationSet({"Z": [10, 20, 30]})
    
def test_rejects_y_kwarg_with_too_few_values():
    with pytest.raises(ValueError): ObservationSet(Y=[10, 20])
    
def test_rejects_invalid_k_zero_after_valid_construction():
    obs = ObservationSet([10, 20, 30])
    with pytest.raises(ValueError): obs.get_subsets(0)
    
def test_accepts_k_equal_to_n_and_returns_the_full_set():
    obs = ObservationSet([10, 20, 30])
    assert obs.get_subsets(3) == [[[1, 10], [2, 20], [3, 30]]]

def test_rejects_k_greater_than_n_after_valid_construction():
    obs = ObservationSet([10, 20, 30])
    with pytest.raises(ValueError): obs.get_subsets(4)

def test_rejects_bool_k_after_valid_construction():
    obs = ObservationSet([10, 20, 30])
    with pytest.raises(TypeError): obs.get_subsets(True)
