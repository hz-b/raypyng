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
- rayx **and** graxpy are optional dependencies, both installed via `pip install raypyng[rayx]`; any import of either must be guarded with a try/except.
- On macOS, use `multiprocessing.get_context("fork")` for `ProcessPoolExecutor` (avoids spawn re-import issues).
- On macOS, never prepend `xvfb-run` to the RAY-UI command; the runner skips it automatically when `config.opsys == "Darwin"`.
- RAY-UI binary path on macOS: `<install_dir>/Ray-UI.app/Contents/MacOS/Ray-UI` (not `<install_dir>/Contents/MacOS/Ray-UI`).

## rayx integration status (work in progress)

The `integrate_rayx` branch (now merged to `develop`) adds a GPU ray-tracer backend.

Key files:
- `src/raypyng/rayx_runner.py` — `RayXAPI`: load/trace/export wrapper around rayx
- `src/raypyng/graxpy_efficiency.py` — grating efficiency via RCWA (graxpy)
- `examples/rayx_comparison/` — scripts comparing rayx vs RAY-UI output

How the rayx export works:
- `RayXAPI.export()` writes per-simulation raw-ray CSVs with an extra `{element}_W` column = per-ray `|E_x|² + |E_y|² + |E_z|²` normalised to the source total.
- `PostProcess._extract_intensity()` detects the `_W` column and sums it instead of counting rows, giving intensity-weighted `NumberRaysSurvived`.
- graxpy efficiency is applied on top for elements at or after the grating (rayx does not apply diffraction efficiency to E-fields internally).

Known remaining discrepancy:
- rayx passes ~8–10× more rays through the exit slit than RAY-UI at grating energies (200–2200 eV). Root cause: rayx's plane grating monochromator does not reproduce RAY-UI's vertical beam dispersion at the exit slit plane. This is a rayx engine physics issue, not a raypyng bug.

## Active branches

| Branch | Purpose |
|--------|---------|
| `main` | stable releases |
| `develop` | integration target (rayx integration merged here) |
| `fix/macos-integration` | macOS runtime fixes |
| `integrate_rayx` | rayx engine integration (open PR → develop) |
