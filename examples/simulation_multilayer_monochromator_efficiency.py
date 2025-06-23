from raypyng import Simulate
import numpy as np
import os
import pandas as pd

this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/dipole_beamline.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
beamline = sim.rml.beamline



# define the values of the parameters to scan 
energy    = np.arange(200, 7201,250)
SlitSize  = np.array([0.1])
cff       = np.array([2.25, 3])
nrays     = 5e3

# define a list of dictionaries with the parameters to scan
params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {beamline.Dipole.photonEnergy:energy}, 
            # set a range of  values 
            {beamline.ExitSlit.totalHeight:SlitSize},
            # set values 
            {beamline.PG.cFactor:cff},
            {beamline.Dipole.numberRays:nrays}
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'ML_Mono'

# repeat the simulations as many time as needed
sim.repeat = 1

sim.analyze = False # don't let RAY-UI analyze the results
sim.raypyng_analysis=True # let raypyng analyze the results

## This must be a list of dictionaries
sim.exports  =  [{beamline.DetectorAtFocus:['RawRaysOutgoing']},
                ]

# the efficiency of the multilayer monochromator has been calculated with other programs
# or, in this example is we make it up
eff = pd.DataFrame({
    "Efficiency": [0.9, 0.8, 0.7],
    "Energy[eV]": [100, 200, 300]
})
# and then we just pass it to the simulatins class to multiply this by the efficency 
# calculated by the RAY-UI
sim.efficiency = eff

#uncomment to run the simulations
sim.run(multiprocessing=5, force=True, remove_rawrays=True, remove_round_folders=True)



        