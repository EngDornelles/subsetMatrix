# Going 4 Rust — roadmap for a native extension on `functional`

This document captures the reasoning and the concrete steps for adding a
Rust extension to this branch, written up after a benchmarking session
that exhausted the pure-Python/numpy options first. Read this before
starting the Rust work so the "why" isn't lost.

## 1. Why: what the benchmarks actually showed

The `functional` branch exists to explore an inline, non-OOP alternative
to `ObservationSet` (see [`.agents/observations.md`](.agents/observations.md)
for the full trail). Across several rounds of drafting
`src/subsetmatrix/functional.py` and benchmarking it:

- A per-row numpy-decode loop is ~10-12x slower than batching the same
  decode through one broadcasted call (the trick `engine.generateMatrix`
  already uses). Fixing that closed the gap to parity with `engine.py` —
  but parity with `engine.py` isn't the goal, since `ObservationSet`
  already calls `engine.generateMatrix` internally.
- The real comparison — `ObservationSet.get_subsets` (dense matrix →
  `np.nonzero` → reshape → assemble `[X,Y]` pairs) vs an itertools
  baseline doing the same assembly — showed itertools winning by
  ~1.3-1.4x, at n=20, k=14/15/16, 100 reps each.
- That gap is *not* OOP overhead (a class wrapping the same three calls
  costs nanoseconds, not 30-40%). It's the dense-matrix/mask round-trip
  itself: `itertools.combinations` is a C iterator yielding index tuples
  directly, so the only Python-level cost is the list-comprehension
  lookup. Every matrix- or mask-based approach pays extra Python-level
  cost to get from "compact representation" back to "actual member
  values" — see `observations.md`'s 2026-07-28 entries for the same
  conclusion reached independently via `functional_pipeline.py`.

Net conclusion: no pure-Python or numpy-broadcast approach in this repo
beats `itertools.combinations` once real member data has to come back
out, because `itertools.combinations` already runs below the Python
object layer and everything else here doesn't. Closing that gap means
leaving the Python object layer entirely for the hot loop — hence Rust.

## 2. Architecture decision: in-process extension, not a standalone API

Two shapes were considered:

1. **PyO3 extension module** — compiles to a native module Python
   `import`s directly (a `.pyd` on Windows). Calls are in-process,
   function-call overhead only, no serialization.
2. **Standalone Rust binary/service**, called from Python via subprocess
   or a local socket/HTTP API.

**Chosen: (1).** The entire point of reaching for Rust here is to avoid
per-item overhead; a separate process reintroduces exactly that in the
form of IPC + serialization on every call. A standalone binary only
makes sense if the Rust piece needs to run outside Python too (CLI,
service) — not the goal on this branch.

## 3. The big-number caveat

Rust's fixed-width integers (`u64`, `i64`, `u128`, …) don't overflow into
arbitrary precision the way Python's `int` does by default — this is a
deliberate tradeoff (fixed-width is what makes them fast; Python's `int`
pays an arbitrary-precision tax on *every* integer op, which is part of
why the pure-Python paths lose in the first place).

- For this repo: subset masks fit comfortably in `u128` for any
  realistic `n` (`engine.generateMatrix` already caps dense generation
  at `n<=20`; even ungated mask generation stays well under 128 bits for
  any n this project would realistically see).
- If a value genuinely needs arbitrary precision (as has happened
  before in an unrelated project, `Multinterp`), the `num-bigint` crate
  gives Rust the same behavior as Python's `int` — but it's opt-in, not
  the default, so it should only be reached for on the specific values
  that need it, not applied blanket "just in case."

## 4. Environment check (as of 2026-07-29, this machine)

- Rust (`rustc`/`cargo`): **not installed**.
- `maturin`: **not installed**.
- MSVC build tools: **already installed** — `vswhere` found "Ferramentas
  de Build do Visual Studio 2026" with the C++ (`VC.Tools.x86.x64`)
  component present. This is normally the slow/painful part of a Rust
  setup on Windows and it's already done.

Re-check before assuming this is still accurate — it's a snapshot, not
a guarantee (see governance note in `.agents/observations.md`).

## 5. Setup steps

1. **Install Rust.** MSVC build tools are already present, so target the
   default `x86_64-pc-windows-msvc` host (not the GNU target — MSVC is
   what PyO3/maturin expect for standard wheel compatibility):
   ```powershell
   winget install Rustlang.Rustup
   ```
   or run `rustup-init.exe` from rustup.rs. Restart the shell afterward
   so `cargo`/`rustc` land on `PATH`.

2. **Install maturin** into the project venv (it builds the PyO3 crate
   into a wheel and can install it straight into the venv):
   ```powershell
   .\.venv\Scripts\pip.exe install maturin
   ```

3. **Scaffold the crate as a subproject**, kept separate from the
   existing Python package:
   ```
   subsetMatrix/
   ├── src/subsetmatrix/       # existing Python package, untouched
   └── rust/subsetmatrix_rs/   # new: maturin init here
   ```
   ```powershell
   cd rust
   maturin new subsetmatrix_rs --bindings pyo3
   ```
   Add the `numpy` crate for zero-copy array returns. Add `num-bigint`
   only if/when a specific value actually needs arbitrary precision
   (see §3) — default to `u64`/`u128`.

4. **Iterate** from `rust/subsetmatrix_rs/`:
   ```powershell
   .\..\..\.venv\Scripts\maturin.exe develop --release
   ```
   Installs the built module straight into `.venv` as an importable
   module (e.g. `import subsetmatrix_rs`) — no separate packaging step
   needed while prototyping.

5. **First target to port**: the mask-generation-and-decode loop —
   `engine.iter_k_masks` plus the member-extraction bit-walk from
   `functional_pipeline.py` (`while m: low = m & -m; ...`). Have the
   Rust function take `n`, `k`, `X`, `Y` and return the assembled
   `[[X[j],Y[j]], ...]`-per-subset structure directly, so it can be
   benchmarked against the same itertools baseline used throughout this
   session — that number is the one that says whether this was worth
   it.

6. **Don't port validation/plumbing to Rust.**
   `payload_args_validation.py`'s duck-typed branching is exactly the
   kind of code that fights Rust's type system for no speed benefit.
   Keep that in Python; call into Rust only for the hot numeric loop.

## 6. Definition of done for the first pass

A `subsetmatrix_rs` module, importable from the project venv, exposing
one function that reproduces `ObservationSet.get_subsets`'s output for a
given `n`/`k`/`X`/`Y`, benchmarked head-to-head against the itertools
baseline at the same n/k values used in this session's benchmarks
(n=20, k=14/15/16, 100 reps). If it doesn't beat itertools by a
meaningful margin there, the premise needs revisiting before going
further, not the implementation.

## 7. Results from the first implementation pass (2026-07-29)

`rust/subsetmatrix_rs/src/lib.rs` now has five real functions plus two
throwaway diagnostics (`_count_combinations`, `_generate_masks_only`,
still present, underscore-prefixed, not part of any contract). In the
order they were tried, with what each one actually showed:

1. **`combinations_indices(n, k) -> Vec<Vec<usize>>`** — mask-walk +
   bit-decode, same algorithm as `engine.iter_k_masks` /
   `functional_pipeline.py`, returned via PyO3's automatic nested-`Vec`
   conversion. Result: **~3.6-4.9x slower than itertools** for
   generation alone (n=20, k=14/15/16). Diagnosed via two throwaway
   functions: the mask-generation loop itself is fast (beats itertools);
   the cost is entirely PyO3 constructing one Python list object per
   subset (38,760 of them at k=14) instead of one bulk structure.

2. **`generate_matrix(n, k_values) -> PyArray2<u8>`** (dense matrix,
   one flat buffer, one bulk numpy return) and
   **`combinations_indices_array(n, k) -> PyArray2<usize>`** (packed
   index matrix, same idea without the dense matrix's wasted n-k
   "off" columns) — both fix the generation-only number decisively
   (dense matrix: **2.6x faster** than itertools, ~6.8x faster than
   `engine.generateMatrix`). But the *full* pipeline (matrix/array →
   `.tolist()` or `np.nonzero`+reshape → assemble `[X,Y]` pairs) lands
   back at **1.1-1.3x slower** than itertools — `.tolist()` alone on the
   packed array cost *more* than the entire Rust generation step,
   because turning array cells into individually-addressable Python
   objects pays the same tax as (1), just relocated into numpy's
   `.tolist()` internals instead of PyO3's `Vec<Vec<T>>` conversion.

3. **`combinations_values(k, x, y) -> PyArray3<f64>`** — the one that
   actually won. Fuses generation *and* the `X[j]`/`Y[j]` lookup into
   one Rust pass, straight into one pre-allocated `(count, k, 2)` f64
   buffer, one bulk numpy array back. **20-37x faster than itertools**,
   ~30-53x faster than `ObservationSet`, at n=20, k=14/15/16. This is
   `numbers_only=True` in `native_backend.get_subsets_native` — numeric
   X/Y only (the Multinterp use case), deliberately departing from the
   index-only architecture in exchange for never materializing a single
   per-subset Python object.

4. **`python_typed=True`** (default) added on top of (3): calls
   `.tolist()` on the array before returning, for callers that want
   native Python floats back. Confirmed via a proper 100-rep benchmark
   at a larger scale (K=range(4,17), n=20, ~1.05M subsets) that this
   **erases nearly all of (3)'s advantage** — lands ~10% *slower* than
   itertools, statistically indistinguishable from the plain index-only
   default path (both ~10-12% behind itertools, both still ~26-28%
   ahead of `ObservationSet`). Confirms the rule from (2): the win is
   exclusively in staying a bulk array; asking for native Python types
   back gives essentially all of it up, regardless of which function
   produced the array.

5. **`combinations_indices_hand_built(n, k)`** — an experiment prompted
   by a sharp question: if itertools is fast partly *because* it's
   hand-written C with no generic conversion layer, does bypassing
   PyO3's automatic `Vec<Vec<T>>` conversion and hand-building each
   tuple via raw `pyo3::ffi` calls (`PyTuple_New`/`PyTuple_SetItem`,
   `PyList_New`/`PyList_SetItem` — the same calls itertools' own C
   source uses) close the gap from (1)? Tested 3 reps, k=14/15/16,
   n=20: **yes, substantially** — ~2.5-3.3x faster than (1)'s automatic
   conversion, confirming a real chunk of (1)'s slowdown was PyO3's
   generic-conversion tax specifically, not something inherent to
   crossing into Python from compiled code. But it still lands
   **~1.4-1.6x slower than itertools**, not a tie. The remaining gap is
   most likely algorithmic, not construction-related: Gosper's hack
   does several arithmetic ops per mask (XOR, shift, AND, ADD, and a
   division), while itertools' internal algorithm directly increments
   a small index array — strictly less work per combination. Not yet
   isolated further; see the open items below.

**Net takeaway so far:** the only strategy that has actually beaten
itertools end-to-end is fusing generation with the value lookup and
returning one bulk array (3). Everything that has to hand back
individually-addressable Python objects — however it's built, in
whichever language — converges to roughly itertools' own cost or
somewhat behind it. That convergence point (1.1-1.6x behind, across
three different "make Python objects" strategies: generic PyO3
conversion, numpy `.tolist()`, hand-built ffi) is consistent enough
across independent measurements to trust as a real ceiling, not noise.

### Open items for a later session (not yet benchmarked)

Raised at the end of this session, worth testing before assuming either
way:

- **Brute-force iterate `1..2^n` with a popcount filter**, instead of
  Gosper's hack, to find all masks with `k` set bits. Cheaper per step
  (an increment plus one hardware `POPCNT` instruction vs Gosper's
  hack's several ops), but visits *every* value up to `2^n` instead of
  only the `C(n,k)` matches. Honest caveat before trying it: this is
  only a good trade when `C(n,k)` is a large fraction of `2^n` (k near
  `n/2`). At the k values benchmarked all session (14/15/16 at n=20),
  `C(n,k)` is only 0.5-3.7% of `2^n` — brute force would iterate ~30-200x
  more values than it needs to for exactly the cases already measured,
  and could easily lose. Needs benchmarking across a wider k range
  (including k near 10) before drawing a conclusion, not just the tail
  values used elsewhere in this doc.
- **A precomputed popcount lookup table** (`1..2^20`) instead of calling
  popcount at generation time. Flag before building it: `u128::count_ones()`/
  `u32::count_ones()` already compile to a single hardware `POPCNT`
  instruction on any target that supports it — a lookup table trades
  that for a memory/cache access, which is not obviously faster and
  could be slower once the table exceeds L1 cache size (a 2^20-entry
  byte table is ~1MB, past typical L1, into L2). Worth measuring, not
  assuming.
- **Mask width, u128 vs u64.** `going_4_rust.md` §3 picked `u128` for
  "any realistic n," but Gosper's hack's costliest step is the
  division, and 128-bit division has no native hardware instruction on
  current CPUs — it's compiler-emulated multi-word long division,
  meaningfully slower than the single hardware instruction a 64-bit
  division gets. Since the dense-matrix path is already capped at
  `n<=20` (trivially fits `u64`), this may be a real, easily-fixed cost
  with no corresponding benefit today. Worth an A/B benchmark of the
  existing functions with `u64` masks before deciding whether the
  original "consistency" reasoning still holds.
- **Conversion to native Python types remains a hard bar.** Every
  attempt to hand back individually-addressable Python objects (however
  it's constructed) has landed within roughly the same narrow band,
  behind itertools. This may just be a real floor, not a solved-later
  problem — noted here so it isn't mistaken for an oversight.
