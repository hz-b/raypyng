from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.requires_ray_ui


def _needs_xvfb() -> bool:
    return sys.platform.startswith("linux") and shutil.which("xvfb-run") is None


@pytest.mark.skipif(_needs_xvfb(), reason="Ray-UI hide=True on Linux requires xvfb-run")
def test_raypyng_analysis_export_mismatch(rayui_path, tmp_path: Path):
    script_path = tmp_path / "raypyng_analysis_probe.py"
    script_path.write_text(
        """
import os
import numpy as np
from raypyng import Simulate

REPO_ROOT = r\"%s\"
RML_FILE = os.path.join(REPO_ROOT, "examples", "00_raypyng", "..", "rml", "dipole_beamline.rml")
OUTPUT_DIR = r\"%s\"

if __name__ == "__main__":
    sim = Simulate(RML_FILE, hide=True, ray_path=os.environ["RAYUI_PATH"])
    sim.path = OUTPUT_DIR
    beamline = sim.rml.beamline
    sim.params = [
        {beamline.Dipole.photonEnergy: np.arange(200, 1201, 500)},
        {beamline.ExitSlit.totalHeight: np.array([0.1])},
        {beamline.PG.cFactor: np.array([2.25])},
        {beamline.Dipole.numberRays: 1000},
    ]
    sim.simulation_name = "raypyng_lightweight_repro"
    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True
    sim.exports = [
        {beamline.Dipole: ["RawRaysOutgoing"]},
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]
    print(sim.run(multiprocessing="auto", force=True, remove_rawrays=True))
"""
        % (str(REPO_ROOT).replace("\\", "\\\\"), str(tmp_path).replace("\\", "\\\\")),
        encoding="utf8",
    )

    env = os.environ.copy()
    pythonpath_entries = [str(REPO_ROOT / "src")]
    if env.get("PYTHONPATH"):
        pythonpath_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    env["RAYUI_PATH"] = rayui_path

    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    text = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, text
    assert "Traceback" not in text

    sim_dir = tmp_path / "RAYPy_Simulation_raypyng_lightweight_repro"
    assert (sim_dir / "Dipole_RawRaysOutgoing.csv").exists()
    assert (sim_dir / "DetectorAtFocus_RawRaysOutgoing.csv").exists()
    assert not (sim_dir / "Dipole_RawRaysIncoming.csv").exists()
