"""Run the dipole beamline simulation using the RAY-UI engine.

Results are written to RAYPy_Simulation_rayui/ inside this folder.
Run this script before plot_comparison.py.
"""

import os

from raypyng import Simulate
from params import rml_file, energy, SlitSize, cff, nrays, repeat

this_dir = os.path.dirname(os.path.realpath(__file__))

sim = Simulate(rml_file, hide=True)

rml = sim.rml
beamline = sim.rml.beamline

sim.params = [
    {beamline.Dipole.photonEnergy: energy},
    {beamline.Dipole.numberRays: nrays},
]

sim.simulation_name = "rayui"
sim.path = this_dir
sim.repeat = repeat

sim.analyze = False
sim.raypyng_analysis = True

sim.exports = [
    {beamline.Dipole: ["RawRaysOutgoing"]},
    {beamline.M1: ["RawRaysOutgoing"]},
    {beamline.PremirrorM2: ["RawRaysOutgoing"]},
    {beamline.PG: ["RawRaysOutgoing"]},
    {beamline.M3: ["RawRaysOutgoing"]},
    {beamline.ExitSlit: ["RawRaysOutgoing"]},
    {beamline.KB1_hor: ["RawRaysOutgoing"]},
    {beamline.KB2_ver: ["RawRaysOutgoing"]},
    {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
]

sim.run(multiprocessing="auto", force=True, remove_rawrays=False)
