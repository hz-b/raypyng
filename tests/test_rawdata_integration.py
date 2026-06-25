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
    """Helper: run a single small simulation and return the sim folder path."""
    from raypyng import Simulate

    sim = Simulate(rml=dipole_rml, hide=True, ray_path=DEV_RAY_PATH)
    sim.path = str(tmp_path)
    sim.simulation_name = "rawrays"
    sim.raypyng_analysis = True

    beamline = sim.rml.beamline
    # Minimal single-point scan; small ray count keeps the trace fast.
    sim.params = [
        {beamline.Dipole.photonEnergy: [700]},
        {beamline.Dipole.numberRays: 1000},
    ]
    sim.exports = [
        {beamline.Dipole: ["RawRaysOutgoing"]},
        {beamline.DetectorAtFocus: ["RawRaysOutgoing"]},
    ]
    sim.run(multiprocessing=1, force=True, remove_rawrays=remove_rawrays)
    return str(tmp_path)


# Per-simulation raw-ray dumps from the stream path use a dash before the item id
# ('<n>_<Element>-RawRaysOutgoing.csv') and live under round_*/. The consolidated
# raypyng-analysis output uses an underscore ('<Element>_RawRaysOutgoing.csv') and
# lives in the simulation root; only the former is governed by remove_rawrays.
def _stream_rawrays_csvs(sim_path):
    return glob.glob(os.path.join(sim_path, "**", "*-RawRays*.csv"), recursive=True)


def _consolidated_analysis_csvs(sim_path):
    return glob.glob(os.path.join(sim_path, "**", "*_RawRays*.csv"), recursive=True)


def test_remove_rawrays_true_no_csv(dipole_rml, tmp_path):
    """remove_rawrays=True: the per-sim raw-ray stream CSVs are never written."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=True, tmp_path=tmp_path)
    stream_csvs = _stream_rawrays_csvs(sim_path)
    assert stream_csvs == [], f"Found unexpected raw-ray stream CSVs: {stream_csvs}"


def test_remove_rawrays_true_analysis_output_exists(dipole_rml, tmp_path):
    """remove_rawrays=True: postprocessing still produces the consolidated analysis CSV."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=True, tmp_path=tmp_path)
    analysis_csvs = _consolidated_analysis_csvs(sim_path)
    assert len(analysis_csvs) > 0, "No consolidated analysis CSV — postprocessing may have failed"


def test_remove_rawrays_false_csv_preserved(dipole_rml, tmp_path):
    """remove_rawrays=False: the stream path writes per-sim CSVs in the expected format."""
    sim_path = _run_simulation(dipole_rml, remove_rawrays=False, tmp_path=tmp_path)
    stream_csvs = _stream_rawrays_csvs(sim_path)
    assert len(stream_csvs) > 0, "Expected raw-ray stream CSVs when remove_rawrays=False"

    # Verify format: first line is sep=\t, second line is the tab-separated header.
    for csv_file in stream_csvs:
        with open(csv_file) as f:
            # Keep the trailing tab — .strip() would remove the "\t" we're checking for.
            first_line = f.readline().rstrip("\r\n")
            header_line = f.readline().strip()
        assert first_line == "sep=\t", f"Missing sep=\\t header in {csv_file}"
        cols = header_line.split("\t")
        assert len(cols) >= 5, f"Too few columns in {csv_file}: {cols}"
