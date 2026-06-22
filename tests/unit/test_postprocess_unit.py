"""Unit tests for PostProcess helper methods.

No RAY-UI installation required — all inputs are constructed in-memory.
"""

import numpy as np
import pandas as pd
import pytest

from raypyng.postprocessing import PostProcess


@pytest.fixture
def pp():
    return PostProcess()


# ── _extract_intensity ────────────────────────────────────────────────────────


def test_extract_intensity_rowcount(pp):
    """Plain ndarray (no named columns) → returns row count."""
    rays = np.zeros((17, 3))
    assert pp._extract_intensity(rays) == 17


def test_extract_intensity_weight_column(pp):
    """Structured array with a _W column → returns sum of weights."""
    dtype = np.dtype([("MyElement_OX", float), ("MyElement_W", float)])
    weights = np.array([10.0, 15.5, 17.0])
    rays = np.array(
        list(zip(np.zeros(3), weights)),
        dtype=dtype,
    )
    result = pp._extract_intensity(rays)
    assert abs(result - 42.5) < 1e-9


def test_extract_intensity_ignores_non_W_columns(pp):
    """Structured array without a _W column → falls back to row count."""
    dtype = np.dtype([("MyElement_OX", float), ("MyElement_OY", float)])
    rays = np.zeros(5, dtype=dtype)
    assert pp._extract_intensity(rays) == 5


def test_extract_intensity_single_row(pp):
    """Single ray with weight column → returns that weight."""
    dtype = np.dtype([("Det_W", float)])
    rays = np.array([(3.14,)], dtype=dtype)
    result = pp._extract_intensity(rays)
    assert abs(result - 3.14) < 1e-9


# ── _calculate_percentage_rays ────────────────────────────────────────────────


def test_calculate_percentage_no_efficiency(pp):
    assert pp._calculate_percentage_rays(500, 1000) == pytest.approx(50.0)


def test_calculate_percentage_full_transmission(pp):
    assert pp._calculate_percentage_rays(1000, 1000) == pytest.approx(100.0)


def test_calculate_percentage_zero(pp):
    assert pp._calculate_percentage_rays(0, 1000) == pytest.approx(0.0)


def test_calculate_percentage_with_efficiency(pp):
    """Efficiency table is interpolated and applied correctly."""
    efficiency_df = pd.DataFrame(
        {"Energy[eV]": [400.0, 600.0], "Efficiency": [0.10, 0.20]}
    )
    # At 500 eV the interpolated efficiency is 0.15
    result = pp._calculate_percentage_rays(
        500, 1000, efficiency=efficiency_df, photon_energy=500.0
    )
    expected = 500 / 1000 * 100 * 0.15
    assert result == pytest.approx(expected, rel=1e-6)


def test_calculate_percentage_efficiency_extrapolation_low(pp):
    """Efficiency clamps to table edge below the range (np.interp behaviour)."""
    efficiency_df = pd.DataFrame(
        {"Energy[eV]": [500.0, 1000.0], "Efficiency": [0.5, 1.0]}
    )
    result = pp._calculate_percentage_rays(
        100, 1000, efficiency=efficiency_df, photon_energy=200.0
    )
    # np.interp clamps to 0.5 below range
    expected = 100 / 1000 * 100 * 0.5
    assert result == pytest.approx(expected, rel=1e-6)


# ── _extract_fwhm ─────────────────────────────────────────────────────────────


def test_extract_fwhm_gaussian(pp):
    """FWHM of a Gaussian sample matches 2.355 * sigma within 15 %.

    The implementation uses a 30-bin histogram; bin quantization alone
    introduces up to ~7 % error, so we use a generous tolerance here.
    """
    rng = np.random.default_rng(42)
    sigma = 2.0
    samples = rng.normal(loc=0.0, scale=sigma, size=50_000)
    fwhm = pp._extract_fwhm(samples)
    expected = 2 * np.sqrt(2 * np.log(2)) * sigma  # ≈ 4.709
    assert abs(fwhm - expected) / expected < 0.15


def test_extract_fwhm_few_rays_no_exception(pp):
    """With fewer than 100 rays the std-based fallback must not raise."""
    rng = np.random.default_rng(7)
    samples = rng.normal(0.0, 1.0, size=50)
    fwhm = pp._extract_fwhm(samples)
    assert fwhm > 0


def test_extract_fwhm_uniform(pp):
    """FWHM of a uniform distribution [0, L] equals L (all bins at max height).

    For a flat histogram every bin is at the maximum, so the half-max
    crossing spans the full distribution width.
    """
    rng = np.random.default_rng(99)
    L = 10.0
    samples = rng.uniform(0.0, L, size=100_000)
    fwhm = pp._extract_fwhm(samples)
    assert abs(fwhm - L) / L < 0.05
