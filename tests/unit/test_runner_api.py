from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from raypyng import config
from raypyng.errors import RayPyError
from raypyng.runner import RayUIAPI
from raypyng.runner import RayUIRunner


class FakeRunner:
    def __init__(self, lines=(), payload=b""):
        self.isrunning = True
        self.lines = iter(lines)
        self.payload = payload
        self.writes = []
        self._process = SimpleNamespace(
            stdin=SimpleNamespace(write=self._write_bytes, flush=lambda: None)
        )
        self._auto_flush = True

    def _write(self, cmd):
        self.writes.append(cmd)

    def _write_bytes(self, payload):
        self.writes.append(payload)

    def _readline_with_timeout(self, timeout=None):
        return next(self.lines, None)

    def _readexactly_with_timeout(self, size, timeout=None):
        data = self.payload[:size]
        self.payload = self.payload[size:]
        return data


def test_runner_accepts_windows_executable_without_x_bit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    exe_path = tmp_path / "rayui.exe"
    exe_path.write_text("", encoding="utf8")

    monkeypatch.setattr(config, "opsys", "Windows")
    monkeypatch.setattr("raypyng.runner.os.access", lambda *_args: False)

    runner = RayUIRunner(ray_path=str(tmp_path), ray_binary="rayui.exe")

    assert runner._full_path == str(exe_path)


def test_runner_detects_windows_install_dir(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "opsys", "Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")
    monkeypatch.setenv("ProgramFiles", r"C:\Program Files")
    monkeypatch.setenv("ProgramFiles(x86)", r"C:\Program Files (x86)")

    existing_dirs = {
        r"C:\Users\tester\AppData\Local\Programs\RAY-UI",
    }
    existing_files = {
        r"C:\Users\tester\AppData\Local\Programs\RAY-UI\rayui.exe",
    }

    monkeypatch.setattr("raypyng.runner.os.path.isdir", lambda path: path in existing_dirs)
    monkeypatch.setattr("raypyng.runner.os.path.isfile", lambda path: path in existing_files)
    monkeypatch.setattr("raypyng.runner.os.access", lambda *_args: True)

    runner = object.__new__(RayUIRunner)
    runner._platform = "Windows"
    runner._binary = "rayui.exe"

    detected = runner._RayUIRunner__detect_ray_path()

    assert detected == r"C:\Users\tester\AppData\Local\Programs\RAY-UI"


def test_runner_windows_hide_sets_hidden_creation_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    exe_path = tmp_path / "rayui.exe"
    exe_path.write_text("", encoding="utf8")

    monkeypatch.setattr(config, "opsys", "Windows")
    monkeypatch.setattr("raypyng.runner.os.access", lambda *_args: True)

    runner = RayUIRunner(ray_path=str(tmp_path), ray_binary="rayui.exe", hide=True)

    assert runner._hide == []
    assert (
        runner._creationflags & subprocess.CREATE_NO_WINDOW
        == subprocess.CREATE_NO_WINDOW
    )
    assert runner._startupinfo is not None


def test_runner_linux_hide_uses_xvfb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    exe_path = tmp_path / "rayui.sh"
    exe_path.write_text("", encoding="utf8")

    monkeypatch.setattr(config, "opsys", "Linux")
    monkeypatch.setattr("raypyng.runner.os.access", lambda *_args: True)
    monkeypatch.setattr("raypyng.runner.shutil.which", lambda name: "/usr/bin/xvfb-run")

    runner = RayUIRunner(ray_path=str(tmp_path), ray_binary="rayui.sh", hide=True)

    assert runner._hide == ["/usr/bin/xvfb-run", "--auto-servernum", "--server-num=3000"]


def test_runner_macos_hide_does_not_wrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    exe_path = tmp_path / "Ray-UI"
    exe_path.write_text("", encoding="utf8")

    monkeypatch.setattr(config, "opsys", "Darwin")
    monkeypatch.setattr("raypyng.runner.os.access", lambda *_args: True)

    runner = RayUIRunner(ray_path=str(tmp_path), ray_binary="Ray-UI", hide=True)

    assert runner._hide == []


def test_runner_readline_and_readexactly_use_shared_buffer():
    runner = object.__new__(RayUIRunner)
    runner._process = SimpleNamespace()
    runner._verbose = False
    runner._stdout_buffer = bytearray(b"trace success\n1234")
    runner._stdout_eof = False
    runner._stdout_condition = __import__("threading").Condition()

    assert runner._readline_with_timeout(timeout=0.01) == "trace success"
    assert runner._readexactly_with_timeout(4, timeout=0.01) == b"1234"


def test_api_export_transcript_with_intermediate_path_succeeds():
    api = RayUIAPI(
        FakeRunner(
            [
                "export",
                "export path: C:\\temp\\raypyng_raw_export_probe",
                "export success",
            ]
        )
    )

    assert api.export("Dipole", "RawRaysOutgoing", r"C:\temp\out", "single_") is True


def test_api_export_failed_reply_returns_false():
    api = RayUIAPI(FakeRunner(["export", "export failed (path does not exist)"]))

    assert api.export("Dipole", "RawRaysOutgoing", r"C:\temp\out", "single_") is False


def test_api_trace_preserves_elapsed_lines_and_marks_simulation_done():
    seen = []
    api = RayUIAPI(FakeRunner(["trace", "elapsedMs=120,elapsed=00s", "trace success"]))

    assert api.trace(analyze=False, cbNewLine=seen.append) is True
    assert seen == ["elapsedMs=120,elapsed=00s"]
    assert api._simulation_done is True


def test_api_results_parses_multi_line_success():
    api = RayUIAPI(FakeRunner(["results", "value=1,unit=mm", "results success"]))

    assert api.results("Detector") == ["value=1", "unit=mm"]


def test_api_loadstream_writes_command_and_bytes():
    runner = FakeRunner(["loadstream", "loadstream success"])
    api = RayUIAPI(runner)

    assert api.loadstream("<xml />", base_path=r"C:\tmp\base") is True
    assert runner.writes[0] == 'loadstream 7 --base "C:\\\\tmp\\\\base"'
    assert runner.writes[1] == b"<xml />"


def test_api_rawdata_reads_binary_payload():
    payload = b"0123456789"
    api = RayUIAPI(FakeRunner(["rawdata", "rawdata success", "10"], payload=payload))

    assert api.rawdata("Detector", "RawRaysOutgoing") == payload


def test_api_single_reply_commands_quote_paths_and_values():
    runner = FakeRunner(["getconfig", "foo"])
    api = RayUIAPI(runner)

    assert api.getconfig("key with space") == "foo"
    assert runner.writes[0] == 'getconfig "key with space"'


def test_api_export_command_quotes_all_arguments():
    runner = FakeRunner(["export", "export success"])
    api = RayUIAPI(runner)

    api.export("Dipole,DetectorAtFocus", "RawRaysOutgoing", r"C:\temp dir\out", "0 prefix")

    assert (
        runner.writes[0]
        == 'export "Dipole,DetectorAtFocus" "RawRaysOutgoing" "C:\\\\temp dir\\\\out" "0 prefix"'
    )


def test_api_getparam_failed_reply_raises():
    api = RayUIAPI(FakeRunner(["getparam", "getparam failed: missing value"]))

    with pytest.raises(RayPyError, match="getparam"):
        api.getparam("Dipole", "photonEnergy")
