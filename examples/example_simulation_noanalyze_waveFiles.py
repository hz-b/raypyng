import os
import numpy as np

from raypyng import Simulate

this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/undulator_file_beamline.rml')

sim = Simulate(rml_file, hide=True)

rml=sim.rml
beamline = sim.rml.beamline



# define the values of the parameters to scan 
energies    = np.array([80, 150, 200, 300])
energies_path = []

print('The absolute path of the undulator files is:')
for en in energies:
    this_file = os.path.realpath(__file__)
    this_folder = os.path.dirname(this_file)
    path = os.path.join(this_folder, 'WAVE', 'U49H1allrayfiles', f'U49H1_{en}eV_bo.dat')
    print(path)
    energies_path.append(path)
print()


# define a list of dictionaries with the parameters to scan
params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {beamline.Undulator.undulatorFile:energies_path,
             beamline.Undulator.energySpread:energies/1000}, 
            {beamline.PG.cFactor:2.25},
            {beamline.Undulator.numberRays:1e4}
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'test_noAnalyze_undulator_wave'

# repeat the simulations as many time as needed
sim.repeat = 2

sim.analyze = False # don't let RAY-UI analyze the results
sim.raypyng_analysis=True # let raypyng analyze the results

## This must be a list of dictionaries
sim.exports  =  [{beamline.Undulator:['RawRaysOutgoing']},
                {beamline.DetectorAtFocus:['RawRaysOutgoing']}
                ]

#uncomment to run the simulations
sim.run(multiprocessing=5, force=True)


