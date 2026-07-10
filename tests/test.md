# Tests

Use `uv` with Python 3.12.

## Setup

```bash
uv venv --python 3.12
uv pip install -e '.[dev]'
```

## Run

```bash
uv run --python 3.12 pytest tests/unit
uv run --python 3.12 pytest -m "not requires_ray_ui"
uv run --python 3.12 pytest tests/smoke
uv run --python 3.12 pytest tests/platform
uv run --python 3.12 pytest tests/functional --stable-ray-path /path/to/RAY-UI --dev-ray-path /path/to/RAY-UI-dev
```

## What Each File Checks

### Unit tests

- `tests/unit/test_diodes.py`: loads diode calibration data and checks interpolation plus error handling.
- `tests/unit/test_graxpy_efficiency.py`: reads grating inputs and verifies efficiency export logic with mocked `graxpy`.
- `tests/unit/test_inspect.py`: builds and saves inspection tables from simulated results.
- `tests/unit/test_mutable_config_properties.py`: ensures config lists copy input and reject invalid mutation patterns.
- `tests/unit/test_postprocess_unit.py`: validates post-processing helpers for intensity, percentage, flux, and FWHM calculations.
- `tests/unit/test_rayui_recap.py`: rebuilds recap CSVs from saved RAY-UI output folders and checks missing-file errors.
- `tests/unit/test_recipes.py`: checks recipe helpers switch exports and reflectivity settings correctly.
- `tests/unit/test_rml_xmltools.py`: parses and serializes RML XML and sanitizes element attributes.
- `tests/unit/test_runner_api.py`: exercises runner/API command quoting, process control, and transcript handling.
- `tests/unit/test_simulate_eta.py`: verifies ETA estimates and progress updates from scan metadata.
- `tests/unit/test_simulate_exports.py`: checks export validation for supported and unsupported export types.
- `tests/unit/test_simulate_windows_multiprocessing.py`: validates Windows multiprocessing setup and shutdown behavior.
- `tests/unit/test_simulation_class.py`: checks analyze mode toggles and reflectivity handling.
- `tests/unit/test_vls_grating.py`: verifies VLS grating coefficient conversions and known baselines.
- `tests/unit/test_wave_helper.py`: discovers wave helper energy files and converts them into paths.

### Smoke tests

- `tests/smoke/test_analyze_smoke.py`: runs a small `Simulate` job with analyze on and checks expected output files.
- `tests/smoke/test_no_analyze_smoke.py`: runs the same job with analyze off and checks raw-ray export output.
- `tests/smoke/test_rayui_smoke.py`: starts the runner/API, loads an RML, traces, saves, and exports data.

### Platform tests

- `tests/platform/test_linux_raypyng_analysis_export_mismatch.py`: runs a real RAY-UI probe on Linux and checks analysis export names.
- `tests/platform/test_windows_example00_smoke.py`: runs the example-00 script end to end and checks the generated output.
- `tests/platform/test_windows_multiprocessing_smoke.py`: runs the Windows multiprocessing probe and checks for clean worker shutdown.

### Functional tests

- `tests/functional/test_version_regression.py`: compares stable vs dev RAY-UI runs and checks detector metrics and outputs.
- For version-regression runs, the base tolerance can be changed with `--tolerance`, and the metric multipliers plus `numberRays` can be adjusted directly in `tests/functional/test_version_regression.py`.

### Manual tests

`tests/manual_tests/` is kept outside automated runs.
