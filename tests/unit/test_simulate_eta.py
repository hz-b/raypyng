from __future__ import annotations

from pathlib import Path

from raypyng.simulate import Simulate

_RML = str(Path(__file__).parent.parent / "rml" / "dipole.rml")


class _DummyPbar:
    def __init__(self, total=10):
        self.total = total
        self.n = 0
        self.postfix = None

    def set_postfix_str(self, value, refresh=True):
        self.postfix = value

    def update(self, amount):
        self.n += amount


def test_initial_eta_seed_fixed_number_rays():
    sim = Simulate(_RML, hide=True)
    beamline = sim.rml.beamline
    sim.params = [
        {beamline.Dipole.photonEnergy: [1000, 1200]},
        {beamline.ExitSlit.totalHeight: [0.1]},
        {beamline.PG.cFactor: [2.25]},
    ]
    sim._workers = 2
    sim.repeat = 3

    seed = sim._build_initial_eta_seed()

    assert seed is not None
    assert seed["basis"] == "fixed"
    assert seed["first_round_seconds"] > 0
    assert seed["total_seconds"] == seed["first_round_seconds"] * sim.repeat / sim._workers


def test_round_zero_number_rays_detects_scanned_values():
    sim = Simulate(_RML, hide=True)
    beamline = sim.rml.beamline
    sim.params = [
        {beamline.Dipole.photonEnergy: [1000]},
        {beamline.Dipole.numberRays: [10_000, 500_000]},
    ]

    result = sim._round_zero_number_rays()

    assert result == {"basis": "scanned", "values": [10_000.0, 500_000.0]}


def test_initial_eta_seed_unsupported_engine_returns_none():
    sim = Simulate(_RML, hide=True, engine="rayx")
    beamline = sim.rml.beamline
    sim.params = [{beamline.Dipole.photonEnergy: [1000]}]

    assert sim._build_initial_eta_seed() is None


def test_seed_progress_bar_uses_initial_estimate():
    sim = Simulate(_RML, hide=True)
    sim._initial_eta_seed = {
        "basis": "fixed",
        "first_round_seconds": 12.0,
        "total_seconds": 24.0,
    }
    pbar = _DummyPbar()

    sim._seed_progress_bar_eta(pbar)

    assert pbar.postfix == "ETA~: 24s"


def test_update_progress_bar_replaces_seed_with_measured_timings():
    sim = Simulate(_RML, hide=True)
    sim._workers = 2
    sim._simulations_duration_total = 8.0
    pbar = _DummyPbar(total=5)
    pbar.postfix = "ETA~: 24s"

    sim._update_progress_bar([8.0], pbar)

    assert "Last: 8.00s" in pbar.postfix
    assert "Avg: 8.00s/it" in pbar.postfix
    assert pbar.n == 1


def test_number_rays_estimate_uses_conservative_safety_factor():
    sim = Simulate(_RML, hide=True)

    estimate = sim._estimate_seconds_from_number_rays(10_000)

    assert estimate == 10.4
