from raypyng import Simulate
import numpy as np
from raypyng_recipe import ML


rml_file = ('rml/elisa.rml')
sim      = Simulate(rml_file, hide=True)


sim.analyze = False

nsim = 1e1

# correct output using a dirty trick:
myRecipe = ML(nsim,['DetectorAtFocus'],sim_folder='ELISA_correct', dirty_hack=True)

# buggy output using a dirty trick:
myRecipe = ML(nsim,['DetectorAtFocus'],sim_folder='ELISA_bug', dirty_hack=False)

# test resolving power simulations
sim.run(myRecipe, multiprocessing=4, force=False)


############################################
# to reproduce the problem depends on the specs of your computer, i guess. 
# In the following I increase the number of simulations, and I use all the cpus. 
# Hopefully that should work and produce the "killed" output


# myRecipe = ML(1e6,['DetectorAtFocus'],sim_folder='ELISA_bug', dirty_hack=True)

# # test resolving power simulations
# sim.run(myRecipe, multiprocessing=True, force=False)