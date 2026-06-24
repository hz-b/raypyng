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


def test_collect_missing_simulations_returns_structured_result(monkeypatch):
    sim = Simulate(_RML, hide=True)
    sim.repeat = 2
    sim.logger = types.SimpleNamespace(info=lambda *args, **kwargs: None)

    class DummyProgress:
        def __init__(self):
            self.updates = 0
            self.postfix = []

        def set_postfix_str(self, value, refresh=True):
            self.postfix.append(value)

        def update(self, amount):
            self.updates += amount

        def close(self):
            pass

    progress = DummyProgress()
    monkeypatch.setattr(sim, "_initialize_progress_bar", lambda total, description: progress)
    monkeypatch.setattr(
        sim,
        "_scan_round_outputs",
        lambda round_number: {
            "round": round_number,
            "expected_count": 4,
            "missing_ids": [round_number + 1],
            "missing_by_export_suffix": {"_Detector-RawRaysOutgoing.csv": [round_number + 1]},
        },
    )

    result = sim._collect_missing_simulations()

    assert result["missing_count"] == 2
    assert result["missing_by_round"] == {0: [1], 1: [2]}
    assert result["missing_simulations"] == [
        {"round": 0, "sim_number": 1},
        {"round": 1, "sim_number": 2},
    ]
    assert progress.updates == 2
    assert progress.postfix[-1] == "Missing so far: 2"


def test_missing_outputs_raise_after_retry():
    sim = Simulate(_RML, hide=True)
    missing = [{"round": 0, "sim_number": 2}, {"round": 0, "sim_number": 3}]

    with pytest.raises(RuntimeError, match="round 0 sim 2, round 0 sim 3"):
        raise RuntimeError(sim._format_missing_simulations_error(missing))


def test_run_reports_retry_summary(monkeypatch):
    sim = Simulate(_RML, hide=True)
    sim.simulation_name = "test"
    sim.repeat = 1

    messages = []

    monkeypatch.setattr(sim, "_setup_simulation_environment", lambda recipe: None)
    monkeypatch.setattr(sim, "_validate_run_configuration", lambda: None)
    monkeypatch.setattr(sim, "_prepare_simulation_environment", lambda overwrite_rml: None)
    monkeypatch.setattr(sim, "_init_logging", lambda: setattr(sim, "logger", types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None)))
    monkeypatch.setattr(sim, "_status_message", messages.append)
    monkeypatch.setattr(sim, "_print_simulations_info", lambda: None)

    class DummyRunner:
        def __init__(self, *args, **kwargs):
            pass

        def kill(self):
            pass

    monkeypatch.setattr(simulate_module, "RayUIRunner", DummyRunner)

    collect_calls = iter(
        [
            {
                "missing_count": 2,
                "missing_simulations": [{"round": 0, "sim_number": 1}, {"round": 0, "sim_number": 2}],
                "missing_by_round": {0: [1, 2]},
                "missing_by_export_suffix": {},
            },
            {
                "missing_count": 0,
                "missing_simulations": [],
                "missing_by_round": {0: []},
                "missing_by_export_suffix": {},
            },
        ]
    )
    monkeypatch.setattr(sim, "_collect_missing_simulations", lambda description="": next(collect_calls))

    execute_calls = []

    def fake_execute(*args, **kwargs):
        execute_calls.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(sim, "_execute_simulations", fake_execute)

    class DummyProgress:
        def close(self):
            pass

    monkeypatch.setattr(sim, "_initialize_progress_bar", lambda total, description="": DummyProgress())
    monkeypatch.setattr(sim.sp, "_calc_number_sim", lambda: 3)

    sim.run(force=True)

    assert any("Final check found 2 missing simulations; retrying 2 now." == msg for msg in messages)
    assert any("Retry completed; 0 missing simulations remain." == msg for msg in messages)
    assert len(execute_calls) == 2
    assert execute_calls[1]["kwargs"]["selected_simulations_by_round"] == {0: [1, 2]}


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
