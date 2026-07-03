from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from raypyng.simulate import Simulate

pytestmark = pytest.mark.requires_ray_ui


def test_no_analyze_produces_expected_files(rayui_path, tmp_path: Path):
    rml_file = Path(__file__).resolve().parents[1] / "data" / "rml" / "dipole.rml"
    sim = Simulate(str(rml_file), hide=True, ray_path=rayui_path)
    sim.path = str(tmp_path)

    beamline = sim.rml.beamline

    sim.params = [
        {beamline.Dipole.photonEnergy: np.arange(200, 7201, 1000)},
        {beamline.ExitSlit.totalHeight: np.array([0.1])},
        {beamline.PG.cFactor: np.array([2.25])},
        {beamline.Dipole.numberRays: 1000},
    ]
    sim.simulation_name = "test_NoAnalyze"
    sim.repeat = 2
    sim.analyze = False
    sim.raypyng_analysis = True
    sim.exports = [
        {beamline.Dipole: ["RawRaysOutgoing"]},
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]

    sim.run(multiprocessing=5, force=True)

    base_dir = Path(sim.sim_path)
    assert (base_dir / "input_param_Dipole_numberRays.dat").is_file()
    assert (base_dir / "input_param_Dipole_photonEnergy.dat").is_file()
    assert (base_dir / "input_param_ExitSlit_totalHeight.dat").is_file()
    assert (base_dir / "input_param_PG_cFactor.dat").is_file()
    assert (base_dir / "round_0").is_dir()
    assert (base_dir / "Dipole_RawRaysOutgoing.csv").is_file()
    assert (base_dir / "DetectorAtFocus_RawRaysOutgoing.csv").is_file()
