import os
import sys
import unittest

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.abspath(os.path.join(THIS_FILE_DIR, "..", "..", "src"))
sys.path.insert(1, SRC_DIR)

from raypyng.simulate import Simulate


class TestAnalyze(unittest.TestCase):

    def test_1_turn_reflectivity_on(self):

        rml_file = os.path.join(THIS_FILE_DIR, "..", "data", "rml", "dipole.rml")

        sim = Simulate(rml_file, hide=True)

        beamline = sim.rml.beamline

        sim.reflectivity(True)

        for oe in beamline.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("1", oe.reflectivityType.cdata)

    def test_0_turn_reflectivity_off(self):

        rml_file = os.path.join(THIS_FILE_DIR, "..", "data", "rml", "dipole.rml")

        sim = Simulate(rml_file, hide=True)

        beamline = sim.rml.beamline

        sim.reflectivity(False)

        for oe in beamline.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("0", oe.reflectivityType.cdata)


if __name__ == "__main__":
    unittest.main(verbosity=2)
