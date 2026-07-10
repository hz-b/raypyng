from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pandas as pd

from raypyng.graxpy_efficiency import (
    aggregate_graxpy_results,
    compute_grating_efficiency,
    elements_after_first_grating,
    read_grating_params,
    write_efficiency_csv,
)


def _write_grating_rml(tmp_path: Path) -> Path:
    rml_path = tmp_path / "grating.rml"
    rml_path.write_text(
        dedent(
            """\
            <lab>
              <beamline>
                <object name="Source" type="Undulator">
                  <param id="numberRays" enabled="T">100000</param>
                  <param id="photonEnergy" enabled="T">750</param>
                </object>
                <object name="PG" type="Plane Grating">
                  <param id="lineProfile" enabled="T" comment="blaze">1</param>
                  <param id="lineDensity" enabled="T">1200</param>
                  <param id="alpha" enabled="T">12.5</param>
                  <param id="orderDiffraction" enabled="T">1</param>
                  <param id="materialSubstrate" enabled="T">Si</param>
                  <param id="roughnessSubstrate" enabled="T">0.1</param>
                  <param id="materialCoating1" enabled="T">Au</param>
                  <param id="thicknessCoating1" enabled="T">5</param>
                  <param id="blazeAngle" enabled="T">2.0</param>
                </object>
                <object name="DetectorAtFocus" type="Detector">
                  <param id="worldPosition" enabled="F">
                    <x>0</x>
                    <y>0</y>
                    <z>20</z>
                  </param>
                </object>
              </beamline>
            </lab>
            """
        ),
        encoding="utf-8",
    )
    return rml_path


def test_read_grating_params_and_elements_after_first_grating(tmp_path: Path):
    rml_path = _write_grating_rml(tmp_path)

    grating_params = read_grating_params(rml_path)
    elements = elements_after_first_grating(rml_path)

    assert len(grating_params) == 1
    assert grating_params[0]["name"] == "PG"
    assert grating_params[0]["profile_type"] == "blaze"
    assert grating_params[0]["period_lpermm"] == 1200.0
    assert grating_params[0]["layer_material"] == "Au"
    assert grating_params[0]["layer_thickness_nm"] == 5.0
    assert grating_params[0]["energy_ev"] == 750.0
    assert elements == {"PG", "DetectorAtFocus"}


def test_compute_grating_efficiency_with_mocked_graxpy(tmp_path: Path, monkeypatch):
    rml_path = _write_grating_rml(tmp_path)
    captured = {}

    class DummyGrating:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def run_simulation(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(selected_efficiency=0.42)

    dummy_grax = SimpleNamespace(
        BlazedGrating=DummyGrating,
        LaminarGrating=DummyGrating,
        run_simulation=run_simulation,
    )
    monkeypatch.setitem(sys.modules, "grax", dummy_grax)

    results = compute_grating_efficiency(
        rml_path,
        fourier_orders=11,
        x_resolution_nm=0.2,
        z_resolution_nm=0.3,
    )

    assert results == {
        "PG": {
            "energy_ev": 750.0,
            "grazing_angle_deg": 77.5,
            "diffraction_order": 1,
            "efficiency_p": 0.42,
        }
    }
    assert captured["kwargs"]["grating"].kwargs["period_lpermm"] == 1200
    assert captured["kwargs"]["polarization"] == "p"


def test_write_and_aggregate_grating_efficiency_csvs(tmp_path: Path):
    round_0 = tmp_path / "round_0"
    round_1 = tmp_path / "round_1"
    round_0.mkdir()
    round_1.mkdir()

    write_efficiency_csv(
        round_0 / "dummy.rml",
        {
            "PG": {
                "energy_ev": 750.0,
                "grazing_angle_deg": 77.5,
                "diffraction_order": 1,
                "efficiency_p": 0.42,
            }
        },
    )
    write_efficiency_csv(
        round_1 / "dummy.rml",
        {
            "PG": {
                "energy_ev": 760.0,
                "grazing_angle_deg": 77.0,
                "diffraction_order": 1,
                "efficiency_p": 0.43,
            }
        },
    )

    aggregated = aggregate_graxpy_results(tmp_path)
    df = pd.read_csv(aggregated)

    assert aggregated == tmp_path / "graxpy_efficiency.csv"
    assert df["grating_name"].tolist() == ["PG", "PG"]
