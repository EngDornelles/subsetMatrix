"""Functional-style prototype, kept deliberately separate from ObservationSet.

No classes, no dense matrix. Subsets are walked mask-by-mask straight off
`engine.iter_k_masks` (plain Python ints, so there's no dtype/memory cap tied
to n the way generateMatrix's dense array has) and each member is written to
SQLite as it's found. The whole generate -> persist path lives in one
function on purpose: this is an experiment in staying inline instead of
decomposing into a call per concern.

Schema is normalized long-format, not one-column-per-position: a wide
`x_1..x_n` table makes "does any/every member satisfy X > bound" require
either a giant OR chain or a column list that changes with n. One row per
(finding, member) instead makes both queries plain SQL:

    -- at least one member of the subset lands in the box (existential)
    SELECT DISTINCT finding_id FROM members WHERE x_val > :b1 AND y_val < :b2;

    -- every member of the subset lands in the box (universal)
    SELECT finding_id FROM members
    GROUP BY finding_id
    HAVING MIN(x_val) > :b1 AND MAX(y_val) < :b2;

    -- reconstruct a finding's original combo (join back to X/Y by mask bits,
    -- or just read the finding's rows out of members and match against the
    -- `findings` table for its k / mask)
    SELECT k, mask FROM findings WHERE finding_id = ?;

Assumes X and Y are numeric (int/float) -- that's the whole point of this
schema. Non-numeric X (labels, dates) isn't what this prototype is for;
ObservationSet's dataset_payload.py already covers that flexibility.

`memory_only=True` skips SQLite entirely and returns the findings as a
plain in-memory list -- the same [[X[j], Y[j]], ...]-per-subset shape
ObservationSet.get_subsets returns. Benchmarking showed SQLite persistence
costs a roughly constant ~15-20x over pure in-memory generation regardless
of n (see benchmarks/bench_functional_pipeline.py); for small batches
where you don't need a queryable file, that tax isn't worth paying.
"""

import sqlite3

from subsetmatrix.engine import iter_k_masks


def run(
    X: list,
    Y: list,
    k_values: int | list[int],
    db_path: str | None = None,
    batch_size: int = 10_000,
    memory_only: bool = False,
) -> int | list[list[list]]:
    """Generate every k-sized subset of range(len(Y)).

    By default persists to db_path and returns the number of findings
    written. With memory_only=True, db_path is ignored, nothing touches
    disk, and the full list of findings is returned instead (one entry per
    subset, each a list of [X[j], Y[j]] pairs, ascending by index -- same
    shape and order as ObservationSet.get_subsets).

    Indexes are built after the bulk insert, not before -- maintaining an
    index row-by-row during a large insert is slower than building it once
    over the finished table, and the whole reason to reach for SQLite here
    is to keep the explosion in row count from also exploding write time.
    """
    n = len(Y)
    if len(X) != n:
        raise ValueError(f"X and Y must be the same length. X:{len(X)} Y:{n}")
    if isinstance(k_values, int):
        k_values = [k_values]
    for k in k_values:
        if not 0 < k <= n:
            raise ValueError(f"k must satisfy 0 < k <= n. Received k={k}, n={n}.")

    if memory_only:
        res = []
        for k in k_values:
            for mask in iter_k_masks(n, k):
                members = []
                m = mask
                while m:
                    low = m & -m
                    j = low.bit_length() - 1
                    members.append([X[j], Y[j]])
                    m ^= low
                res.append(members)
        return res

    if db_path is None:
        raise ValueError("db_path is required unless memory_only=True.")

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("BEGIN")
    con.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            finding_id INTEGER PRIMARY KEY,
            mask INTEGER NOT NULL,
            k INTEGER NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS members (
            finding_id INTEGER NOT NULL,
            x_val REAL,
            y_val REAL NOT NULL
        )
    """)

    finding_id = 0
    findings_batch = []
    members_batch = []

    for k in k_values:
        for mask in iter_k_masks(n, k):
            finding_id += 1
            findings_batch.append((finding_id, mask, k))

            m = mask
            while m:
                low = m & -m
                j = low.bit_length() - 1
                members_batch.append((finding_id, X[j], Y[j]))
                m ^= low

            if len(findings_batch) >= batch_size:
                con.executemany("INSERT INTO findings VALUES (?, ?, ?)", findings_batch)
                con.executemany("INSERT INTO members VALUES (?, ?, ?)", members_batch)
                findings_batch.clear()
                members_batch.clear()

    if findings_batch:
        con.executemany("INSERT INTO findings VALUES (?, ?, ?)", findings_batch)
        con.executemany("INSERT INTO members VALUES (?, ?, ?)", members_batch)

    # built after the data lands, per the docstring above
    con.execute("CREATE INDEX IF NOT EXISTS idx_members_finding ON members(finding_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_members_x ON members(x_val)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_members_y ON members(y_val)")

    con.commit()
    con.close()
    return finding_id
