import os
import sys
import types
import unittest

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.abspath(os.path.join(THIS_FILE_DIR, "..", "..", "src"))
sys.path.insert(1, SRC_DIR)

if "raypyng" not in sys.modules:
    package = types.ModuleType("raypyng")
    package.__path__ = [os.path.join(SRC_DIR, "raypyng")]
    sys.modules["raypyng"] = package

if "raypyng.runner" not in sys.modules:
    runner = types.ModuleType("raypyng.runner")

    class _DummyRunner:
        def __init__(self, *args, **kwargs):
            self._path = None

    class _DummyAPI:
        pass

    runner.RayUIRunner = _DummyRunner
    runner.RayUIAPI = _DummyAPI
    sys.modules["raypyng.runner"] = runner

from raypyng.simulate import Simulate


class TestAnalyze(unittest.TestCase):
    def _sim(self):
        rml_file = os.path.join(THIS_FILE_DIR, "..", "data", "rml", "dipole.rml")
        return Simulate(rml_file, hide=True)

    def test_1_turn_reflectivity_on(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.reflectivity(True)

        for oe in beamline.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("1", oe.reflectivityType.cdata)
                self.assertEqual("DerivedbyMaterial", oe.reflectivityType.attributes()["comment"])

    def test_0_turn_reflectivity_off(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.reflectivity(False)

        for oe in beamline.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("0", oe.reflectivityType.cdata)
                self.assertEqual("100%", oe.reflectivityType.attributes()["comment"])

    def test_turn_slope_errors_on(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.slope_errors(True)

        for oe in beamline.children():
            if hasattr(oe, "slopeError"):
                self.assertEqual("0", oe.slopeError.cdata)
                self.assertEqual("Yes", oe.slopeError.attributes()["comment"])

    def test_turn_slope_errors_off(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.slope_errors(False)

        for oe in beamline.children():
            if hasattr(oe, "slopeError"):
                self.assertEqual("1", oe.slopeError.cdata)
                self.assertEqual("No", oe.slopeError.attributes()["comment"])

    def test_turn_alignment_errors_on(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.alignment_errors(True)

        for oe in beamline.children():
            if hasattr(oe, "alignmentError"):
                self.assertEqual("0", oe.alignmentError.cdata)
                self.assertEqual("Yes", oe.alignmentError.attributes()["comment"])

    def test_turn_alignment_errors_off(self):
        sim = self._sim()

        beamline = sim.rml.beamline

        sim.alignment_errors(False)

        for oe in beamline.children():
            if hasattr(oe, "alignmentError"):
                self.assertEqual("1", oe.alignmentError.cdata)
                self.assertEqual("No", oe.alignmentError.attributes()["comment"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
