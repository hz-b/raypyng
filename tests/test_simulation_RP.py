from RayPyNG.simulate import Simulate
from RayPyNG.simulate import SimulationParams
import numpy as np



sim = Simulate('examples/rml/high_energy_branch_flux_1200.rml',template='examples/rml/high_energy_branch_flux_1200.rml', hide=True)

rml=sim.rml
elisa = sim.rml.beamline



# test resolving power simulations
sim._RP_simulation(elisa.Dipole, np.arange(1000,1101,50), elisa.DetectorAtFocus)

# to run the script
# PYTHONPATH=. python tests/test_simulate_RP.py


        