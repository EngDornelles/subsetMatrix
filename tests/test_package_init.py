def test_top_level_imports_expose_public_api():
    from subsetmatrix import ObservationSet, generateMatrix, iter_k_masks, cardinality, extract_k_window

    obs = ObservationSet({"Y": [10, 20, 30, 40], "X": ["A", "B", "C", "D"]})
    assert obs.get_subsets(2) == [
        [["A", 10], ["B", 20]],
        [["A", 10], ["C", 30]],
        [["B", 20], ["C", 30]],
        [["A", 10], ["D", 40]],
        [["B", 20], ["D", 40]],
        [["C", 30], ["D", 40]],
    ]
    assert generateMatrix(4).shape == (11, 4)
    assert list(iter_k_masks(4, 2)) == [3, 5, 6, 9, 10, 12]
    assert cardinality(5) == 2
    assert extract_k_window(generateMatrix(4, [1, 2, 3]), 2).shape == (6, 4)
