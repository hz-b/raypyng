"""raypyng + rayx example: run a single trace of test_dipole.rml using engine="rayx"."""

import os
import numpy as np
from raypyng import Simulate

if __name__ == "__main__":
    this_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_dir, "../rayx_comparison/test_dipole.rml")

    sim = Simulate(rml_file, engine="rayx")

    beamline = sim.rml.beamline

    sim.params = [
        {beamline.Dipole.photonEnergy: np.arange(200,2200.1, 500)},
        {beamline.Dipole.numberRays: 10000},
    ]

    sim.simulation_name = "rayx_example"
    sim.path = this_dir
    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]

    sim.run(multiprocessing=1, force=True, remove_rawrays=True)
