import os
import sys
import unittest

sys.path.insert(1, "../src")

from raypyng.simulate import Simulate


class TestAnalyze(unittest.TestCase):

    def test_1_turn_reflectivity_on(self):

        this_file_dir = os.path.dirname(os.path.realpath(__file__))
        rml_file = os.path.join(this_file_dir, "rml/elisa.rml")

        sim = Simulate(rml_file, hide=True)

        elisa = sim.rml.beamline

        sim.reflectivity(True)

        for oe in elisa.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("1", oe.reflectivityType.cdata)

    def test_0_turn_reflectivity_off(self):

        this_file_dir = os.path.dirname(os.path.realpath(__file__))
        rml_file = os.path.join(this_file_dir, "rml/elisa.rml")

        sim = Simulate(rml_file, hide=True)

        elisa = sim.rml.beamline

        sim.reflectivity(False)

        for oe in elisa.children():
            if hasattr(oe, "reflectivityType"):
                self.assertEqual("0", oe.reflectivityType.cdata)


if __name__ == "__main__":
    unittest.main(verbosity=2)
