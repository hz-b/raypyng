"""Unit tests for PostProcess.postprocess_RawRays with raw_array input.

No RAY-UI installation required — inputs are constructed in-memory.
"""

import io
import os
import tempfile

import numpy as np
import pytest

from raypyng.postprocessing import PostProcess

ELEMENT = "Toroid"
OBJECT = "RawRaysOutgoing"

_DIPOLE_RML = os.path.join(os.path.dirname(__file__), "..", "rml", "dipole.rml")


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def pp():
    return PostProcess()


@pytest.fixture
def raw_array():
    """Minimal rawdata structured array with 20 rays."""
    n = 20
    dtype = np.dtype(
        [
            ("RN", "<f8"),
            ("RS", "<f8"),
            ("RO", "<f8"),
            ("OX", "<f8"),
            ("OY", "<f8"),
            ("OZ", "<f8"),
            ("DX", "<f8"),
            ("DY", "<f8"),
            ("DZ", "<f8"),
            ("EN", "<f8"),
            ("PL", "<f8"),
            ("S0", "<f8"),
            ("S1", "<f8"),
            ("S2", "<f8"),
            ("S3", "<f8"),
        ]
    )
    arr = np.zeros(n, dtype=dtype)
    rng = np.random.default_rng(42)
    arr["OX"] = rng.normal(0, 0.5e-3, n)
    arr["OY"] = rng.normal(0, 0.1e-3, n)
    arr["DX"] = rng.normal(0, 1e-4, n)
    arr["DY"] = rng.normal(0, 1e-4, n)
    arr["DZ"] = rng.normal(1, 1e-6, n)
    arr["EN"] = 250.0
    arr["S0"] = 1.0
    arr["RS"] = 1.0
    arr["RN"] = np.arange(n)
    return arr


@pytest.fixture
def minimal_rml():
    """Path to the existing dipole.rml test file."""
    return _DIPOLE_RML


# ── field renaming ────────────────────────────────────────────────────────────


def test_raw_array_fields_prefixed_internally(pp, raw_array, minimal_rml, tmp_path):
    """postprocess_RawRays renames raw_array fields with the element prefix internally.

    We verify this indirectly: if the renaming is wrong the call raises KeyError
    or produces NaN for all numeric outputs.
    """
    dat_path = tmp_path / "0_Toroid_analyzed_rays_RawRaysOutgoing.dat"
    pp.postprocess_RawRays(
        ELEMENT,
        OBJECT,
        str(tmp_path),
        "0_",
        minimal_rml,
        suffix=OBJECT,
        remove_rawrays=False,
        raw_array=raw_array,
    )
    assert dat_path.exists(), ".dat output was not created"


# ── no CSV written ────────────────────────────────────────────────────────────


def test_no_csv_written_when_raw_array_provided(pp, raw_array, minimal_rml, tmp_path):
    """When raw_array is provided, postprocess_RawRays never reads or writes the CSV."""
    csv_path = tmp_path / f"0_{ELEMENT}-{OBJECT}.csv"
    assert not csv_path.exists()

    pp.postprocess_RawRays(
        ELEMENT,
        OBJECT,
        str(tmp_path),
        "0_",
        minimal_rml,
        suffix=OBJECT,
        remove_rawrays=False,
        raw_array=raw_array,
    )
    assert not csv_path.exists(), "CSV should NOT be written by postprocess_RawRays itself"


def test_remove_rawrays_ignored_when_raw_array_provided(pp, raw_array, minimal_rml, tmp_path):
    """remove_rawrays=True must not crash even though there is no CSV to remove."""
    pp.postprocess_RawRays(
        ELEMENT,
        OBJECT,
        str(tmp_path),
        "0_",
        minimal_rml,
        suffix=OBJECT,
        remove_rawrays=True,
        raw_array=raw_array,
    )


# ── backward compat: raw_array=None still reads from CSV ─────────────────────


def test_csv_path_still_works_when_raw_array_none(pp, raw_array, minimal_rml, tmp_path):
    """When raw_array is None the existing CSV-reading path is used."""
    import pandas

    df = pandas.DataFrame(
        {f"{ELEMENT}_{col}": raw_array[col] for col in raw_array.dtype.names}
    )
    csv_path = tmp_path / f"0_{ELEMENT}-{OBJECT}.csv"
    with open(csv_path, "w") as f:
        f.write("sep=\t\n")
        df.to_csv(f, sep="\t", index=False)

    dat_path = tmp_path / f"0_{ELEMENT}_analyzed_rays_{OBJECT}.dat"
    pp.postprocess_RawRays(
        ELEMENT,
        OBJECT,
        str(tmp_path),
        "0_",
        minimal_rml,
        suffix=OBJECT,
        remove_rawrays=False,
        raw_array=None,
    )
    assert dat_path.exists()
    assert csv_path.exists(), "CSV should remain when remove_rawrays=False"


def test_remove_rawrays_true_deletes_csv_when_raw_array_none(pp, raw_array, minimal_rml, tmp_path):
    """remove_rawrays=True deletes the CSV only when raw_array=None (old path)."""
    import pandas

    df = pandas.DataFrame(
        {f"{ELEMENT}_{col}": raw_array[col] for col in raw_array.dtype.names}
    )
    csv_path = tmp_path / f"0_{ELEMENT}-{OBJECT}.csv"
    with open(csv_path, "w") as f:
        f.write("sep=\t\n")
        df.to_csv(f, sep="\t", index=False)

    pp.postprocess_RawRays(
        ELEMENT,
        OBJECT,
        str(tmp_path),
        "0_",
        minimal_rml,
        suffix=OBJECT,
        remove_rawrays=True,
        raw_array=None,
    )
    assert not csv_path.exists(), "CSV should be deleted when remove_rawrays=True, raw_array=None"
