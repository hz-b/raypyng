import os

import numpy as np

from raypyng import Simulate

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir  # write output inside this example's own folder

    rml = sim.rml
    beamline = sim.rml.beamline

    # define the values of the parameters to scan
    energy   = np.arange(100, 1601, 500)
    SlitSize = np.array([0.02])
    cff      = np.array([2.25])
    nrays    = 2e5

    params = [
        {beamline.Dipole.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: SlitSize},
        {beamline.PG.cFactor: cff},
        {beamline.Dipole.numberRays: nrays},
    ]

    sim.reflectivity = True
    sim.params = params
    sim.simulation_name = 'RAY-UI'
    sim.repeat = 1
    sim.analyze = True

    sim.exports = [{beamline.ExitSlit: ['ScalarBeamProperties']}]

    sim.run(multiprocessing='auto', force=True)



        
