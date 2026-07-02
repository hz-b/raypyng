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
uv run --python 3.12 pytest tests/smoke
uv run --python 3.12 pytest tests/platform
uv run --python 3.12 pytest tests/functional --stable-ray-path /path/to/RAY-UI --dev-ray-path /path/to/RAY-UI-dev
```

## Environment

- `tests/smoke/`: set `RAYUI_PATH` to a local RAY-UI install.
- `tests/platform/`: same `RAYUI_PATH` on Windows and macOS; Linux smoke tests also need `xvfb-run`.
- `tests/functional/`: set `RAYUI_STABLE_PATH` and `RAYUI_DEV_PATH`, or pass `--stable-ray-path` and `--dev-ray-path`.

## Notes

- `manual_tests/` stays untouched and is not part of automated runs.
