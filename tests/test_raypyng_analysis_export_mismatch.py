import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "examples" / "repro" / "simulation_raypyng_lightweight.py"


def _can_run_rayui() -> bool:
    if shutil.which("xvfb-run") is None:
        return False

    sys.path.insert(0, str(REPO_ROOT / "src"))
    try:
        from raypyng.runner import RayUIRunner

        RayUIRunner(hide=True)
    except Exception:
        return False
    return True


@pytest.mark.skipif(not _can_run_rayui(), reason="Ray-UI/xvfb environment not available")
def test_raypyng_analysis_export_mismatch(tmp_path: Path):
    env = os.environ.copy()
    pythonpath_entries = [str(REPO_ROOT / "src")]
    if env.get("PYTHONPATH"):
        pythonpath_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

    out_dir = tmp_path / "repro"
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--output-dir",
        str(out_dir),
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    text = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, text
    assert "Traceback" not in text

    sim_dir = out_dir / "RAYPy_Simulation_raypyng_lightweight_repro"
    assert (sim_dir / "Dipole_RawRaysOutgoing.csv").exists()
    assert (sim_dir / "ExitSlit_RawRaysOutgoing.csv").exists()
    assert (sim_dir / "ExitSlit_RawRaysIncoming.csv").exists()
    assert not (sim_dir / "Dipole_RawRaysIncoming.csv").exists()
