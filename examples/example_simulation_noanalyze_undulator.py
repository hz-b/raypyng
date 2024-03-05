from raypyng import Simulate
import numpy as np
import os
import time

st = time.time()

this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/nap-leem.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
elisa = sim.rml.beamline



# define the values of the parameters to scan 
energy    = np.arange(200, 2201,200)
SlitSize  = np.array([0.1])
cff       = np.array([2.25])
nrays     = 1e5

# define a list of dictionaries with the parameters to scan
params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {elisa.SU.photonEnergy:energy}, 
            # set a range of  values 
            {elisa.ExitSlit.totalHeight:SlitSize},
            # set values 
            {elisa.PG.cFactor:cff},
            {elisa.SU.numberRays:nrays}
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'test_noAnalyze_undulator'

# repeat the simulations as many time as needed
sim.repeat = 1

sim.analyze = False # don't let RAY-UI analyze the results
sim.raypyng_analysis=True # let raypyng analyze the results

## This must be a list of dictionaries
sim.exports  =  [{elisa.SU:['RawRaysOutgoing']},
                {elisa.DetectorAtFocus:['RawRaysOutgoing']}
                ]

#uncomment to run the simulations
sim.run(multiprocessing=1, force=True)



time_needed = time.time() - st

# Convert the time difference to minutes and seconds
minutes, seconds = divmod(time_needed, 60)

# Print the time needed in minutes:seconds format
print(f"Time needed: {int(minutes)}:{int(seconds):02d}")