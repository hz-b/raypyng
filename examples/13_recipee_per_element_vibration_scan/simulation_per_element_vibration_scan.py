import os

from raypyng import Simulate
from raypyng.recipes import PerElementVibrationScan


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, "..", "rml", "simple_undulator_beamline.rml")

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir

    beamline = sim.rml.beamline
    energy = 1000
    cff = {beamline.PG.cFactor: 2.5}
    exit_slit = {beamline.ExitSlit.totalHeight: [0.02]}

    sim.analyze = False
    sim.raypyng_analysis = True

    recipe = PerElementVibrationScan(
        energy,
        beamline.DetectorAtFocus,
        exit_slit,
        cff,
        max_rms_nm=5,
        transfer_factor={
            "translationXerror": 30,
            "translationYerror": 30,
            "translationZerror": 30,
            "rotationXerror": 15,
            "rotationYerror": 15,
            "rotationZerror": 15,
        },
        nrays=int(1e5),
        n_scan_points=7,
        rounds=2,
        sim_folder="per_element_vibration_scan",
    )

    sim.repeat = recipe.rounds
    sim.run(
        recipe,
        multiprocessing="auto",
        force=True,
        remove_round_folders=True,
        remove_rawrays=True,
    )
