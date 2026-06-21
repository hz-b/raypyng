# raypyng — Claude Code project rules

## Repository overview

raypyng is a Python wrapper around RAY-UI (and optionally rayx) for synchrotron beamline optical simulations. It spawns RAY-UI as a subprocess, loads `.rml` files, runs traces, exports results, and post-processes them.

Key paths:
- `src/raypyng/` — main package
- `src/raypyng/simulate.py` — `Simulate` class and worker functions
- `src/raypyng/runner.py` — `RayUIRunner` / `RayUIAPI`
- `src/raypyng/config.py` — OS-aware path defaults
- `src/raypyng/rayx_runner.py` — `RayXAPI` (rayx engine wrapper)
- `examples/` — usage examples; `examples/rayx_comparison/` for engine comparison
- `tools/bootstrap.sh` — create `.venv` with uv + Python 3.12, install dev deps
- `tools/build_docs.sh` — build Sphinx docs

## Workflow rules

- **Never commit or push unless explicitly asked.** Stage, diff, and review are fine; `git commit` and `git push` require a direct user instruction.
- **Never run simulations without asking first.** Simulations are long-running (minutes), consume CPU, and write output files. Always confirm before executing `sim.run()` or any simulation script.
- **Always check the current branch** before making changes. We often work on feature branches (`fix/macos-integration`, `integrate_rayx`, etc.).

## Code conventions

- Python 3.12, line length 100 (black + ruff enforced via pre-commit).
- rayx is an **optional** dependency (`pip install raypyng[rayx]`); any import must be guarded with a try/except.
- On macOS, use `multiprocessing.get_context("fork")` for `ProcessPoolExecutor` (avoids spawn re-import issues).
- On macOS, never prepend `xvfb-run` to the RAY-UI command; the runner skips it automatically when `config.opsys == "Darwin"`.
- RAY-UI binary path on macOS: `<install_dir>/Ray-UI.app/Contents/MacOS/Ray-UI` (not `<install_dir>/Contents/MacOS/Ray-UI`).

## Active branches

| Branch | Purpose |
|--------|---------|
| `main` | stable releases |
| `develop` | integration target |
| `fix/macos-integration` | macOS runtime fixes (current work) |
| `integrate_rayx` | rayx engine integration |
