"""Beamwaist example — simulation step.

Traces the beam through every optical element at a single photon energy and
saves the combined beamwaist image (``xh.txt`` / ``yh.txt``) into this folder's
``RAYPy_Simulation_Beamwaist`` directory. Run ``eval_beamwaist.py`` afterwards
to produce the 2D plot from the saved trace.
"""

import os

from raypyng.beamwaist import PlotBeamwaist
from raypyng.simulate import Simulate

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True, ray_path="/home/simone/Applications/Ray-UI-development-stream")
    sim.path = this_file_dir  # write output inside this example's own folder
    sim_folder = 'Beamwaist'

    bw = PlotBeamwaist(sim_folder, sim)
    # PlotBeamwaist.directory is CWD-relative by default; make it absolute so it
    # matches where Simulate (sim.path) writes, regardless of the caller's CWD.
    bw.directory = os.path.join(this_file_dir, bw.directory)

    energy = 500
    nrays = 1000
    bw.simulate_beamline(energy, nrays=nrays, force=True)

    bw.define_hist(lim=20, step=.5)  # lim should be larger than max beam waist
    bw.define_zstep(step_z=100)      # in mm, step in optical direction to trace RAYS
    bw.reduce_Nrays(factor=1)        # this reduces the n of rays by the factor you set

    bw.trace_beamwaist(save_results=True)
