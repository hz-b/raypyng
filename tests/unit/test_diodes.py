from __future__ import annotations

import numpy as np
import pytest

from raypyng.diodes import AXUVDiode, GaASPDiode, load_data_from_py_AXUV, load_data_from_py_GaAsP


def test_axuv_diode_interpolates_and_converts_to_current():
    table = load_data_from_py_AXUV()
    diode = AXUVDiode()

    energy_keV = float((table["Energy[keV]"].iloc[0] + table["Energy[keV]"].iloc[1]) / 2)
    factor = float(
        np.interp(energy_keV, table["Energy[keV]"], table["Photon_to_nAmp_BestOf"])
    )

    current = diode.convert_photons_to_amp(
        np.array([energy_keV * 1000.0]),
        np.array([factor * 1e9]),
    )

    assert diode.check_boundary_conditions(energy_keV - 0.001)
    assert current.tolist() == pytest.approx([1.0])


def test_axuv_diode_marks_below_range_as_nan():
    table = load_data_from_py_AXUV()
    diode = AXUVDiode()
    below_range = float(table["Energy[keV]"].min() - 0.01)

    current = diode.convert_photons_to_amp(np.array([below_range * 1000.0]), np.array([1.0]))

    assert np.isnan(current[0])


def test_gaasp_data_loader_returns_expected_schema():
    assert load_data_from_py_GaAsP().columns.tolist() == ["Energy[keV]", "Photon_to_nAmp"]


def test_gaasp_diode_rejects_shape_mismatch():
    diode = GaASPDiode()

    with pytest.raises(ValueError, match="same number of elements"):
        diode.convert_photons_to_amp(np.array([1000.0, 2000.0]), np.array([1.0]))
