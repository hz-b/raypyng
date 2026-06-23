"""Shared pytest fixtures and CLI options for raypyng tests.

Functional regression tests (--stable-ray-path / --dev-ray-path) are silently
skipped when either path is not supplied or does not exist on disk.
"""

import os

import pytest

# These files in tests/ are plain scripts, not proper test modules.
# They read external files on import and crash during pytest collection.
collect_ignore = ["test_dipole.py", "test_waveHelper.py"]


def pytest_addoption(parser):
    parser.addoption(
        "--stable-ray-path",
        default=None,
        help="Path to the stable RAY-UI installation directory",
    )
    parser.addoption(
        "--dev-ray-path",
        default=None,
        help="Path to the development RAY-UI installation directory",
    )
    parser.addoption(
        "--tolerance",
        type=float,
        default=0.01,
        help="Relative tolerance for cross-version metric comparison (default 0.01 = 1%%)",
    )


def _resolve_path(raw):
    """Expand ~, return None if the path does not exist."""
    if raw is None:
        return None
    expanded = os.path.expanduser(raw)
    return expanded if os.path.isdir(expanded) else None


@pytest.fixture(scope="session")
def stable_ray_path(request):
    raw = request.config.getoption("--stable-ray-path") or os.environ.get(
        "RAYUI_STABLE_PATH"
    )
    path = _resolve_path(raw)
    if path is None:
        pytest.skip(
            "Stable RAY-UI path not provided or not found. "
            "Pass --stable-ray-path=<dir> or set RAYUI_STABLE_PATH."
        )
    return path


@pytest.fixture(scope="session")
def dev_ray_path(request):
    raw = request.config.getoption("--dev-ray-path") or os.environ.get("RAYUI_DEV_PATH")
    path = _resolve_path(raw)
    if path is None:
        pytest.skip(
            "Development RAY-UI path not provided or not found. "
            "Pass --dev-ray-path=<dir> or set RAYUI_DEV_PATH."
        )
    return path


@pytest.fixture(scope="session")
def tolerance(request):
    return request.config.getoption("--tolerance")
