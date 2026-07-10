from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve_rayui_path() -> str | None:
    env_path = os.environ.get("RAYUI_PATH")
    if env_path and Path(env_path).is_dir():
        return env_path

    sys.path.insert(0, str(REPO_ROOT / "src"))
    try:
        from raypyng.runner import RayUIRunner

        return RayUIRunner(ray_path=None, hide=(platform.system() == "Windows"))._path
    except Exception:
        return None


@pytest.fixture(scope="module")
def rayui_path():
    path = _resolve_rayui_path()
    if path is None:
        pytest.skip("RAY-UI environment not available")
    return path


@pytest.fixture
def rayui_api(rayui_path):
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from raypyng.runner import RayUIAPI, RayUIRunner

    runner = RayUIRunner(ray_path=rayui_path, hide=(platform.system() == "Windows"))
    api = RayUIAPI(runner)
    try:
        yield runner, api
    finally:
        try:
            api.quit()
        except Exception:
            pass
        runner.kill()
