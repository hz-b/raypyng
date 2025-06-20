import numpy as np
from raypyng import Simulate

# define the values of the parameters to scan 
def make_slopes_params(param_dict):
    # Start with the number of parameters
    expanded_entries = []

    # First entry is the all-zero base
    total_steps = 1 + sum(len(v) for v in param_dict.values())

    # Initialize all-zero lists of correct length
    scan_dict = {k: [0] * total_steps for k in param_dict}

    # Fill one parameter at a time (shifted by +1)
    cursor = 1  # Start after the zero baseline
    for key, values in param_dict.items():
        for v in values:
            scan_dict[key][cursor] = v
            cursor += 1

    return scan_dict

sim = Simulate('rml/dipole_beamline.rml', hide=True)

rml=sim.rml
beamline = sim.rml.beamline

energy = np.array([500, 1000])    
rounds = 1
nrays  = 1e4

slopes = {beamline.M1.slopeErrorMer:  np.arange(0.3,1.1, 0.1), 
            beamline.M1.slopeErrorSag:np.arange(1.5, 2.1, 0.1), 
            beamline.M3.slopeErrorSag:np.arange(0.5, 2.1, 0.5), 
            beamline.M3.slopeErrorMer:np.arange(0.3, 0.61, 0.3), 
            }

slopes_dict = make_slopes_params(slopes)

# define a list of dictionaries with the parameters to scan
params = [  
            {beamline.PG.cFactor: [2,5]},
            {beamline.Dipole.photonEnergy:energy,
            beamline.Dipole.energySpread:energy/1000},
            {beamline.Dipole.numberRays:nrays}, 
        ]

params.append(slopes_dict)  # append the slopes dictionary to the list of parameters
#and then plug them into the Simulation class
sim.params=params

sim.simulation_name = 'test_noAnalyze_slopes'

# repeat the simulations as many time as needed
sim.repeat = rounds

sim.analyze = False # let RAY-UI analyze the results
sim.raypyng_analysis = True # let RAY-UI analyze the results
## This must be a list of dictionaries
sim.exports  =  [{beamline.DetectorAtFocus:['RawRaysOutgoing']}]

#uncomment to run the simulations
sim.run(multiprocessing=5, force=False, remove_round_folders=False, remove_rawrays=False)