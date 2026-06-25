"""Integration tests for the rawdata IPC stream path.

Requires the development RAY-UI binary installed at DEV_RAY_PATH.
Tests are automatically skipped when the binary is absent.
"""

import glob
import io
import os
import shutil
import tempfile

import numpy as np
import pytest

DEV_RAY_PATH = "/home/simone/Applications/Ray-UI-development-stream"
RML_FILE = os.path.join(os.path.dirname(__file__), "rml", "dipole.rml")

pytestmark = pytest.mark.skipif(
    not os.path.isdir(DEV_RAY_PATH),
    reason=f"dev RAY-UI not installed at {DEV_RAY_PATH}",
)

_RAWRAYS_ITEM_IDS = ("RawRaysOutgoing", "RawRaysIncoming", "RawRaysBeam")


# ── low-level API tests ───────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def traced_api():
    """Start RAY-UI, load dipole.rml, trace, yield API, then quit."""
    from raypyng.runner import RayUIAPI, RayUIRunner

    runner = RayUIRunner(ray_path=DEV_RAY_PATH, hide=True)
    api = RayUIAPI(runner)
    runner.run()
    api.load(RML_FILE)
    api.trace(analyze=True)
    yield api
    try:
        api.quit()
    except Exception:
        pass
    runner.kill()


def test_rawdata_returns_ndarray(traced_api):
    """api.rawdata() returns a numpy structured array with the expected columns."""
    arr = traced_api.rawdata("DetectorAtFocus", "RawRaysOutgoing")
    assert isinstance(arr, np.ndarray)
    assert arr.ndim == 1
    expected_cols = {"RN", "RS", "RO", "OX", "OY", "OZ", "DX", "DY", "DZ", "EN", "PL", "S0", "S1", "S2", "S3"}
    assert expected_cols.issubset(set(arr.dtype.names))


def test_rawdata_nonzero_rays(traced_api):
    """rawdata() returns at least one ray for a detector element after tracing."""
    arr = traced_api.rawdata("DetectorAtFocus", "RawRaysOutgoing")
    assert len(arr) > 0


def test_rawdata_incoming(traced_api):
    """rawdata() works for RawRaysIncoming on a mirror element."""
    arr = traced_api.rawdata("M1", "RawRaysIncoming")
    assert isinstance(arr, np.ndarray)
    assert arr.ndim == 1


# ── Simulate-level tests ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def dipole_rml():
    return RML_FILE


def _run_simulation(dipole_rml, remove_rawrays: bool, tmp_path):
    """Helper: run a single simulation and return the sim folder path."""
    from raypyng import Simulate
    from raypyng.rml import RMLFile

    sim = Simulate(rml=dipole_rml, folder=str(tmp_path))
    sim.ray_path = DEV_RAY_PATH
    sim.hide = True
    sim.raypyng_analysis = True
    sim.remove_rawrays = remove_rawrays

    rml = RMLFile(dipole_rml)
    exports = sim.exports
    # Accept whatever exports are defined in the dipole.rml
    sim.run(multiprocessing=False)
    return str(tmp_path)


def test_remove_rawrays_true_no_csv(dipole_rml, tmp_path):
    """remove_rawrays=True: rawrays CSV files are never written to disk."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=True, tmp_path=tmp_path)
    csv_files = glob.glob(os.path.join(sim_path, "**", "*RawRays*.csv"), recursive=True)
    assert csv_files == [], f"Found unexpected rawrays CSV files: {csv_files}"


def test_remove_rawrays_true_dat_files_exist(dipole_rml, tmp_path):
    """remove_rawrays=True: .dat analysis files are written for rawrays elements."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=True, tmp_path=tmp_path)
    dat_files = glob.glob(os.path.join(sim_path, "**", "*analyzed_rays*.dat"), recursive=True)
    assert len(dat_files) > 0, "No .dat files found — postprocessing may have failed"


def test_remove_rawrays_false_csv_preserved(dipole_rml, tmp_path):
    """remove_rawrays=False: Python writes the CSV in the expected format."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=False, tmp_path=tmp_path)
    csv_files = glob.glob(os.path.join(sim_path, "**", "*RawRays*.csv"), recursive=True)
    assert len(csv_files) > 0, "Expected CSV files when remove_rawrays=False"

    # Verify format: first line is sep=\t, second line is tab-separated header
    for csv_file in csv_files:
        with open(csv_file) as f:
            first_line = f.readline().strip()
            header_line = f.readline().strip()
        assert first_line == "sep=\t", f"Missing sep=\\t header in {csv_file}"
        cols = header_line.split("\t")
        assert len(cols) >= 5, f"Too few columns in {csv_file}: {cols}"
