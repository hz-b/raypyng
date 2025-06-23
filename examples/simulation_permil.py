from raypyng import Simulate
import numpy as np
import os

this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/dipole_beamline.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
beamline = sim.rml.beamline



# define the values of the parameters to scan 
energy    = np.arange(100, 8101,500)
SlitSize  = np.array([0.1])
cff       = np.array([2.25])
grating   = np.array([400, 1200])
nrays     = 50000

# define a list of dictionaries with the parameters to scan
params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {beamline.Dipole.photonEnergy:energy}, 
            # set a range of  values 
            {beamline.ExitSlit.totalHeight:SlitSize},
            # set values 
            {beamline.PG.cFactor:cff},
            {beamline.Dipole.numberRays:nrays}, 
            {beamline.PG.lineDensity:grating},
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'Permil'

# repeat the simulations as many time as needed
sim.repeat = 1

sim.analyze = False # don't let RAY-UI analyze the results
sim.raypyng_analysis=True # let raypyng analyze the results

## This must be a list of dictionaries
sim.exports  =  [{beamline.Dipole:['RawRaysOutgoing']},
                {beamline.DetectorAtFocus:['RawRaysOutgoing']}
                ]

#uncomment to run the simulations
sim.run(multiprocessing=8, force=True)



        