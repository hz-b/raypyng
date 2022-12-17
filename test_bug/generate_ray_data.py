from raypyng import Simulate
import numpy as np
from raypyng_recipe import ML


rml_file = ('rml/elisa.rml')
sim      = Simulate(rml_file, hide=True)


sim.analyze = False

nsim = 1e3
myRecipe = ML(nsim,['DetectorAtFocus'],sim_folder='ELISA_'+"{:.0e}".format(nsim))

# test resolving power simulations
sim.run(myRecipe, multiprocessing=4, force=False)