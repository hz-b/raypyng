
from RayPyNG.rml import RMLFile
from RayPyNG.simulate import Simulate
import numpy as np


#rml = RMLFile('RayPyNG/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')
#sim = Simulate(rml=rml)
sim = Simulate('examples/rml/high_energy_branch_flux_1200.rml',template='examples/rml/high_energy_branch_flux_1200.rml')
rml = sim.rml

params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml.beamline.M1.grazingIncAngle:np.array([1,2]), rml.beamline.M1.longRadius:[0,180], rml.beamline.Dipole.photonEnergy:[1000,2000]}, 
            # set a range of  values - in independed way
            {rml.beamline.M1.exitArmLengthMer:range(19400,19501, 100)},
            # set a value - in independed way
            {rml.beamline.M1.exitArmLengthSag:np.array([100])}
        ]

params3 = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {'grazingIncAngle':np.array([1,2]), 'longRadius':[0,180], 'photonEnergy':[1000,2000]}, 
            # set a range of  values - in independed way
            {'exitArmLengthMer':range(19400,19501, 100)},
            # set a value - in independed way
            {'exitArmLengthSag':np.array([100])}
        ]


# param_list = [
#     # self.params() returns 
#     {rml.beamline.M1.grazingIncAngle:1,rml.beamline.M1
# .longRadius:0,rml.beamline.Dipole.photonEnergy:1000,rml.beamline.M1.exitArmLengthMer:19400,rml.beamline.M1.exitArmLengthSag:100}
#     # self.params() returns 
#     {rml.beamline.M1.grazingIncAngle:2,rml.beamline.M1.longRadius:180,rml.beamline.Dipole.photonEnergy:2000,rml.beamline.M1.exitArmLengthMer:19400,rml.beamline.M1.exitArmLengthSag:100}
#     # self.params() returns 
#     {rml.beamline.M1.grazingIncAngle:1,rml.beamline.M1.longRadius:0,rml.beamline.Dipole.photonEnergy:1000,rml.beamline.M1.exitArmLengthMer:19501,rml.beamline.M1.exitArmLengthSag:100}
#     # ...
#     ...
# ]

#sp = SimulationParams(rml, params) # epxands to rml_list/params_list, now aware of runner

#sim = Simulation(sp) # usees rml_list to save rml and run simulation

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_folder = 'test'
sim.repeat = 1
sim.path = '/home/simone/Documents/RAYPYNG/raypyng' # expand internally to abspath()!
sim.prefix = 'asdasd'
sim.exports = [{},{}]
#sim.exports = ['Dipole,DetectorAtFocus', 'ScalarBeamProperties,ScalarElementProperties']
#sim.run(nNowrkers = 10)


sim.params=params
sim._extract_param(verbose=False)
sim._calc_loop()
#sim.create_simulation_files('simulation_test')


        