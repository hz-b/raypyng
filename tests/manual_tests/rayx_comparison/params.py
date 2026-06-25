import os
import numpy as np

rml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_dipole.rml")

energy   = np.arange(200, 2201, 500)
SlitSize = np.array([0.1, 0.2])
cff      = np.array([2.25])
nrays    = 1e5
repeat   = 1
