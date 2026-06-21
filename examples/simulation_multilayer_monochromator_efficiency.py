from raypyng import Simulate
import numpy as np
import os
import pandas as pd

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, 'rml/dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)

    rml = sim.rml
    beamline = sim.rml.beamline

    # define the values of the parameters to scan
    energy   = np.arange(200, 7201, 250)
    SlitSize = np.array([0.1])
    cff      = np.array([2.25, 3])
    nrays    = 5e3

    params = [
        {beamline.Dipole.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: SlitSize},
        {beamline.PG.cFactor: cff},
        {beamline.Dipole.numberRays: nrays},
    ]

    sim.params = params
    sim.simulation_name = 'ML_Mono'
    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [{beamline.DetectorAtFocus: ['RawRaysOutgoing']}]

    # efficiency calculated externally; multiplied into the RAY-UI result
    eff = pd.DataFrame({
        "Efficiency": [0.9, 0.8, 0.7],
        "Energy[eV]": [100, 200, 300],
    })
    sim.efficiency = eff

    sim.run(
        multiprocessing="auto",
        force=True,
        remove_rawrays=True,
        remove_round_folders=True,
    )



        
