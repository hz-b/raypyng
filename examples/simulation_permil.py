from raypyng import Simulate
import numpy as np
import os

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, 'rml/dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)

    rml = sim.rml
    beamline = sim.rml.beamline

    # define the values of the parameters to scan
    energy   = np.arange(100, 8101, 500)
    SlitSize = np.array([0.1])
    cff      = np.array([2.25])
    grating  = np.array([400, 1200])
    nrays    = 50000

    params = [
        {beamline.Dipole.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: SlitSize},
        {beamline.PG.cFactor: cff},
        {beamline.Dipole.numberRays: nrays},
        {beamline.PG.lineDensity: grating},
    ]

    sim.params = params
    sim.simulation_name = 'Permil'
    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [
        {beamline.Dipole: ['RawRaysOutgoing']},
        {beamline.DetectorAtFocus: ['RawRaysOutgoing']},
    ]

    sim.run(multiprocessing="auto", force=True)



        
