from RayPyNG.rml import RMLFile
from RayPyNG.simulate import Simulate
from RayPyNG.simulate import SimulationParams
import numpy as np


params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml.beamline.M1.grazingIncAngle:np.array([1,2]), rml.beamline.M1.longRadius:[0,180], rml.beamline.Dipole.photonEnergy:[1000,2000]}, 
            # set a range of  values - in independed way
            {rml.beamline.M1.exitArmLengthMer:range(19400,19501, 100)},
            # set a value - in independed way
            {rml.beamline.M1.exitArmLengthSag:np.array([100])}
        ]


sp = SimulationParams(rml) # epxands to rml_list/params_list, now aware of runner
sp.params=params



sim = Simulate('examples/rml/high_energy_branch_flux_1200.rml',template='examples/rml/high_energy_branch_flux_1200.rml')
rml = sim.rml

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'test'

# repeat the simulations as many time as needed
sim.repeat = 2

#this is defined at the current working directory by default
#sim.path = '/home/simone/Documents/RAYPYNG/raypyng' 

# this is defined as RAYPy_simulation by default
#sim.prefix = 'asdasd_'

# This must be a list of dictionaries
sim.exports  =  [{rml.beamline.Dipole:'ScalarBeamProperties'},
                 {rml.beamline.DetectorAtFocus:['ScalarElementProperties','ScalarBeamProperties']}
                ]


# params must be an instance of SimulationsParams
sim.params=sp 

# create the rml files
sim.rml_list()


#uncomment to run the simulations
sim.run_example()

# To be implemented
#sim.run(nNowrkers = 10)

'''A couple of things to keep in mind:
 - when we rteace we want to check if the file was 
   already traced and exported, or if we have to do it
 - we put the simulations in a list called result: 
   what happens if we have millions of simulations?
 - we are passing rml to both the SimulationParams class 
   and to the Simulation class. 
   This might generate some errors, can we avoid it?
'''


        