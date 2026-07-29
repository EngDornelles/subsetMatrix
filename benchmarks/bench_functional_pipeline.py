"""Benchmark functional_pipeline.run (mask-walk + SQLite) against a plain
itertools.combinations equivalent writing to the identical schema, plus a
no-persistence itertools baseline for context on how much of the cost is
generation vs. I/O.

Run with:
    .\\.venv\\Scripts\\python.exe benchmarks\\bench_functional_pipeline.py
"""
import os
import sqlite3
import tempfile
import timeit
from itertools import combinations

from subsetmatrix.functional_pipeline import run

REPEATS_SMALL = 5
REPEATS_LARGE = 1  # cases with 100k+ findings: one clean timing, not five


def itertools_run(X: list, Y: list, k_values, db_path: str, batch_size: int = 10_000) -> int:
    """Same schema, same batching, same index-after-insert order as
    functional_pipeline.run -- only the generation method differs, so any
    gap in timing below is attributable to mask-walk vs itertools.combinations,
    not to the persistence layer."""
    n = len(Y)
    if isinstance(k_values, int):
        k_values = [k_values]

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("BEGIN")
    con.execute("CREATE TABLE IF NOT EXISTS findings (finding_id INTEGER PRIMARY KEY, mask INTEGER NOT NULL, k INTEGER NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS members (finding_id INTEGER NOT NULL, x_val REAL, y_val REAL NOT NULL)")

    finding_id = 0
    findings_batch = []
    members_batch = []
    for k in k_values:
        for combo in combinations(range(n), k):
            finding_id += 1
            mask = 0
            for j in combo:
                mask |= (1 << j)
            findings_batch.append((finding_id, mask, k))
            for j in combo:
                members_batch.append((finding_id, X[j], Y[j]))
            if len(findings_batch) >= batch_size:
                con.executemany("INSERT INTO findings VALUES (?, ?, ?)", findings_batch)
                con.executemany("INSERT INTO members VALUES (?, ?, ?)", members_batch)
                findings_batch.clear()
                members_batch.clear()

    if findings_batch:
        con.executemany("INSERT INTO findings VALUES (?, ?, ?)", findings_batch)
        con.executemany("INSERT INTO members VALUES (?, ?, ?)", members_batch)

    con.execute("CREATE INDEX IF NOT EXISTS idx_members_finding ON members(finding_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_members_x ON members(x_val)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_members_y ON members(y_val)")
    con.commit()
    con.close()
    return finding_id


def itertools_in_memory(X: list, Y: list, k_values) -> list:
    n = len(Y)
    if isinstance(k_values, int):
        k_values = [k_values]
    res = []
    for k in k_values:
        for combo in combinations(range(n), k):
            res.append([[X[j], Y[j]] for j in combo])
    return res


def _clean(path: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = path + suffix
        if os.path.exists(p):
            os.remove(p)


def timed_db_run(fn, X, Y, K, tmp_dir: str, repeats: int) -> float:
    """Each call needs a fresh db file (PRIMARY KEY findings.finding_id
    collides across repeats otherwise), so this can't reuse timeit.repeat
    on a single closure the way the in-memory benches do."""
    best = float("inf")
    for _ in range(repeats):
        path = os.path.join(tmp_dir, f"bench_{os.getpid()}_{id(fn)}.db")
        _clean(path)
        t0 = timeit.default_timer()
        fn(X, Y, K, path)
        t1 = timeit.default_timer()
        best = min(best, t1 - t0)
        _clean(path)
    return best


def bench():
    print("=" * 100)
    print("SQLite path: functional_pipeline.run vs itertools.combinations, both writing the same schema")
    print("=" * 100)
    header = (
        f"{'n':>4} {'K':>10} {'findings':>10} {'members':>10} "
        f"{'mask+sqlite(s)':>15} {'iter+sqlite(s)':>15} {'ratio':>7}"
    )
    print(header)
    print("-" * len(header))

    cases = [
        (8, list(range(2, 9)), REPEATS_SMALL),
        (12, list(range(2, 13)), REPEATS_SMALL),
        (16, list(range(2, 17)), REPEATS_SMALL),
        (18, [9], REPEATS_SMALL),          # 48,620 findings -- moderate
        (20, [10], REPEATS_LARGE),         # 184,756 findings -- old dense-matrix n<=20 ceiling
        (22, [11], REPEATS_LARGE),         # 705,432 findings -- past the old ceiling entirely
    ]

    sqlite_results = []
    with tempfile.TemporaryDirectory(dir=r"C:\Users\Avell\AppData\Local\Temp\claude\C--projetosPython-subsetMatrix\6bc5b9a2-4b67-4560-af4f-03e4839b5242\scratchpad") as tmp_dir:
        for n, K, repeats in cases:
            Y = [float(i) for i in range(n)]
            X = list(range(1, n + 1))
            n_findings = sum(len(list(combinations(range(n), k))) for k in K)
            n_members = sum(len(list(combinations(range(n), k))) * k for k in K)

            t_mask = timed_db_run(run, X, Y, K, tmp_dir, repeats)
            t_iter_db = timed_db_run(itertools_run, X, Y, K, tmp_dir, repeats)

            ratio = t_iter_db / t_mask if t_mask else float("inf")
            k_label = f"{K[0]}..{K[-1]}" if len(K) > 1 else str(K[0])
            print(
                f"{n:>4} {k_label:>10} {n_findings:>10} {n_members:>10} "
                f"{t_mask:>15.4f} {t_iter_db:>15.4f} {ratio:>6.2f}x"
            )
            sqlite_results.append((n, K, repeats, n_findings, t_mask))

    print()
    print("=" * 100)
    print("memory_only=True path: functional_pipeline.run vs itertools in-memory, plus cost of the sqlite tax")
    print("=" * 100)
    header2 = (
        f"{'n':>4} {'K':>10} {'findings':>10} "
        f"{'mask mem(s)':>13} {'iter mem(s)':>13} {'mem ratio':>10} {'sqlite tax':>11}"
    )
    print(header2)
    print("-" * len(header2))

    for n, K, repeats, n_findings, t_mask_sqlite in sqlite_results:
        Y = [float(i) for i in range(n)]
        X = list(range(1, n + 1))

        t_mask_mem = min(timeit.repeat(lambda: run(X, Y, K, memory_only=True), number=1, repeat=repeats))
        t_iter_mem = min(timeit.repeat(lambda: itertools_in_memory(X, Y, K), number=1, repeat=repeats))

        mem_ratio = t_iter_mem / t_mask_mem if t_mask_mem else float("inf")
        sqlite_tax = t_mask_sqlite / t_mask_mem if t_mask_mem else float("inf")
        k_label = f"{K[0]}..{K[-1]}" if len(K) > 1 else str(K[0])
        print(
            f"{n:>4} {k_label:>10} {n_findings:>10} "
            f"{t_mask_mem:>13.4f} {t_iter_mem:>13.4f} {mem_ratio:>9.2f}x {sqlite_tax:>10.2f}x"
        )


if __name__ == "__main__":
    bench()
