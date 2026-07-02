from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from raypyng import Simulate


def main():
    base_dir = Path(__file__).resolve().parents[1]
    output_root = Path(os.environ["RAYPYNG_SMOKE_OUTPUT"])
    rml_file = base_dir / "rml" / "dipole.rml"

    sim = Simulate(str(rml_file), hide=True, ray_path=os.environ["RAYUI_PATH"])
    beamline = sim.rml.beamline
    sim.simulation_name = "windows_mp_smoke"
    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True
    sim.path = str(output_root)
    sim.params = [
        {beamline.Dipole.photonEnergy: np.array([200, 400])},
        {beamline.ExitSlit.totalHeight: np.array([0.1])},
        {beamline.PG.cFactor: np.array([2.25])},
        {beamline.Dipole.numberRays: 1000},
    ]
    sim.exports = [
        {beamline.Dipole: "RawRaysOutgoing"},
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]
    sim.run(multiprocessing=2, force=True)


if __name__ == "__main__":
    main()
