from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tests" / "manual_tests" / "windows_multiprocessing_smoke.py"

pytestmark = pytest.mark.requires_ray_ui


def test_windows_multiprocessing_smoke(rayui_path, tmp_path: Path):
    env = os.environ.copy()
    pythonpath_entries = [str(REPO_ROOT / "src")]
    if env.get("PYTHONPATH"):
        pythonpath_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    env["RAYUI_PATH"] = rayui_path
    env["RAYPYNG_SMOKE_OUTPUT"] = str(tmp_path)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    text = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, text
    sim_dir = tmp_path / "RAYPy_Simulation_windows_mp_smoke"
    assert (sim_dir / "round_0").is_dir()

    current = psutil.Process()
    leftovers = []
    for child in current.children(recursive=True):
        try:
            name = (child.name() or "").lower()
            cmdline = " ".join(child.cmdline()).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if "rayui" in name or "ray-ui" in name or "rayui" in cmdline or "ray-ui" in cmdline:
            leftovers.append(child.pid)
    assert leftovers == []
