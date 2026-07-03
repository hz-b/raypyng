from __future__ import annotations

import pytest

from raypyng.vls_grating import N1_to_b2, cff_for_fixed_focus, calculate_vls_coeff


def test_calculate_vls_coeff_matches_known_baseline():
    assert calculate_vls_coeff(verbose=False) == pytest.approx(
        (
            2.8631733660494936e-05,
            7.10324084801985e-09,
            2.105973778552881e-12,
            9.78095856175572e-16,
        ),
        rel=1e-12,
    )


def test_n1_to_b2_converts_units():
    assert N1_to_b2(2400, 1200) == pytest.approx(0.01)


def test_cff_for_fixed_focus_matches_known_baseline():
    assert cff_for_fixed_focus(0.01, 1000.0, 1200.0, verbose=False) == pytest.approx(
        1.0026903814904344,
        rel=1e-12,
    )
