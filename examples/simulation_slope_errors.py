import os

import numpy as np
from raypyng import Simulate

if __name__ == "__main__":

    def make_slopes_params(param_dict):
        total_steps = 1 + sum(len(v) for v in param_dict.values())
        scan_dict = {k: [0] * total_steps for k in param_dict}
        cursor = 1
        for key, values in param_dict.items():
            for v in values:
                scan_dict[key][cursor] = v
                cursor += 1
        return scan_dict

    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    sim = Simulate(os.path.join(this_file_dir, "rml/dipole_beamline.rml"), hide=True)

    rml = sim.rml
    beamline = sim.rml.beamline

    energy = np.array([500, 1000])
    rounds = 1
    nrays = 1e4

    slopes = {
        beamline.M1.slopeErrorMer: np.arange(0.3, 1.1, 0.1),
        beamline.M1.slopeErrorSag: np.arange(1.5, 2.1, 0.1),
        beamline.M3.slopeErrorSag: np.arange(0.5, 2.1, 0.5),
        beamline.M3.slopeErrorMer: np.arange(0.3, 0.61, 0.3),
    }

    slopes_dict = make_slopes_params(slopes)

    params = [
        {beamline.PG.cFactor: [2, 5]},
        {
            beamline.Dipole.photonEnergy: energy,
            beamline.Dipole.energySpread: energy / 1000,
        },
        {beamline.Dipole.numberRays: nrays},
    ]
    params.append(slopes_dict)

    sim.params = params
    sim.simulation_name = "SlopeErrors"
    sim.repeat = rounds
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.exports = [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]

    sim.run(
        multiprocessing="auto",
        force=False,
        remove_round_folders=False,
        remove_rawrays=False,
    )
