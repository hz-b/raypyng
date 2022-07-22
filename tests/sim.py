from RayPyNG.rml import RMLFile
from RayPyNG.simulate import Simulate
from RayPyNG.simulate import SimulationParams
import numpy as np



sim = Simulate('examples/rml/high_energy_branch_flux_1200.rml',template='examples/rml/high_energy_branch_flux_1200.rml', hide=True)

rml=sim.rml
elisa = sim.rml.beamline
sp = SimulationParams(rml) 




order     = 1
energy    = np.arange(200, 2001,200)
SlitSize  = np.array([0.1,0.05])
cff       = np.array([2.25])
nrays     = 10000



params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {elisa.Dipole.photonEnergy:energy}, 
            # set a range of  values 
            {elisa.ExitSlit.totalHeight:SlitSize},
            # set values 
            {elisa.PG.cFactor:cff},
            {elisa.Dipole.numberRays:nrays}
        ]


sp.params=params

# sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
sim.simulation_name = 'test'

# repeat the simulations as many time as needed
sim.repeat = 1

#this is defined at the current working directory by default
#sim.path = '/home/simone/Documents/RAYPYNG/raypyng' 

# this is defined as RAYPy_simulation by default
#sim.prefix = 'asdasd_'
analyze = False
analyze = True

if analyze:
    sim.analyze = True
    # This must be a list of dictionaries
    sim.exports  =  [{elisa.Dipole:'ScalarBeamProperties'},
                    {elisa.DetectorAtFocus:['ScalarElementProperties','ScalarBeamProperties']}
                    ]
else:
    sim.analyze = False
    ## This must be a list of dictionaries
    sim.exports  =  [{elisa.Dipole:'RawRaysOutgoing'},
                    {elisa.DetectorAtFocus:['RawRaysOutgoing']}
                    ]

# params must be an instance of SimulationsParams
sim.params=sp 

# create the rml files
sim.rml_list()


#sim.check_simulations(force=True)

#uncomment to run the simulations
#sim.run(force=True)

#uncomment to run the simulations
sim.run_mp(number_of_cpus=5,force=False)





# test resolving power simulations
#sim._RP_simulation(elisa.Dipole, np.arange(1000,1101,50), elisa.DetectorAtFocus)

# to run the script
# PYTHONPATH=. python tests/sim.py


        