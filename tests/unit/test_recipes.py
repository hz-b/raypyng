from __future__ import annotations

from collections import OrderedDict
import sys
import types
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
PACKAGE_DIR = SRC_DIR / "raypyng"
sys.path.insert(1, str(SRC_DIR))

if "raypyng" not in sys.modules:
    package = types.ModuleType("raypyng")
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules["raypyng"] = package

from raypyng.recipes import (
    BeamWaist,
    Flux,
    PerElementVibrationScan,
    ResolvingPower,
    Roughness,
    Slopes,
    plot_per_element_vibration_scan,
    plot_roughness_scan,
    plot_slopes_scan,
)
from raypyng.rml import RMLFile


def _build_sim(tmp_path: Path, *, analyze: bool = True):
    rml_path = tmp_path / "recipe_fixture.rml"
    rml_path.write_text(
        dedent(
            """\
            <lab>
              <beamline>
                <object name="Source" type="Undulator">
                  <param id="photonEnergy" enabled="T">1000</param>
                  <param id="numberRays" enabled="T">100000</param>
                </object>
                <object name="Mirror" type="Toroid">
                  <param id="reflectivityType" enabled="T">0</param>
                  <param id="slopeError" comment="Yes" enabled="T">0</param>
                  <param id="slopeErrorMer" enabled="T">0.05</param>
                  <param id="slopeErrorSag" enabled="T">0.5</param>
                  <param id="roughnessSubstrate" enabled="T">0</param>
                  <param id="roughnessCoating1" enabled="T">0.2</param>
                  <param id="roughnessCoating2" enabled="F">0</param>
                  <param id="roughnessTopLayer" enabled="F">0</param>
                  <param id="alignmentError" comment="Yes" enabled="T">0</param>
                  <param id="translationXerror" enabled="T">0</param>
                  <param id="translationYerror" enabled="T">0</param>
                  <param id="translationZerror" enabled="T">0</param>
                  <param id="rotationXerror" enabled="T">0</param>
                  <param id="rotationYerror" enabled="T">0</param>
                  <param id="rotationZerror" enabled="T">0</param>
                  <param id="worldPosition" enabled="F">
                    <x>0</x>
                    <y>0</y>
                    <z>100</z>
                  </param>
                </object>
                <object name="MirrorTwo" type="Toroid">
                  <param id="reflectivityType" enabled="T">0</param>
                  <param id="slopeError" comment="Yes" enabled="T">0</param>
                  <param id="slopeErrorMer" enabled="T">0.07</param>
                  <param id="slopeErrorSag" enabled="T">0.7</param>
                  <param id="roughnessSubstrate" enabled="T">0</param>
                  <param id="alignmentError" comment="Yes" enabled="T">0</param>
                  <param id="translationXerror" enabled="T">0</param>
                  <param id="rotationZerror" enabled="T">0</param>
                </object>
                <object name="DetectorAtFocus" type="Detector">
                  <param id="worldPosition" enabled="F">
                    <x>0</x>
                    <y>0</y>
                    <z>200</z>
                  </param>
                </object>
              </beamline>
            </lab>
            """
        ),
        encoding="utf-8",
    )
    return SimpleNamespace(rml=RMLFile(str(rml_path)), analyze=analyze)


def test_resolving_power_uses_source_energy_and_disables_reflectivity(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=True)
    beamline = sim.rml.beamline
    recipe = ResolvingPower(
        np.array([500.0, 600.0]),
        beamline.DetectorAtFocus,
        sim_folder="rp-scan",
    )

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert np.array_equal(params[0][beamline.Source.photonEnergy], np.array([500.0, 600.0]))
    assert any(d.get(beamline.Mirror.reflectivityType) == 0 for d in params)
    assert exports == [{beamline.DetectorAtFocus: ["ScalarBeamProperties"]}]
    assert recipe.simulation_name(sim) == "rp-scan"


def test_flux_uses_source_energy_and_turns_reflectivity_on(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = Flux(np.array([750.0]), beamline.DetectorAtFocus)

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert np.array_equal(params[0][beamline.Source.photonEnergy], np.array([750.0]))
    assert any(d.get(beamline.Mirror.reflectivityType) == 1 for d in params)
    assert exports == [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    assert recipe.simulation_name(sim) == "Flux"


def test_beamwaist_exports_every_beamline_element(tmp_path: Path):
    sim = _build_sim(tmp_path)
    beamline = sim.rml.beamline
    recipe = BeamWaist(750.0)

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert params[0][beamline.Source.photonEnergy] == 750.0
    assert any(d.get(beamline.Mirror.reflectivityType) == 0 for d in params)
    assert exports == [
        {beamline.Source: ["RawRaysOutgoing"]},
        {beamline.Mirror: ["RawRaysOutgoing"]},
        {beamline.MirrorTwo: ["RawRaysOutgoing"]},
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]
    assert recipe.simulation_name(sim) == "Beamwaist"


def test_recipe_import_surface_exposes_existing_and_new_symbols():
    from raypyng.recipes import (
        BeamWaist,
        Flux,
        PerElementVibrationScan,
        ResolvingPower,
        Roughness,
        Slopes,
        plot_per_element_vibration_scan,
        plot_roughness_scan,
        plot_slopes_scan,
    )

    assert BeamWaist is not None
    assert Flux is not None
    assert PerElementVibrationScan is not None
    assert ResolvingPower is not None
    assert Roughness is not None
    assert Slopes is not None
    assert callable(plot_per_element_vibration_scan)
    assert callable(plot_roughness_scan)
    assert callable(plot_slopes_scan)


def test_roughness_recipe_sets_beamline_state_and_builds_grouped_scan(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = Roughness(
        np.array([750.0, 800.0]),
        beamline.DetectorAtFocus,
        {beamline.DetectorAtFocus.worldPosition.z: [200]},
        roughness_values=np.array([0.1, 0.3]),
        preferred_value=0.3,
        nrays=12345,
        rounds=7,
        sim_folder="roughness-scan",
    )

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert np.array_equal(params[0][beamline.Source.photonEnergy], np.array([750.0, 800.0]))
    assert params[1] == {beamline.DetectorAtFocus.worldPosition.z: [200]}
    assert params[2] == {beamline.Source.numberRays: 12345}

    assert beamline.Mirror.reflectivity_enabled is True
    assert beamline.MirrorTwo.reflectivity_enabled is True
    assert beamline.Mirror.slope_error_enabled is False
    assert beamline.MirrorTwo.slope_error_enabled is False

    scan_dict = params[3]
    assert scan_dict[beamline.Mirror.roughnessSubstrate] == [0, 0.3, 0.1, 0.3, 0, 0]
    assert scan_dict[beamline.Mirror.roughnessCoating1] == [0, 0.3, 0.1, 0.3, 0, 0]
    assert scan_dict[beamline.MirrorTwo.roughnessSubstrate] == [0, 0.3, 0, 0, 0.1, 0.3]
    assert beamline.Mirror.roughnessCoating2 not in scan_dict
    assert beamline.Mirror.roughnessTopLayer not in scan_dict

    assert exports == [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    assert recipe.simulation_name(sim) == "roughness-scan"
    assert recipe.rounds == 7


def test_plot_roughness_scan_creates_summary_and_per_element_plots(tmp_path: Path):
    sim_folder = tmp_path / "RAYPy_Simulation_Roughness"
    sim_folder.mkdir()
    df = pd.DataFrame(
        {
            "Source.photonEnergy": [500, 500, 500, 500],
            "ExitSlit.openingHeight": [0.1, 0.1, 0.1, 0.1],
            "Mirror.roughnessSubstrate": [0.0, 0.3, 0.1, 0.0],
            "Mirror.roughnessCoating1": [0.0, 0.3, 0.1, 0.0],
            "MirrorTwo.roughnessSubstrate": [0.0, 0.3, 0.0, 0.1],
            "Bandwidth": [1.0, 1.2, 1.1, 1.15],
            "HorizontalFocusFWHM": [0.01, 0.011, 0.012, 0.013],
            "VerticalFocusFWHM": [0.02, 0.021, 0.022, 0.023],
        }
    )
    recap_path = sim_folder / "DetectorAtFocus_RawRaysOutgoing.csv"
    df.to_csv(recap_path, index=False)

    paths = plot_roughness_scan(sim_folder, showplot=False, saveplot=True)

    names = {path.name for path in paths}
    assert "roughness_summary_0p1.png" in names
    assert "roughness_Mirror_0p1.png" in names
    assert "roughness_MirrorTwo_0p1.png" in names


def test_slopes_recipe_sets_beamline_state_and_builds_scan(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = Slopes(
        np.array([750.0, 800.0]),
        beamline.DetectorAtFocus,
        {beamline.DetectorAtFocus.worldPosition.z: [200]},
        slope_values={
            beamline.Mirror.slopeErrorMer: {"slope_values": np.array([0.03, 0.05]), "reference_value": 0.05},
            beamline.Mirror.slopeErrorSag: {"slope_values": np.array([0.3, 0.5]), "reference_value": 0.5},
            beamline.MirrorTwo.slopeErrorMer: {"slope_values": np.array([0.07, 0.09]), "reference_value": 0.07},
            beamline.MirrorTwo.slopeErrorSag: {"slope_values": np.array([0.7, 0.9]), "reference_value": 0.7},
        },
        nrays=22222,
        rounds=5,
        sim_folder="slopes-scan",
    )

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert np.array_equal(params[0][beamline.Source.photonEnergy], np.array([750.0, 800.0]))
    assert params[1] == {beamline.DetectorAtFocus.worldPosition.z: [200]}
    assert params[2] == {beamline.Source.numberRays: 22222}
    assert beamline.Mirror.reflectivity_enabled is True
    assert beamline.MirrorTwo.reflectivity_enabled is True
    assert beamline.Mirror.slope_error_enabled is True
    assert beamline.MirrorTwo.slope_error_enabled is True

    scan_dict = params[3]
    assert scan_dict[beamline.Mirror.slopeErrorMer] == [0, 0.05, 0.03, 0.05, 0, 0]
    assert scan_dict[beamline.Mirror.slopeErrorSag] == [0, 0.5, 0.3, 0.5, 0, 0]
    assert scan_dict[beamline.MirrorTwo.slopeErrorMer] == [0, 0.07, 0, 0, 0.07, 0.09]
    assert scan_dict[beamline.MirrorTwo.slopeErrorSag] == [0, 0.7, 0, 0, 0.7, 0.9]
    assert exports == [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    assert recipe.simulation_name(sim) == "slopes-scan"
    assert recipe.rounds == 5


def test_plot_slopes_scan_creates_summary_and_per_element_plots(tmp_path: Path):
    sim_folder = tmp_path / "RAYPy_Simulation_Slopes"
    sim_folder.mkdir()
    df = pd.DataFrame(
        {
            "Source.photonEnergy": [500, 500, 500, 500, 500, 500, 500, 500],
            "ExitSlit.openingHeight": [0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05],
            "Mirror.slopeErrorMer": [0.0, 0.05, 0.03, 0.0, 0.0, 0.05, 0.03, 0.0],
            "Mirror.slopeErrorSag": [0.0, 0.5, 0.3, 0.0, 0.0, 0.5, 0.3, 0.0],
            "MirrorTwo.slopeErrorMer": [0.0, 0.07, 0.0, 0.09, 0.0, 0.07, 0.0, 0.09],
            "MirrorTwo.slopeErrorSag": [0.0, 0.7, 0.0, 0.9, 0.0, 0.7, 0.0, 0.9],
            "Bandwidth": [1.0, 1.2, 1.1, 1.15, 0.8, 0.85, 0.82, 0.88],
            "HorizontalFocusFWHM": [0.01, 0.011, 0.012, 0.013, 0.05, 0.051, 0.052, 0.053],
            "VerticalFocusFWHM": [0.02, 0.021, 0.022, 0.023, 0.06, 0.061, 0.062, 0.063],
        }
    )
    recap_path = sim_folder / "DetectorAtFocus_RawRaysOutgoing.csv"
    df.to_csv(recap_path, index=False)

    paths = plot_slopes_scan(sim_folder, showplot=False, saveplot=True)

    names = {path.name for path in paths}
    assert "slopes_summary.png" in names
    assert "slopes_Mirror.png" in names
    assert "slopes_MirrorTwo.png" in names
    assert "slopes_summary_0p1.png" not in names
    assert "slopes_summary_0p05.png" not in names


def test_slopes_recipe_accepts_legacy_tuple_config(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = Slopes(
        np.array([750.0]),
        beamline.DetectorAtFocus,
        slope_values={
            beamline.Mirror.slopeErrorMer: (np.array([0.03, 0.05]), 0.05),
            beamline.Mirror.slopeErrorSag: (np.array([0.3, 0.5]), 0.5),
        },
    )

    params = recipe.params(sim)
    scan_dict = params[1]

    assert scan_dict[beamline.Mirror.slopeErrorMer] == [0, 0.05, 0.03, 0.05]
    assert scan_dict[beamline.Mirror.slopeErrorSag] == [0, 0.5, 0.3, 0.5]


def test_per_element_vibration_scan_builds_scan_and_disables_other_effects(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = PerElementVibrationScan(
        750.0,
        beamline.DetectorAtFocus,
        {beamline.DetectorAtFocus.worldPosition.z: [200]},
        max_rms_nm=2,
        transfer_factor={
            "translationXerror": 10,
            "translationYerror": 20,
            "translationZerror": 30,
            "rotationXerror": 40,
            "rotationYerror": 50,
            "rotationZerror": 60,
        },
        nrays=12345,
        n_scan_points=3,
        rounds=4,
        sim_folder="per-element-vibration-scan",
    )

    params = recipe.params(sim)
    exports = recipe.exports(sim)

    assert params[0][beamline.Source.photonEnergy] == 750.0
    assert params[1] == {beamline.DetectorAtFocus.worldPosition.z: [200]}
    assert params[2] == {beamline.Source.numberRays: 12345}

    assert beamline.Mirror.reflectivity_enabled is False
    assert beamline.MirrorTwo.reflectivity_enabled is False
    assert beamline.Mirror.slope_error_enabled is False
    assert beamline.MirrorTwo.slope_error_enabled is False
    assert beamline.Mirror.alignment_error_enabled is False
    assert beamline.MirrorTwo.alignment_error_enabled is False

    scan_dict = params[3]
    assert len(scan_dict) == 10
    assert scan_dict[beamline.Mirror.alignmentError][:9] == [0] * 9
    assert scan_dict[beamline.MirrorTwo.alignmentError][:9] == [1] * 9
    assert scan_dict[beamline.Mirror.translationXerror][:3] == [-20.0, 0.0, 20.0]
    assert scan_dict[beamline.Mirror.translationYerror][:3] == [0.0, 0.0, 0.0]
    assert scan_dict[beamline.Mirror.rotationXerror][9:12] == [-80.0, 0.0, 80.0]
    assert scan_dict[beamline.MirrorTwo.translationXerror][:18] == [0.0] * 18
    assert scan_dict[beamline.MirrorTwo.translationXerror][18:21] == [-20.0, 0.0, 20.0]
    assert scan_dict[beamline.MirrorTwo.rotationZerror][21:24] == [-120.0, 0.0, 120.0]
    assert exports == [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    assert recipe.simulation_name(sim) == "per-element-vibration-scan"
    assert recipe.rounds == 4


def test_per_element_vibration_scan_accepts_scalar_transfer_factor(tmp_path: Path, capsys):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline
    recipe = PerElementVibrationScan(
        750.0,
        beamline.DetectorAtFocus,
        max_rms_nm=1.5,
        transfer_factor=30,
        nrays=1000,
        n_scan_points=2,
    )

    params = recipe.params(sim)
    scan_dict = params[2]
    captured = capsys.readouterr()

    assert "requested n_scan_points=2 is even; using 3" in captured.out
    assert recipe.n_scan_points == 3
    assert scan_dict[beamline.Mirror.translationXerror][:3] == [-45.0, 0.0, 45.0]
    assert scan_dict[beamline.Mirror.rotationXerror][9:12] == [-45.0, 0.0, 45.0]


def test_per_element_vibration_scan_rejects_invalid_transfer_factor_key(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline

    try:
        PerElementVibrationScan(
            750.0,
            beamline.DetectorAtFocus,
            max_rms_nm=1,
            transfer_factor={"notARealParam": 10},
            nrays=1000,
        )
    except ValueError as exc:
        assert "unsupported alignment parameter names" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid transfer_factor key")


def test_per_element_vibration_scan_rejects_invalid_scan_points(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline

    try:
        PerElementVibrationScan(
            750.0,
            beamline.DetectorAtFocus,
            max_rms_nm=1,
            nrays=1000,
            n_scan_points=1,
        )
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid n_scan_points")


def test_per_element_vibration_scan_rejects_non_scalar_energy(tmp_path: Path):
    sim = _build_sim(tmp_path, analyze=False)
    beamline = sim.rml.beamline

    try:
        PerElementVibrationScan(
            np.array([750.0]),
            beamline.DetectorAtFocus,
            max_rms_nm=1,
            nrays=1000,
        )
    except TypeError as exc:
        assert "energy must be a number" in str(exc)
    else:
        raise AssertionError("Expected TypeError for non-scalar energy")


def test_plot_per_element_vibration_scan_creates_expected_figures(tmp_path: Path):
    sim_folder = tmp_path / "RAYPy_Simulation_PerElementVibrationScan"
    sim_folder.mkdir()
    df = pd.DataFrame(
        {
            "Source.photonEnergy": [500] * 8,
            "Mirror.alignmentError": [0, 0, 0, 0, 1, 1, 1, 1],
            "Mirror.translationXerror": [-10.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "Mirror.translationYerror": [0.0, 0.0, 0.0, -20.0, 0.0, 0.0, 0.0, 0.0],
            "Mirror.translationZerror": [0.0] * 8,
            "Mirror.rotationXerror": [0.0] * 8,
            "Mirror.rotationYerror": [0.0] * 8,
            "Mirror.rotationZerror": [0.0] * 8,
            "MirrorTwo.alignmentError": [1, 1, 1, 1, 0, 0, 0, 0],
            "MirrorTwo.translationXerror": [0.0, 0.0, 0.0, 0.0, -5.0, 0.0, 5.0, 0.0],
            "MirrorTwo.rotationZerror": [0.0, 0.0, 0.0, 0.0, 0.0, -15.0, 0.0, 15.0],
            "Bandwidth": [1.0, 1.1, 1.2, 1.15, 0.9, 0.95, 1.0, 1.05],
            "HorizontalCenter": [0.0, 0.1, 0.2, 0.15, -0.2, -0.1, 0.0, 0.1],
            "VerticalCenter": [0.0, -0.1, -0.2, -0.15, 0.2, 0.1, 0.0, -0.1],
        }
    )
    recap_path = sim_folder / "DetectorAtFocus_RawRaysOutgoing.csv"
    df.to_csv(recap_path, index=False)

    paths = plot_per_element_vibration_scan(sim_folder, showplot=False, saveplot=True)

    names = {path.name for path in paths}
    assert "per_element_vibration_scan_bandwidth.png" in names
    assert "per_element_vibration_scan_centers.png" in names


def test_plot_per_element_vibration_scan_deduplicates_center_point(tmp_path: Path):
    sim_folder = tmp_path / "RAYPy_Simulation_PerElementVibrationScan_Dedup"
    sim_folder.mkdir()
    df = pd.DataFrame(
        {
            "Source.photonEnergy": [500] * 4,
            "Mirror.alignmentError": [0, 0, 0, 0],
            "Mirror.translationXerror": [-10.0, 0.0, 0.0, 10.0],
            "Mirror.translationYerror": [0.0, -20.0, 0.0, 0.0],
            "Bandwidth": [1.0, 1.1, 1.15, 1.2],
            "HorizontalCenter": [0.0, 0.1, 0.15, 0.2],
            "VerticalCenter": [0.0, -0.1, -0.15, -0.2],
        }
    )
    recap_path = sim_folder / "DetectorAtFocus_RawRaysOutgoing.csv"
    df.to_csv(recap_path, index=False)

    plot_df = pd.read_csv(recap_path)
    element_names = ["Mirror"]
    parameter_columns = {"Mirror": OrderedDict({"translationXerror": "Mirror.translationXerror"})}

    from raypyng.recipes.per_element_vibration_scan import _scan_subset

    subset = _scan_subset(
        plot_df,
        element_names,
        parameter_columns,
        "Mirror",
        "translationXerror",
    )

    assert subset["Mirror.translationXerror"].tolist() == [-10.0, 0.0, 10.0]
