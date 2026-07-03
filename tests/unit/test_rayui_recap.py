from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from raypyng.simulate import Simulate

_RML = str(Path(__file__).parent.parent / "data" / "rml" / "dipole.rml")


def _write_rayui_export(
    path: Path,
    header: list[str],
    row: list[object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "sep=\t\n"
        + "\t".join(header)
        + "\n"
        + "\t".join(str(value) for value in row)
        + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def sim(tmp_path: Path):
    sim = Simulate(_RML, hide=True)
    sim.sim_path = str(tmp_path / "RAYPy_Simulation_test")
    Path(sim.sim_path).mkdir(parents=True, exist_ok=True)
    sim.repeat = 2
    sim.analyze = True
    return sim


def test_create_rayui_recap_files_per_configured_export(sim: Simulate):
    beamline = sim.rml.beamline
    sim.exports = [
        {beamline.Dipole: ["ScalarElementProperties"]},
        {beamline.DetectorAtFocus: ["ScalarBeamProperties"]},
    ]

    looper = pd.DataFrame(
        {
            "Simulation Number": [0, 1],
            "Dipole.photonEnergy": [100.0, 200.0],
            "PG.cFactor": [2.25, 2.25],
        }
    )
    looper.to_csv(Path(sim.sim_path) / "looper.csv", index=False)

    for round_n, offset in [(0, 0.0), (1, 2.0)]:
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "0_DetectorAtFocus-ScalarBeamProperties.csv",
            ["#DetectorAtFocus_energyH_width", "DetectorAtFocus_efficiency"],
            [1.0 + offset, 50.0 + offset],
        )
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "1_DetectorAtFocus-ScalarBeamProperties.csv",
            ["#DetectorAtFocus_energyH_width", "DetectorAtFocus_efficiency"],
            [2.0 + offset, 60.0 + offset],
        )
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "0_Dipole-ScalarElementProperties.csv",
            ["#Dipole_photonEnergy", "Dipole_bandwidth"],
            [100.0 + offset, 0.1 + offset / 10.0],
        )
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "1_Dipole-ScalarElementProperties.csv",
            ["#Dipole_photonEnergy", "Dipole_bandwidth"],
            [200.0 + offset, 0.2 + offset / 10.0],
        )

    sim._create_rayui_results_dataframe()

    detector = pd.read_csv(Path(sim.sim_path) / "DetectorAtFocus_ScalarBeamProperties.csv")
    dipole = pd.read_csv(Path(sim.sim_path) / "Dipole_ScalarElementProperties.csv")

    assert detector.columns.tolist() == [
        "Simulation Number",
        "Dipole.photonEnergy",
        "PG.cFactor",
        "DetectorAtFocus_energyH_width",
        "DetectorAtFocus_efficiency",
    ]
    assert detector["DetectorAtFocus_energyH_width"].tolist() == [2.0, 3.0]
    assert detector["DetectorAtFocus_efficiency"].tolist() == [51.0, 61.0]
    assert detector["Dipole.photonEnergy"].tolist() == [100.0, 200.0]

    assert dipole.columns.tolist() == [
        "Simulation Number",
        "Dipole.photonEnergy",
        "PG.cFactor",
        "Dipole_photonEnergy",
        "Dipole_bandwidth",
    ]
    assert dipole["Dipole_photonEnergy"].tolist() == [101.0, 201.0]
    assert dipole["Dipole_bandwidth"].tolist() == [0.2, 0.3]


def test_rayui_recap_missing_file_raises_clear_error(sim: Simulate):
    beamline = sim.rml.beamline
    sim.exports = [{beamline.DetectorAtFocus: ["ScalarBeamProperties"]}]
    pd.DataFrame({"Simulation Number": [0], "Dipole.photonEnergy": [100.0]}).to_csv(
        Path(sim.sim_path) / "looper.csv",
        index=False,
    )
    _write_rayui_export(
        Path(sim.sim_path) / "round_0" / "0_DetectorAtFocus-ScalarBeamProperties.csv",
        ["#DetectorAtFocus_energyH_width", "DetectorAtFocus_efficiency"],
        [1.0, 50.0],
    )

    with pytest.raises(FileNotFoundError, match="Missing expected RAY-UI analysis output"):
        sim._create_rayui_results_dataframe()


def test_rayui_recap_only_emits_configured_exports(sim: Simulate):
    beamline = sim.rml.beamline
    sim.exports = [{beamline.DetectorAtFocus: ["ScalarBeamProperties"]}]
    pd.DataFrame({"Simulation Number": [0], "Dipole.photonEnergy": [100.0]}).to_csv(
        Path(sim.sim_path) / "looper.csv",
        index=False,
    )

    for round_n in range(sim.repeat):
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "0_DetectorAtFocus-ScalarBeamProperties.csv",
            ["#DetectorAtFocus_energyH_width", "DetectorAtFocus_efficiency"],
            [1.0 + round_n, 50.0 + round_n],
        )
        _write_rayui_export(
            Path(sim.sim_path) / f"round_{round_n}" / "0_Dipole-ScalarElementProperties.csv",
            ["#Dipole_photonEnergy", "Dipole_bandwidth"],
            [100.0 + round_n, 0.1 + round_n],
        )

    sim._create_rayui_results_dataframe()

    assert (Path(sim.sim_path) / "DetectorAtFocus_ScalarBeamProperties.csv").exists()
    assert not (Path(sim.sim_path) / "Dipole_ScalarElementProperties.csv").exists()
