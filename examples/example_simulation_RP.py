from raypyng.simulate import Simulate
from raypyng.simulate import SimulationParams
import numpy as np
import os


this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/high_energy_branch_flux_1200.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
elisa = sim.rml.beamline

energy_range = np.arange(1000,2001,500)
cff = {elisa.PG.cFactor:2.5}
ES = {elisa.ExitSlit.totalHeight:[0.1,0.05]}

sim.analyze = False
# test resolving power simulations
sim.RP_simulation(energy_range, elisa.DetectorAtFocus,ES,cff,cpu=5, force=False)


        