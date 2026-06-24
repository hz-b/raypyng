from __future__ import annotations

import types
from pathlib import Path

import pytest

import raypyng.simulate as simulate_module
from raypyng.beamwaist import PlotBeamwaist
from raypyng.simulate import Simulate, run_rml_func, run_rml_func_rayx

_RML = str(Path(__file__).parent.parent / "rml" / "dipole.rml")


def _fake_virtual_memory(available_gb: int):
    return types.SimpleNamespace(available=available_gb * (1024**3))


def test_resolve_workers_explicit(monkeypatch):
    sim = Simulate(_RML, hide=True)
    monkeypatch.setattr(simulate_module.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(simulate_module.psutil, "virtual_memory", lambda: _fake_virtual_memory(32))

    info = sim._resolve_multiprocessing_workers(1)

    assert info["workers"] == 1
    assert "multiprocessing=1 -> 1 worker(s)" in sim._format_worker_resolution_message(info)


def test_resolve_workers_auto(monkeypatch):
    sim = Simulate(_RML, hide=True)
    monkeypatch.setattr(simulate_module.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(simulate_module.psutil, "virtual_memory", lambda: _fake_virtual_memory(6))

    info = sim._resolve_multiprocessing_workers("auto")

    assert info["workers"] == 4
    message = sim._format_worker_resolution_message(info)
    assert "multiprocessing=auto -> 4 worker(s)" in message
    assert "cpu_count=8" in message
    assert "available_ram_gb=6" in message


def test_resolve_workers_max(monkeypatch):
    sim = Simulate(_RML, hide=True)
    monkeypatch.setattr(simulate_module.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(simulate_module.psutil, "virtual_memory", lambda: _fake_virtual_memory(6))

    info = sim._resolve_multiprocessing_workers("max")

    assert info["workers"] == 6
    assert "multiprocessing=max -> 6 worker(s)" in sim._format_worker_resolution_message(info)


def test_run_rml_func_propagates_worker_exceptions(monkeypatch):
    events: list[str] = []

    class DummyRunner:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            events.append("run")

        def kill(self):
            events.append("kill")

    class DummyAPI:
        def __init__(self, runner):
            self.runner = runner

        def load(self, _rml_filename):
            raise RuntimeError("boom")

        def quit(self):
            events.append("quit")

    monkeypatch.setattr(simulate_module, "RayUIRunner", DummyRunner)
    monkeypatch.setattr(simulate_module, "RayUIAPI", DummyAPI)

    parameters = (
        (
            "dummy.rml",
            False,
            False,
            False,
            None,
            False,
            None,
            None,
            False,
            15,
            0.1,
            0.1,
        ),
        [],
    )

    with pytest.raises(RuntimeError, match="boom"):
        run_rml_func(parameters)

    assert events == ["run", "quit", "kill"]


def test_run_rml_func_rayx_propagates_worker_exceptions(monkeypatch):
    import raypyng.rayx_runner as rayx_runner

    class DummyRayXAPI:
        def load(self, _rml_filename):
            raise RuntimeError("rayx boom")

    monkeypatch.setattr(rayx_runner, "_rayui_update_rml", lambda *args, **kwargs: None)
    monkeypatch.setattr(rayx_runner, "RayXAPI", DummyRayXAPI)

    parameters = (
        (
            "dummy.rml",
            False,
            False,
            False,
            None,
            False,
            None,
            None,
            False,
            15,
            0.1,
            0.1,
        ),
        [],
    )

    with pytest.raises(RuntimeError, match="rayx boom"):
        run_rml_func_rayx(parameters)


def test_final_missing_outputs_raise_after_retry():
    sim = Simulate(_RML, hide=True)
    sim.repeat = 1
    sim.simulations_checked = True

    def fake_missing(_round_number):
        return [2, 3]

    sim._missing_simulations_for_round = fake_missing

    with pytest.raises(RuntimeError, match="round 0 sim 2, round 0 sim 3"):
        sim._final_check_on_simulations_and_shutdown(types.SimpleNamespace(close=lambda: None))


def test_beamwaist_preflight_fails_before_spawning_workers(monkeypatch, tmp_path):
    sim = Simulate(_RML, hide=True)
    bw = PlotBeamwaist("Beamwaist", sim)
    bw.directory = str(tmp_path / "RAYPy_Simulation_Beamwaist")
    bw.step_z = 100
    bw.lim = 20
    bw.step = 0.5

    def fake_parse():
        bw.element_names_list = ["Dipole", "M1"]
        bw.distance_list = [0.0, 100.0]
        bw.rotation_list = [False, False]

    monkeypatch.setattr(bw, "_parse_beamline_elements", fake_parse)

    with pytest.raises(FileNotFoundError, match="Missing RawRaysOutgoing export file"):
        bw.trace_beamwaist()
