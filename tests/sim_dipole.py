import numpy as np

from raypyng import Simulate


sim = Simulate('rml/dipole.rml', hide=True)

rml=sim.rml
beamline = sim.rml.beamline


electron_energy_GeV = 2.5  # Electron beam energy in GeV
magnetic_fields = np.array([0.6, 1.3, 2.0, 3.0])  # Magnetic fields in Tesla
bending_radii = 3.335 * electron_energy_GeV / magnetic_fields
params = [  
            {beamline.Dipole.bendingRadius:bending_radii},  # Bending radius in meters
            {beamline.Dipole.photonEnergy:np.arange(1, 10000.1, 100)},  # Energy range from 0.1 to 20 keV
            {beamline.Dipole.numberRays:1000}
        ]

#and then plug them into the Simulation class
sim.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'Dipole'

# turn off reflectivity
sim.reflectivity(False)

# repeat the simulations as many time as needed
sim.repeat = 1

sim.analyze = False # let RAY-UI analyze the results
sim.raypyng_analysis = True # let RAY-UI analyze the results

## This must be a list of dictionaries
sim.exports  =  [
    {beamline.Dipole:['RawRaysOutgoing']}
    ]


# create the rml files
#sim.rml_list()

#uncomment to run the simulations
sim.run(multiprocessing=5, force=False)
