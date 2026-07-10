import numpy as np
import os
from raypyng import Simulate
from raypyng.recipes import Roughness


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, "..", "rml", "dipole_beamline.rml")

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir

    beamline = sim.rml.beamline
    energy_range = np.arange(500, 2001, 250)
    roughness_values = np.array([0.1, 0.3, 0.5, 1.5])

    sim.analyze = False
    sim.raypyng_analysis = True

    recipe = Roughness(
        energy_range,
        beamline.DetectorAtFocus,
        {beamline.ExitSlit.openingHeight: [0.1, 0.05]},
        {beamline.PG.cFactor: 5},
        roughness_values=roughness_values,
        preferred_value=0.3,
        nrays=int(5e4),
        rounds=1,
        sim_folder="1200_roughness_and_exit_slit_cff5",
    )

    sim.repeat = recipe.rounds
    sim.run(recipe, multiprocessing="auto", force=True, remove_round_folders=True, remove_rawrays=True)
