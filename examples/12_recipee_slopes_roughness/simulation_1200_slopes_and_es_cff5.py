import numpy as np
import os
from raypyng import Simulate
from raypyng.recipes import Slopes


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, "..", "rml", "dipole_beamline.rml")

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir

    beamline = sim.rml.beamline
    energy_range = np.arange(500, 2001, 250)

    sim.analyze = False
    sim.raypyng_analysis = True

    recipe = Slopes(
        energy_range,
        beamline.DetectorAtFocus,
        {beamline.ExitSlit.openingHeight: [0.1, 0.05]},
        {beamline.PG.cFactor: 5},
        slope_values={
            beamline.M1.slopeErrorMer: {"slope_values": np.array([0.2, 0.5, 0.7, 2.0]), "reference_value": 0.5},
            beamline.M1.slopeErrorSag: {"slope_values": np.array([1.0, 1.5, 2.0, 5.0]), "reference_value": 1.5},
            beamline.PremirrorM2.slopeErrorMer: {"slope_values": np.array([0.03, 0.05, 0.07, 1.5]), "reference_value": 0.05},
            beamline.PremirrorM2.slopeErrorSag: {"slope_values": np.array([0.3, 0.5, 0.7, 2.0]), "reference_value": 0.5},
            beamline.PG.slopeErrorMer: {"slope_values": np.array([0.03, 0.05, 0.07, 1.5]), "reference_value": 0.05},
            beamline.PG.slopeErrorSag: {"slope_values": np.array([0.3, 0.5, 0.7, 2.0]), "reference_value": 0.5},
            beamline.M3.slopeErrorSag: {"slope_values": np.array([0.5, 1.0, 1.5, 4.0]), "reference_value": 1.0},
            beamline.M3.slopeErrorMer: {"slope_values": np.array([0.1, 0.3, 0.5, 4.0]), "reference_value": 0.3},
            beamline.KB1.slopeErrorMer: {"slope_values": np.array([0.03, 0.05, 0.07, 0.2]), "reference_value": 0.05},
            beamline.KB1.slopeErrorSag: {"slope_values": np.array([0.05, 0.1, 0.15, 0.5]), "reference_value": 0.1},
            beamline.KB2.slopeErrorMer: {"slope_values": np.array([0.03, 0.05, 0.07]), "reference_value": 0.05},
            beamline.KB2.slopeErrorSag: {"slope_values": np.array([0.05, 0.1, 0.15, 0.5]), "reference_value": 0.1},
        },
        nrays=int(1e4),
        rounds=1,
        sim_folder="1200_slopes_and_exit_slit_cff5",
    )

    sim.repeat = recipe.rounds
    sim.run(recipe, multiprocessing="auto", force=True, remove_round_folders=True, remove_rawrays=True)
