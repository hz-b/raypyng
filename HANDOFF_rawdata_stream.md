# Handoff: feature/rawdata-stream

## What this branch does

Adds support for RAY-UI's `rawdata` background command, which streams raw ray
data directly from RAY-UI memory as a numpy `.npy` blob — no intermediate
files written to disk.

When a simulation exports `RawRaysOutgoing` / `RawRaysIncoming` / `RawRaysBeam`,
raypyng now calls `api.rawdata(element, item_id)` instead of `api.export()`,
returning a numpy structured array in-memory (columns: RN RS RO OX OY OZ DX DY
DZ EN PL S0 S1 S2 S3).

## Why it is parked

The `rawdata` command does not exist in any official RAY-UI release yet. It lives
on the RAY-UI source branch `feature/rawrays-stream` at
`/home/simone/projects/raypyng/RAY-UI`. A working native build is described in
`memory/rayui_rawdata_build.md` (build script:
`RAY-UI/tools/build_rawdata_rayui.sh`, deploy target:
`/home/simone/Applications/Ray-UI-development-stream`).

Resume this branch once `rawdata` is merged into an official RAY-UI release.

## Files changed vs develop

| File | What changed |
|------|-------------|
| `src/raypyng/runner.py` | `RayUIAPI.rawdata()`, `_read_bytes()`, `_readline_with_timeout()`; bug fix in `_wait_for_cmd_io` (see below) |
| `src/raypyng/simulate.py` | Worker uses `api.rawdata()` for `_RAWRAYS_ITEM_IDS`; `_write_rawrays_csv()` helper |
| `src/raypyng/postprocessing.py` | Minor adjustments for rawdata-written CSV format |
| `tests/test_rawdata_integration.py` | Integration tests (skipped if dev binary absent) |
| `tests/unit/test_rawdata_runner.py` | Unit tests for `rawdata()` / `_read_bytes()` |
| `tests/unit/test_postprocess_rawdata.py` | Unit tests for postprocessing rawdata output |
| `tests/manual_tests/runner_demo/terminal_commands.md` | Commands to drive RAY-UI manually in a terminal |
| `tests/manual_tests/runner_demo/example_runner.py` | Example using the rawdata API directly |

## Bug fix included (worth merging to develop independently)

`runner.py` — `_wait_for_cmd_io`: newer RAY-UI dev builds emit an
`"export path: /tmp/..."` info line that starts with `"export"`. The old parser
mistook it for the status echo and raised "unsupported reply" on every
`api.export()` call. Fixed by requiring the matched line to end with `"success"`
or `"failed"` before breaking. All existing tests pass.

## Benchmark results (same binary, serial mp=1, 30 sims, 50k rays)

| Path | Time |
|------|------|
| develop — file export | 210.9 s (7.02 s/sim) |
| feature — rawdata stream | 215.1 s (7.15 s/sim) |

The rawdata stream eliminates ~450 ms of file I/O per export call (confirmed
by micro-benchmark: 13× faster for Dipole 50k rays, 632× for small exports).
At 50k rays serial, the gain is swamped by the ~7 s trace time per sim (I/O is
~13% of total). The stream is expected to win more clearly with parallel workers
(MP ≥ 4, where file I/O contention matters) or with shorter traces.

## How to test

Requires the rawdata-capable RAY-UI binary at
`/home/simone/Applications/Ray-UI-development-stream/rayui`:

```bash
# unit + integration tests
python -m pytest tests/unit/test_rawdata_runner.py \
                 tests/unit/test_postprocess_rawdata.py \
                 tests/test_rawdata_integration.py -v

# end-to-end fair benchmark (same binary, both branches)
MP=4 bash /home/simone/projects/raypyng/benchmark_fair.sh
```
