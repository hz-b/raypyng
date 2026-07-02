from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import numpy as np

from raypyng.recipes import BeamWaist, Flux, ResolvingPower
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
                  <param id="worldPosition" enabled="F">
                    <x>0</x>
                    <y>0</y>
                    <z>100</z>
                  </param>
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
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]
    assert recipe.simulation_name(sim) == "Beamwaist"
