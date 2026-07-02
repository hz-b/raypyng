from __future__ import annotations

import multiprocessing
import sys
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace

import pytest

from raypyng.simulate import Simulate

_RML = str(Path(__file__).parent.parent / "rml" / "dipole.rml")


@pytest.fixture
def sim():
    return Simulate(_RML, hide=False)


def test_select_process_pool_context_windows(sim, monkeypatch: pytest.MonkeyPatch):
    expected = object()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        multiprocessing,
        "get_context",
        lambda name: expected if name == "spawn" else None,
    )

    assert sim._select_process_pool_context() is expected


def test_select_process_pool_context_darwin(sim, monkeypatch: pytest.MonkeyPatch):
    expected = object()
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(
        multiprocessing,
        "get_context",
        lambda name: expected if name == "fork" else None,
    )

    assert sim._select_process_pool_context() is expected


def test_select_process_pool_context_linux_uses_default(sim, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "linux")

    assert sim._select_process_pool_context() is None


def test_validate_windows_multiprocessing_runtime_requires_script_file(
    sim, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace())
    monkeypatch.setattr(
        multiprocessing,
        "current_process",
        lambda: SimpleNamespace(name="MainProcess"),
    )

    with pytest.raises(RuntimeError, match="if __name__ == '__main__':"):
        sim._validate_windows_multiprocessing_runtime(2)


def test_validate_windows_multiprocessing_runtime_rejects_worker_reimport(
    sim, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace(__file__="driver.py"))
    monkeypatch.setattr(
        multiprocessing,
        "current_process",
        lambda: SimpleNamespace(name="SpawnProcess-1"),
    )

    with pytest.raises(RuntimeError, match="if __name__ == '__main__':"):
        sim._validate_windows_multiprocessing_runtime(2)


def test_validate_windows_multiprocessing_runtime_allows_single_worker(
    sim, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace())

    sim._validate_windows_multiprocessing_runtime(1)


def test_shutdown_executor_force_cancel_terminates_worker_processes(
    sim, monkeypatch: pytest.MonkeyPatch
):
    sim.logger = SimpleNamespace(info=lambda *args, **kwargs: None)
    sim._executor_has_unfinished_futures = True

    terminated = []

    class FakeWorker:
        def __init__(self, pid):
            self.pid = pid

        def children(self, recursive=True):
            return []

    class FakeProc:
        def __init__(self, pid):
            self.pid = pid

        def is_alive(self):
            return True

        def terminate(self):
            terminated.append(self.pid)

    class FakeExecutor:
        def __init__(self):
            self._processes = {1: FakeProc(101), 2: FakeProc(202)}
            self.shutdown_calls = []

        def shutdown(self, wait, cancel_futures):
            self.shutdown_calls.append((wait, cancel_futures))

    monkeypatch.setattr("raypyng.simulate.psutil.Process", lambda pid: FakeWorker(pid))
    monkeypatch.setattr(sim, "cleanup_child_processes", lambda: terminated.append("cleanup"))

    executor = FakeExecutor()
    sim._shutdown_executor(executor, rerun_missing=False)

    assert 101 in terminated
    assert 202 in terminated
    assert "cleanup" in terminated
    assert executor.shutdown_calls == [(False, True)]


def test_wait_for_simulation_batch_surfaces_worker_exception_without_index_error(
    sim, monkeypatch: pytest.MonkeyPatch
):
    failure = AttributeError("'RayUIRunner' object has no attribute '_hide'")
    future = Future()
    future.set_exception(failure)

    class FakeExecutor:
        def submit(self, func, sim_params):
            return future

    class FakeProgressBar:
        total = 1
        n = 0

        def set_postfix_str(self, *_args, **_kwargs):
            return None

        def update(self, value):
            self.n += value

    sim._engine = "ray-ui"
    sim._batch_number = 0
    sim._simulation_timeout = 20.0
    sim._workers = 2
    sim._simulations_duration_total = 0.0
    sim.logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)

    monkeypatch.setattr(
        "raypyng.simulate.wait",
        lambda pending, timeout, return_when: (set(pending), set()),
    )

    with pytest.raises(AttributeError, match="_hide"):
        sim._wait_for_simulation_batch(
            simulations_durations=[],
            simulation_params_batch=[(("dummy.rml", False, False, False, None, False, None, None, False, 15, 0.1, 0.1), [["Dipole", "RawRaysOutgoing", "round_0", "0"]])],
            executor=FakeExecutor(),
            pbar=FakeProgressBar(),
        )
