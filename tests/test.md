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

## Environment

- `tests/smoke/`: set `RAYUI_PATH` to a local RAY-UI install.
- `tests/platform/`: same `RAYUI_PATH` on Windows and macOS; Linux smoke tests also need `xvfb-run`.
- `tests/functional/`: set `RAYUI_STABLE_PATH` and `RAYUI_DEV_PATH`, or pass `--stable-ray-path` and `--dev-ray-path`.
- CI runs only the `not requires_ray_ui` subset on GitHub-hosted Linux. The `tests/smoke/`, `tests/platform/`, and `tests/functional/` layers are local-environment checks that need a RAY-UI installation.

## Notes

- `manual_tests/` stays untouched and is not part of automated runs.
