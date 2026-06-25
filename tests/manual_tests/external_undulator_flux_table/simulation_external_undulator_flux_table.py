from raypyng import Simulate
import numpy as np
import os
import pandas as pd


if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'simple_undulator_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir  # write output inside this example's own folder

    rml = sim.rml
    beamline = sim.rml.beamline

    # define the values of the parameters to scan
    energy   = np.arange(200, 2201, 250)
    SlitSize = np.array([0.1])
    cff      = np.array([2.25])
    nrays    = 1e4

    params = [
        {beamline.SU.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: SlitSize},
        {beamline.PG.cFactor: cff},
        {beamline.SU.numberRays: nrays},
    ]

    sim.params = params
    sim.simulation_name = 'external_undulator_flux_table'
    sim.repeat = 2
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [
        {beamline.SU: ['RawRaysOutgoing']},
        {beamline.DetectorAtFocus: ['RawRaysOutgoing']},
    ]

    undulator_file_path = os.path.join(
        this_file_dir, '..', 'undulator', 'undulator_harmonics_energy_photons.csv'
    )
    sim.undulator_table = pd.read_csv(undulator_file_path)

    sim.run(multiprocessing="auto", force=True)
