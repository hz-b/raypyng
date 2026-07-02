from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_example00_runs_from_real_script(rayui_path, tmp_path: Path):
    script_path = tmp_path / "example00_windows_probe.py"
    script_path.write_text(
        """
import os
import numpy as np
from raypyng import Simulate

REPO_ROOT = r\"%s\"
THIS_FILE_DIR = os.path.join(REPO_ROOT, "examples", "00_raypyng")
RML_FILE = os.path.join(THIS_FILE_DIR, "..", "rml", "dipole_beamline.rml")
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
    sim.simulation_name = "raypyng"
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
    assert "_hide" not in text, text
    assert proc.returncode == 0, text
