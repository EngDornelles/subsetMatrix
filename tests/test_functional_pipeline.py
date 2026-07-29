import sqlite3
from itertools import combinations
from math import comb

import pytest
from subsetmatrix.functional_pipeline import run


def test_run_persists_expected_finding_and_member_counts(tmp_path):
    X = [10, 20, 30, 40, 50]
    Y = [1.0, 2.0, 3.0, 4.0, 5.0]
    db_path = str(tmp_path / "findings.db")

    total = run(X, Y, [2, 3], db_path)

    expected_findings = comb(5, 2) + comb(5, 3)
    assert total == expected_findings

    con = sqlite3.connect(db_path)
    assert con.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == expected_findings

    expected_members = comb(5, 2) * 2 + comb(5, 3) * 3
    assert con.execute("SELECT COUNT(*) FROM members").fetchone()[0] == expected_members
    con.close()


def test_run_matches_itertools_combinations(tmp_path):
    X = [1, 2, 3, 4, 5]
    Y = [10.0, 20.0, 30.0, 40.0, 50.0]
    db_path = str(tmp_path / "findings.db")

    run(X, Y, [3], db_path)

    con = sqlite3.connect(db_path)
    got = {
        frozenset(row)
        for row in con.execute(
            """
            SELECT finding_id, y_val FROM members
            """
        ).fetchall()
    }
    # reconstruct combos by finding_id -> set of Y values, compare against itertools ground truth
    by_finding = {}
    for finding_id, y_val in con.execute("SELECT finding_id, y_val FROM members"):
        by_finding.setdefault(finding_id, set()).add(y_val)
    con.close()

    expected = {frozenset(Y[j] for j in combo) for combo in combinations(range(5), 3)}
    assert {frozenset(v) for v in by_finding.values()} == expected


def test_existential_range_query(tmp_path):
    X = [1, 2, 3, 4, 5]
    Y = [10.0, 20.0, 30.0, 40.0, 50.0]
    db_path = str(tmp_path / "findings.db")
    run(X, Y, [2], db_path)

    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT DISTINCT finding_id FROM members WHERE x_val > 3 AND y_val < 50"
    ).fetchall()
    con.close()
    # X and Y are paired per index (X[j], Y[j]); only (X=4, Y=40) satisfies both
    # bounds on the same row (X=5 pairs with Y=50, which fails y_val < 50), so
    # every finding containing that member matches: 4 partners out of {1,2,3,5}
    assert len(rows) == 4


def test_universal_range_query(tmp_path):
    X = [1, 2, 3, 4, 5]
    Y = [10.0, 20.0, 30.0, 40.0, 50.0]
    db_path = str(tmp_path / "findings.db")
    run(X, Y, [2], db_path)

    con = sqlite3.connect(db_path)
    rows = con.execute(
        """
        SELECT finding_id FROM members
        GROUP BY finding_id
        HAVING MIN(x_val) > 3 AND MAX(y_val) < 100
        """
    ).fetchall()
    con.close()
    # every member above X=3 means both members drawn from {4, 5} -> exactly 1 pair
    assert len(rows) == 1


def test_rejects_mismatched_lengths(tmp_path):
    with pytest.raises(ValueError):
        run([1, 2, 3], [1.0, 2.0], [1], str(tmp_path / "findings.db"))


def test_rejects_invalid_k(tmp_path):
    with pytest.raises(ValueError):
        run([1, 2, 3], [1.0, 2.0, 3.0], [5], str(tmp_path / "findings.db"))


def test_memory_only_returns_subsets_matching_itertools(tmp_path):
    X = [1, 2, 3, 4, 5]
    Y = [10.0, 20.0, 30.0, 40.0, 50.0]

    res = run(X, Y, [2, 3], memory_only=True)

    expected = {
        frozenset((X[j], Y[j]) for j in combo)
        for k in (2, 3)
        for combo in combinations(range(5), k)
    }
    got = {frozenset(tuple(pair) for pair in subset) for subset in res}
    assert got == expected
    assert len(res) == comb(5, 2) + comb(5, 3)


def test_memory_only_preserves_ascending_order_per_subset():
    # X is monotonically increasing with index, so each subset's pairs should
    # come out in ascending original-index order (same convention as
    # ObservationSet.get_subsets / the SQLite path's member insert order).
    X = [1, 2, 3, 4]
    Y = [10.0, 20.0, 30.0, 40.0]

    res = run(X, Y, [3], memory_only=True)

    for subset in res:
        x_values = [pair[0] for pair in subset]
        assert x_values == sorted(x_values)


def test_memory_only_does_not_touch_disk(tmp_path):
    X = [1, 2, 3]
    Y = [1.0, 2.0, 3.0]

    run(X, Y, [2], memory_only=True)

    assert list(tmp_path.iterdir()) == []


def test_memory_only_without_db_path_does_not_raise():
    res = run([1, 2, 3], [1.0, 2.0, 3.0], [2], memory_only=True)
    assert len(res) == comb(3, 2)


def test_missing_db_path_without_memory_only_raises():
    with pytest.raises(ValueError):
        run([1, 2, 3], [1.0, 2.0, 3.0], [2])
