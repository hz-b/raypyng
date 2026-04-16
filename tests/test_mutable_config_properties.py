import os
import sys
import unittest

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.abspath(os.path.join(THIS_FILE_DIR, "..", "src"))
sys.path.insert(1, SRC_DIR)

from raypyng.simulate import Simulate


class TestMutableConfigProperties(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rml_file = os.path.join(THIS_FILE_DIR, "test_bug", "rml", "elisa.rml")

    def _make_simulation(self):
        sim = Simulate(self.rml_file, hide=True)
        beamline = sim.rml.beamline
        return sim, beamline

    def test_params_append_raises_immediately(self):
        sim, beamline = self._make_simulation()

        with self.assertRaisesRegex(TypeError, "In-place mutation of 'params' is not supported"):
            sim.params.append({beamline.Dipole.photonEnergy: [200, 400]})

    def test_exports_append_raises_immediately(self):
        sim, beamline = self._make_simulation()

        with self.assertRaisesRegex(TypeError, "In-place mutation of 'exports' is not supported"):
            sim.exports.append({beamline.Dipole: ["RawRaysOutgoing"]})

    def test_run_without_params_raises_clear_error(self):
        sim, beamline = self._make_simulation()
        sim.simulation_name = "mutable_config_test"
        sim.exports = [{beamline.Dipole: ["RawRaysOutgoing"]}]

        with self.assertRaisesRegex(
            ValueError, "Simulation parameters are not configured"
        ):
            sim.run()

    def test_params_assignment_copies_input(self):
        sim, beamline = self._make_simulation()
        params = [{beamline.Dipole.photonEnergy: [200, 400]}]

        sim.params = params
        params.append({beamline.ExitSlit.totalHeight: [0.1, 0.2]})

        self.assertEqual(1, len(sim.params))
        self.assertEqual(1, len(sim.sp.ind_par))

    def test_exports_assignment_copies_input(self):
        sim, beamline = self._make_simulation()
        exports = [{beamline.Dipole: ["RawRaysOutgoing"]}]

        sim.exports = exports
        exports[0][beamline.Dipole].append("RawRaysIncoming")

        self.assertEqual(1, len(sim.exports))
        self.assertEqual([("Dipole", "RawRaysOutgoing")], sim._exports_list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
