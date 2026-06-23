import os
import numpy as np

from raypyng import Simulate

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'undulator_file_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir  # write output inside this example's own folder

    rml = sim.rml
    beamline = sim.rml.beamline

    energies = np.array([80, 150, 200, 300])
    energies_path = []

    print('The absolute path of the undulator files is:')
    for en in energies:
        path = os.path.join(this_file_dir, '..', 'WAVE', 'U49H1allrayfiles', f'U49H1_{en}eV_bo.dat')
        print(path)
        energies_path.append(path)
    print()

    params = [
        {beamline.Undulator.undulatorFile: energies_path,
         beamline.Undulator.energySpread: energies / 1000},
        {beamline.PG.cFactor: 2.25},
        {beamline.Undulator.numberRays: 1e4},
    ]

    sim.params = params
    sim.simulation_name = 'WaveFiles'
    sim.repeat = 2
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [
        {beamline.Undulator: ['RawRaysOutgoing']},
        {beamline.DetectorAtFocus: ['RawRaysOutgoing']},
    ]

    sim.run(multiprocessing="auto", force=True)
