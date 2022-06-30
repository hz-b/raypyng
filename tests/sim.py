
from RayPyNG.rml import RMLFile
from RayPyNG.simulate import Simulate
import numpy as np


#rml = RMLFile('RayPyNG/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')
#sim = Simulate(rml=rml)
sim = Simulate('RayPyNG/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')
rml = sim.rml

params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml.beamline.M1.grazingIncAngle:np.array([1,2]), rml.beamline.M1.longRadius:[0,180], rml.beamline.Dipole.photonEnergy:[1000,2000]}, 
            # set a range of  values - in independed way
            {rml.beamline.M1.exitArmLengthMer:range(19400,19501, 100)},
            # set a value - in independed way
            {rml.beamline.M1.exitArmLengthSag:np.array([100])}
        ]


sim.set_param(params)
sim._extract_param(verbose=False)
sim._calc_loop()
sim.create_simulation_files('simulation_test')
        
        