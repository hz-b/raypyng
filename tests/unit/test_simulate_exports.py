"""Unit tests for Simulate export validation.

No RAY-UI installation required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from raypyng.simulate import Simulate

_RML = str(Path(__file__).parent.parent / "rml" / "dipole.rml")


@pytest.fixture
def sim():
    s = Simulate(_RML, hide=True)
    s.simulation_name = "test"
    s.analyze = True
    return s


def test_intensity2d_in_possible_exports(sim):
    """Intensity2D must appear in the list of valid exports."""
    assert "Intensity2D" in sim.possible_exports


def test_intensity2d_accepted_as_export(sim):
    """Setting exports with Intensity2D must not raise."""
    beamline = sim.rml.beamline
    sim.exports = [{beamline.DetectorAtFocus: ["Intensity2D"]}]


def test_unknown_export_still_rejected(sim):
    """A non-existent export type must still raise ValueError."""
    beamline = sim.rml.beamline
    with pytest.raises(ValueError, match="Cannot export"):
        sim.exports = [{beamline.DetectorAtFocus: ["NotARealExport"]}]
