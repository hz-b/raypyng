from raypyng import Simulate
from raypyng.recipes import ResolvingPower
import numpy as np
import os



if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir  # write output inside this example's own folder

    rml = sim.rml
    beamline = sim.rml.beamline

    energy_range = np.arange(1000, 2001, 500)
    cff = {beamline.PG.cFactor: 2.5}
    ES = {beamline.ExitSlit.totalHeight: [0.1, 0.05]}

    # RAY-UI analysis on, so ScalarBeamProperties (energyH_width) is exported and
    # eval_recipee_ResolvinPower.py can compute the resolving power E/ΔE.
    sim.analyze = True

    rp = ResolvingPower(energy_range, [beamline.Dipole, beamline.DetectorAtFocus], ES, cff)

    sim.run(rp, multiprocessing="auto", force=True)


        
