"""Run the same dipole beamline simulation using the RAYX engine.

Results are written to RAYPy_Simulation_rayx/ inside this folder.
Run this script before plot_comparison.py.
"""

import os

import numpy as np

from raypyng import Simulate

this_dir = os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_dir, "../rml/dipole_beamline.rml")

sim = Simulate(rml_file, engine="rayx")

rml = sim.rml
beamline = sim.rml.beamline

energy = np.arange(200, 7201, 500)
SlitSize = np.array([0.1, 0.2])
cff = np.array([2.25])
nrays = 5e4

params = [
    {beamline.Dipole.photonEnergy: energy},
    {beamline.ExitSlit.totalHeight: SlitSize},
    {beamline.PG.cFactor: cff},
    {beamline.Dipole.numberRays: nrays},
]

sim.params = params
sim.simulation_name = "rayx"
sim.path = this_dir
sim.repeat = 2

sim.analyze = False
sim.raypyng_analysis = True

sim.exports = [
    {beamline.Dipole: ["RawRaysOutgoing"]},
    {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
]

sim.run(multiprocessing="auto", force=True, remove_rawrays=True)
