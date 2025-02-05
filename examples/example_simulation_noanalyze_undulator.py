from raypyng import Simulate
import numpy as np
import os
import pandas as pd


this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir, 'rml', 'simple_undulator_beamline.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
beamline = sim.rml.beamline



# define the values of the parameters to scan 
energy    = np.arange(200, 2201,250)
SlitSize  = np.array([0.1])
cff       = np.array([2.25])
nrays     = 1e4

# define a list of dictionaries with the parameters to scan
params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {beamline.SU.photonEnergy:energy}, 
            # set a range of  values 
            {beamline.ExitSlit.totalHeight:SlitSize},
            # set values 
            {beamline.PG.cFactor:cff},
            {beamline.SU.numberRays:nrays}
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'test_noAnalyze_undulator'

# repeat the simulations as many time as needed
sim.repeat = 2

sim.analyze = False # don't let RAY-UI analyze the results
sim.raypyng_analysis=True # let raypyng analyze the results

## This must be a list of dictionaries
sim.exports  =  [{beamline.SU:['RawRaysOutgoing']},
                {beamline.DetectorAtFocus:['RawRaysOutgoing']}
                ]

undulator_file_path = os.path.join(this_file_dir, 
                                   'undulator', 
                                   'undulator_harmonics_energy_photons.csv')

undulator = pd.read_csv(undulator_file_path)

sim.undulator_table=undulator
#uncomment to run the simulations
sim.run(multiprocessing=6, force=True)


