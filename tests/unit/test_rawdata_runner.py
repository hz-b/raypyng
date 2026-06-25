"""Unit tests for RayUIRunner._read_bytes and RayUIAPI.rawdata.

No RAY-UI installation needed — RayUIRunner is mocked via a fake subprocess
and a pre-populated _stdout_buffer.
"""

import io
import struct
import types
import unittest.mock as mock

import numpy as np
import pytest

from raypyng.errors import RayPyError
from raypyng.runner import RayUIAPI, RayUIRunner


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_npy_blob(n_rows=5):
    """Build a minimal .npy blob with the rawdata structured dtype."""
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
    arr = np.zeros(n_rows, dtype=dtype)
    arr["OX"] = np.arange(n_rows, dtype=float)
    arr["EN"] = 100.0
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue(), arr


def _make_runner_with_buffer(data: bytes) -> RayUIRunner:
    """Return a RayUIRunner whose _stdout_buffer is pre-filled with data
    and whose subprocess is mocked to look alive."""
    runner = object.__new__(RayUIRunner)
    runner._stdout_buffer = bytearray(data)
    runner._verbose = False

    fake_proc = mock.MagicMock()
    fake_proc.poll.return_value = None
    fake_proc.stdout.fileno.return_value = -1
    runner._process = fake_proc

    return runner


# ── _read_bytes ───────────────────────────────────────────────────────────────


def test_read_bytes_exact_from_buffer():
    """_read_bytes reads exactly n bytes from a pre-filled buffer."""
    payload = b"hello world"
    runner = _make_runner_with_buffer(payload)
    result = runner._read_bytes(len(payload))
    assert result == payload
    assert len(runner._stdout_buffer) == 0


def test_read_bytes_partial_leaves_rest():
    """_read_bytes consumes only the requested n bytes."""
    payload = b"ABCDEFGHIJ"
    runner = _make_runner_with_buffer(payload)
    result = runner._read_bytes(4)
    assert result == b"ABCD"
    assert bytes(runner._stdout_buffer) == b"EFGHIJ"


def test_read_bytes_returns_none_when_process_dead():
    """_read_bytes returns None immediately if the process is not running."""
    runner = object.__new__(RayUIRunner)
    runner._stdout_buffer = bytearray(b"")
    runner._process = None
    result = runner._read_bytes(10)
    assert result is None


def test_read_bytes_timeout_with_empty_buffer(monkeypatch):
    """_read_bytes returns None on timeout when no data arrives."""
    import select as sel

    runner = _make_runner_with_buffer(b"")

    monkeypatch.setattr(sel, "select", lambda *a, **kw: ([], [], []))

    result = runner._read_bytes(10, timeout=0.0)
    assert result is None


# ── RayUIAPI.rawdata ──────────────────────────────────────────────────────────


class _FakeRunner:
    """Minimal stand-in for RayUIRunner that plays back a scripted stdout."""

    def __init__(self, lines: list[str], binary: bytes = b""):
        self._lines = list(lines)
        self._binary = binary
        self._written = []
        self._stdout_buffer = bytearray()
        self.isrunning = True

    def _write(self, text, endline="\n"):
        self._written.append(text)

    def _readline(self):
        if self._lines:
            return self._lines.pop(0)
        return None

    def _readline_with_timeout(self, timeout=None):
        return self._readline()

    def _read_bytes(self, n, timeout=None):
        if len(self._binary) < n:
            return None
        result = self._binary[:n]
        self._binary = self._binary[n:]
        return result


def _make_api_with_rawdata_response(n_rows=3):
    """Build a RayUIAPI backed by a fake runner returning a rawdata reply."""
    npy_blob, expected_arr = _make_npy_blob(n_rows)
    lines = [
        "rawdata",
        "rawdata success",
        str(len(npy_blob)),
    ]
    fake_runner = _FakeRunner(lines, binary=npy_blob)
    api = object.__new__(RayUIAPI)
    api._runner = fake_runner
    api._read_wait_delay = 0.01
    api._quit_timeout = 5
    api._simulation_done = False
    return api, expected_arr


def test_rawdata_returns_structured_array():
    """rawdata() returns a structured numpy array with the correct dtype fields."""
    api, expected = _make_api_with_rawdata_response(n_rows=10)
    result = api.rawdata("Toroid", "RawRaysOutgoing")
    assert result.dtype.names == expected.dtype.names
    np.testing.assert_array_equal(result["OX"], expected["OX"])
    np.testing.assert_array_equal(result["EN"], expected["EN"])


def test_rawdata_correct_shape():
    """rawdata() returns an array with the expected number of rows."""
    n = 7
    api, _ = _make_api_with_rawdata_response(n_rows=n)
    result = api.rawdata("Mirror", "RawRaysIncoming")
    assert result.shape == (n,)


def test_rawdata_raises_on_failure():
    """rawdata() raises RayPyError when RAY-UI replies with 'rawdata failed'."""
    lines = ["rawdata", "rawdata failed"]
    fake_runner = _FakeRunner(lines, binary=b"")
    api = object.__new__(RayUIAPI)
    api._runner = fake_runner
    api._read_wait_delay = 0.01
    api._quit_timeout = 5
    api._simulation_done = False

    with pytest.raises(RayPyError):
        api.rawdata("BadElement", "RawRaysOutgoing")


def test_rawdata_raises_when_no_byte_count():
    """rawdata() raises RayPyError when the byte-count line is missing."""
    lines = ["rawdata", "rawdata success"]
    fake_runner = _FakeRunner(lines, binary=b"")
    api = object.__new__(RayUIAPI)
    api._runner = fake_runner
    api._read_wait_delay = 0.01
    api._quit_timeout = 5
    api._simulation_done = False

    with pytest.raises(RayPyError):
        api.rawdata("Element", "RawRaysOutgoing")


def test_rawdata_raises_when_binary_truncated():
    """rawdata() raises RayPyError when the binary blob is shorter than promised."""
    npy_blob, _ = _make_npy_blob(3)
    lines = ["rawdata", "rawdata success", str(len(npy_blob))]
    # Only provide half the binary data
    fake_runner = _FakeRunner(lines, binary=npy_blob[: len(npy_blob) // 2])
    api = object.__new__(RayUIAPI)
    api._runner = fake_runner
    api._read_wait_delay = 0.01
    api._quit_timeout = 5
    api._simulation_done = False

    with pytest.raises(RayPyError):
        api.rawdata("Element", "RawRaysOutgoing")


def test_rawdata_fails_fast_when_command_unsupported():
    """A RAY-UI build without 'rawdata' answers nothing; rawdata() must raise
    promptly (wrapping the timeout) instead of hanging forever."""
    import time

    # No scripted lines at all -> _readline_with_timeout always returns None,
    # mimicking a binary that silently ignores the unknown command.
    fake_runner = _FakeRunner([], binary=b"")
    api = object.__new__(RayUIAPI)
    api._runner = fake_runner
    api._read_wait_delay = 0.001
    api._quit_timeout = 5
    api._simulation_done = False

    start = time.monotonic()
    with pytest.raises(RayPyError, match="does not support"):
        api.rawdata("Element", "RawRaysOutgoing", timeout=0.1)
    elapsed = time.monotonic() - start
    # Must fail fast, not hang: well under a second for a 0.1s timeout.
    assert elapsed < 5.0
