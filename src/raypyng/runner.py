###############################################################################
# RayUI process handling and RayUI command API

import atexit
import ctypes
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

import psutil

from . import config
from .errors import RayPyError, RayPyRunnerError, TimeoutError

# import sys # used for some debugging


###############################################################################
class RayUIRunner:
    """RayUIRunner class implements all logic to start a RayUI process,
    load and rml file, trace and export.

    Args:
            ray_path (str, optional): the path to the RAY-UI installation folder.
                                      Defaults to config.ray_path, that will look for the
                                      ray_path in the standard installation folders.
            ray_binary (_type_, optional): the binary file of RAY-UI.
                                            Defaults to "rayui.sh".
            background (bool, optional): activate background mode. Defaults to True.
            hide (bool, optional): Hide the RAY-UI graphical instances.
                                   Available only if xvfb is installed.
                                   Defaults to False.
    """

    def __init__(
        self,
        ray_path=config.ray_path,
        ray_binary=config.ray_binary,
        background=True,
        hide=False,
    ) -> None:
        """
        Args:
            ray_path (str, optional): the path to the RAY-UI installation folder.
                                      Defaults to config.ray_path, that will look for the
                                      ray_path in the standard installation folders.
            ray_binary (_type_, optional): the binary file of RAY-UI.
                                            Defaults to "rayui.sh".
            background (bool, optional): activate background mode. Defaults to True.
            hide (bool, optional): Hide the RAY-UI graphical instances.
                                   Available only if xvfb is installed.
                                   Defaults to False.

        Raises:
            Exception: _description_
        """
        self._platform = config.opsys
        self._binary = ray_binary
        if ray_path is None:
            ray_path = self.__detect_ray_path()
        if ray_path is None:
            raise Exception("ray_path must be defined for now!")

        self._path = ray_path
        self._full_path = self._resolve_executable_path(self._path, self._binary)
        if not os.path.isfile(self._full_path):
            raise FileNotFoundError(f"{self._full_path} does not exist.")
        elif self._platform != "Windows" and not os.access(self._full_path, os.X_OK):
            raise PermissionError(
                f"{self._full_path} exists but is NOT executable.\n"
                f"To make it executable, run:\n\n"
                f'    chmod +x "{self._full_path}"\n'
            )

        self._options = ["-b"] if background else []
        self._process = None
        self._verbose = False
        self._reader_thread = None
        self._stdout_buffer = bytearray()
        self._stdout_eof = False
        self._stdout_condition = threading.Condition()
        self._creationflags = 0
        self._startupinfo = None
        self._hide = []
        if hide and self._platform == "Linux":
            # xvfb-run is Linux-only; on macOS the app runs headlessly via -b alone
            xvfb = shutil.which("xvfb-run")
            if xvfb is None:
                raise RayPyRunnerError(
                    "hide=True requires xvfb-run on Linux, but it was not found in PATH.\n"
                    "Install it with:  sudo apt-get install xvfb\n"
                    "Then retry, or pass hide=False to run with a visible window."
                )
            self._hide = [xvfb, "--auto-servernum", "--server-num=3000"]
        elif hide and self._platform == "Windows":
            self._startupinfo = subprocess.STARTUPINFO()
            self._startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._startupinfo.wShowWindow = subprocess.SW_HIDE
            self._creationflags |= subprocess.CREATE_NO_WINDOW

        # internal configuration parameters
        self._auto_flush = True  # flush on write calls

    def run(self):
        """Open one instance of RAY-UI using subprocess

        Raises:
            RayPyRunnerError: if the RAY-UI executable is not found raise an error

        """
        if not self.isrunning:
            if not os.path.isfile(self._full_path):
                raise RayPyRunnerError("Ray executable {0} is not found".format(self._full_path))
            cmd = [*self._hide, self._full_path, *self._options]
            env = dict(os.environ)  # TODO:: rethink a bit about this line
            popen_kwargs = dict(
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            if self._platform == "Windows":
                popen_kwargs["creationflags"] = self._creationflags
                if self._startupinfo is not None:
                    popen_kwargs["startupinfo"] = self._startupinfo
            else:
                popen_kwargs["start_new_session"] = True
            self._process = subprocess.Popen(
                cmd,
                **popen_kwargs,
            )
            self._reset_stdout_queue()
            self._reader_thread = threading.Thread(
                target=self._pump_stdout,
                name="rayui-stdout",
                daemon=True,
            )
            self._reader_thread.start()
            atexit.register(self.kill)
        return self

    @property
    def isrunning(self):
        """Check weather a process is running and rerutn a boolean

        Returns:
            bool: returns True if the process is running, otherwise False
        """
        if self._process is None:
            return False
        else:
            return self._process.poll() is None

    def kill(self):
        """kill a RAY-UI process"""
        if self._process is None:
            return

        if self.isrunning:
            pid = self._process.pid
            if self._platform == "Windows":
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        process = psutil.Process(pid)
                        for proc in process.children(recursive=True):
                            proc.kill()
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass
            else:
                # macOS GUI apps need more time to shut down; SIGKILL triggers crash dialogs.
                # On macOS we only send SIGTERM and skip the SIGKILL escalation.
                sigterm_timeout = 30 if sys.platform == "darwin" else 5
                try:
                    os.killpg(pid, signal.SIGTERM)
                    self._process.wait(timeout=sigterm_timeout)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    if sys.platform != "darwin":
                        try:
                            process = psutil.Process(pid)
                            for proc in process.children(recursive=True):
                                proc.kill()
                            process.kill()
                        except psutil.NoSuchProcess:
                            pass
                        try:
                            os.killpg(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass

        self._close_pipes()
        self._process = None

    @property
    def pid(self):
        """Get process id of the RayUI process

        Returns:
            int: PID of the process if it running, None otherwise
        """
        if self.isrunning:
            return self._process.pid
        else:
            return None

    def _write(self, instr: str, endline="\n"):
        """Write command to RayUI interface

        Args:
            instr (str): _description_
            endline (str, optional): _description_. Defaults to endline character.

        Raises:
            RayPyRunnerError: _description_
        """
        if self.isrunning:
            payload = bytes(instr + endline, "utf8")
            self._process.stdin.write(payload)
            if self._auto_flush:
                self._process.stdin.flush()
        else:
            raise RayPyRunnerError("RayUI process is not started")

    def _readline(self) -> str:
        """Read a line from the stdout of the process and convert to a string

        Returns:
            str: line read from the input
        """
        return self._readline_with_timeout(timeout=None)

    def _readline_with_timeout(self, timeout=None) -> str:
        """Read one line from stdout, optionally timing out if no new line arrives."""
        if self._process is None:
            return None
        return self._read_stdout_line(timeout=timeout)

    def _readexactly_with_timeout(self, size: int, timeout=None) -> bytes | None:
        """Read an exact number of bytes from stdout, optionally timing out."""
        if self._process is None:
            return None
        return self._read_stdout_bytes(size, timeout=timeout)

    def _close_pipes(self):
        for stream_name in ("stdin", "stdout", "stderr"):
            stream = getattr(self._process, stream_name, None)
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=1)
            self._reader_thread = None
        self._reset_stdout_queue()

    def _pump_stdout(self):
        stdout = getattr(self._process, "stdout", None)
        if stdout is None:
            with self._stdout_condition:
                self._stdout_eof = True
                self._stdout_condition.notify_all()
            return

        try:
            while True:
                chunk = stdout.read1(4096) if hasattr(stdout, "read1") else stdout.read(4096)
                if not chunk:
                    break
                with self._stdout_condition:
                    self._stdout_buffer.extend(chunk)
                    self._stdout_condition.notify_all()
        finally:
            with self._stdout_condition:
                self._stdout_eof = True
                self._stdout_condition.notify_all()

    def _reset_stdout_queue(self):
        with self._stdout_condition:
            self._stdout_buffer = bytearray()
            self._stdout_eof = False

    def _read_stdout_line(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._stdout_condition:
            while True:
                newline_idx = self._stdout_buffer.find(b"\n")
                if newline_idx != -1:
                    raw_line = bytes(self._stdout_buffer[:newline_idx])
                    del self._stdout_buffer[: newline_idx + 1]
                    line = raw_line.decode("utf8", errors="replace").rstrip("\r")
                    if self._verbose:
                        print(line)
                    return line
                if self._stdout_eof:
                    if self._stdout_buffer:
                        raw_line = bytes(self._stdout_buffer)
                        self._stdout_buffer.clear()
                        line = raw_line.decode("utf8", errors="replace").rstrip("\r")
                        if self._verbose:
                            print(line)
                        return line
                    return None
                wait_time = None if deadline is None else deadline - time.monotonic()
                if wait_time is not None and wait_time <= 0:
                    return None
                self._stdout_condition.wait(timeout=wait_time)

    def _read_stdout_bytes(self, size: int, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._stdout_condition:
            while True:
                if len(self._stdout_buffer) >= size:
                    data = bytes(self._stdout_buffer[:size])
                    del self._stdout_buffer[:size]
                    return data
                if self._stdout_eof:
                    return None
                wait_time = None if deadline is None else deadline - time.monotonic()
                if wait_time is not None and wait_time <= 0:
                    return None
                self._stdout_condition.wait(timeout=wait_time)

    def _resolve_executable_path(self, ray_path: str, ray_binary: str) -> str:
        for candidate in self._candidate_binaries(ray_binary):
            full_path = os.path.join(ray_path, candidate)
            if os.path.isfile(full_path):
                return full_path
        return os.path.join(ray_path, ray_binary)

    def _candidate_binaries(self, ray_binary: str):
        candidates = [ray_binary]
        if self._platform == "Windows":
            candidates.extend(["rayui.exe", "Ray-UI.exe", "RAY-UI.exe"])
        seen = set()
        unique = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique.append(candidate)
        return unique

    def __detect_ray_path(self) -> str:
        """Internal function to autodetect installation path of RAY-UI

        Raises:
            RayPyRunnerError: is case no RAY-UI installations can be detected

        Returns:
            str: string with the detected RAY-UI installation path
        """
        basepaths = ["~", "~/Applications", "/opt", "/Applications"]
        if self._platform == "Windows":
            windows_basepaths = [
                os.path.expanduser("~"),
                os.path.join(os.path.expanduser("~"), "Applications"),
            ]
            for env_var in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
                base = os.environ.get(env_var)
                if base:
                    windows_basepaths.extend(
                        [
                            base,
                            os.path.join(base, "Programs"),
                        ]
                    )
            basepaths = windows_basepaths
        installpaths = ("RAY-UI-development", "RAY-UI", "Ray-UI")
        pathlist = [
            os.path.expanduser(p)
            for p in [os.path.join(x, y) for x in basepaths for y in installpaths]
        ]
        for ray_path in pathlist:
            if os.path.isdir(ray_path) and os.path.isfile(
                self._resolve_executable_path(ray_path, self._binary)
            ):
                return ray_path
        raise RayPyRunnerError("Can not detect rayui installation path! Please provide it manually")


###############################################################################
class RayUIAPI:
    """RayUIAPI class implements (hopefully all) command interface of the RAY-UI"""

    def __init__(self, runner: RayUIRunner = None) -> None:
        """Optional Reference to an existing RayUIRunner
        Args:
            runner (RayUIRunner, optional): reference to existing runner.
                                            If set to None a new runner instance will
                                            be automaticlly created. Defaults to None.
        """
        if runner is None:
            runner = RayUIRunner().run()
        self._runner = runner
        # if rayui does not send anything to stdio this delay
        # will be used before next attempt to read
        self._read_wait_delay = 0.01
        self._quit_timeout = 300  # default timeout for commands like quit
        self._simulation_done = False

    def quit(self):
        """quit RAY-UI if it is running"""
        if self._runner.isrunning:
            self._runner._write("quit")
            try:
                self._runner._process.wait(self._quit_timeout)
            except subprocess.TimeoutExpired:
                raise TimeoutError("Timeout while trying to quit") from None

    def load(self, rml_path, **kwargs):
        """Load an rml file

        Args:
            rml_path (str): path to the rml file
        """
        self._simulation_done = False
        return self._cmd_io("load", self._quote_arg(rml_path), **kwargs)

    def save(self, rml_path, **kwargs):
        """Save an rml file

        Args:
            rml_path (path): path to save the rml file
        """
        return self._cmd_io("save", self._quote_arg(rml_path), **kwargs)

    def trace(self, analyze=True, **kwargs):
        """Trace an rml file (must have been loaded before).

        Args:
            analyze (bool, optional): If True RAY-UI will perform analysis of the rays.
                                      Defaults to True.

        """
        return self._cmd_io("trace", None if analyze else "noanalyze", **kwargs)

    def loadstream(self, rml_content, base_path=None, **kwargs):
        if isinstance(rml_content, str):
            rml_bytes = rml_content.encode("utf8")
        else:
            rml_bytes = bytes(rml_content)
        parts = ["loadstream", str(len(rml_bytes))]
        if base_path is not None:
            parts.extend(["--base", self._quote_arg(base_path)])
        self._runner._write(" ".join(parts))
        if self._runner.isrunning:
            self._runner._process.stdin.write(rml_bytes)
            if self._runner._auto_flush:
                self._runner._process.stdin.flush()
        response = self._wait_for_cmd_io("loadstream", cbdataread=kwargs.get("cbNewLine"))
        return response["status"] == "success"

    def beamline_elements(self, **kwargs):
        line = self._read_single_reply_line("beamline", "elements")
        self._raise_on_failed_reply("beamline", line)
        return self._split_csv_line(line)

    def beamline_parameters(self, element, **kwargs):
        payload = "parameters " + self._quote_arg(element)
        line = self._read_single_reply_line("beamline", payload)
        self._raise_on_failed_reply("beamline", line)
        return self._split_csv_line(line)

    def getparam(self, element, parameter, **kwargs):
        payload = f"{self._quote_arg(element)} {self._quote_arg(parameter)}"
        line = self._read_single_reply_line("getparam", payload)
        self._raise_on_failed_reply("getparam", line)
        return self._split_csv_line(line)

    def setparam(self, element, parameter, value, **kwargs):
        payload = " ".join(
            [
                self._quote_arg(element),
                self._quote_arg(parameter),
                self._quote_arg(value),
            ]
        )
        line = self._read_single_reply_line("setparam", payload)
        self._raise_on_failed_reply("setparam", line)
        return self._split_csv_line(line)

    def results(self, element, **kwargs):
        response = self._cmd_collect("results", self._quote_arg(element), **kwargs)
        return self._split_csv_line(response["lines"][0] if response["lines"] else "")

    def rawdata(self, element, dataset, **kwargs):
        payload = f"{self._quote_arg(element)} {self._quote_arg(dataset)}"
        payload_size = self._read_rawdata_size_line(payload)
        payload_bytes = self._runner._readexactly_with_timeout(payload_size, timeout=None)
        if payload_bytes is None or len(payload_bytes) != payload_size:
            raise TimeoutError("timeout while waiting rawdata payload")
        return payload_bytes

    def getconfig(self, key, **kwargs):
        data = self._read_single_reply_line("getconfig", self._quote_arg(key))
        self._raise_on_failed_reply("getconfig", data)
        if key == "*":
            return self._split_csv_line(data)
        return data

    def setconfig(self, key, value, **kwargs):
        payload = f"{self._quote_arg(key)} {self._quote_arg(value)}"
        response = self._read_command_response("setconfig", payload=payload, **kwargs)
        return response["status"] == "success"

    def looper_validate(self, preset_file, **kwargs):
        return self._looper_cmd("validate", preset_file, **kwargs)

    def looper_load(self, preset_file, **kwargs):
        return self._looper_cmd("load", preset_file, **kwargs)

    def looper_run(self, preset_file, **kwargs):
        return self._looper_cmd("run", preset_file, **kwargs)

    def analyze(self, **kwargs):
        self._runner._write("analyze")
        return True

    def export_items(self, **kwargs):
        line = self._read_single_reply_line("export", "items")
        self._raise_on_failed_reply("export", line)
        return self._split_csv_line(line)

    def export(
        self,
        objects: str,
        parameters: str,
        export_path: str,
        data_prefix: str,
        **kwargs,
    ):
        """Export simulation results from RAY-UI.

        Args:
            objects (str): string with objects list, e.g. "Dipole,DetectorAtFocus"
            parameters (str): stromg with parameters to export,
            e.g. "ScalarBeamProperties,ScalarElementProperties"
            export_path (str): path where to save the data
            data_prefix (str): prefix for the putput files
        """
        payload = " ".join(
            [
                self._quote_arg(objects),
                self._quote_arg(parameters),
                self._quote_arg(self._normalize_export_path(export_path)),
                self._quote_arg(data_prefix),
            ]
        )
        return self._cmd_io("export", payload, **kwargs)

    def codata(self, enabled: bool, **kwargs):
        value = "true" if enabled else "false"
        self._runner._write(f"codata {value}")
        return True

    def _cmd_io(self, cmd: str, payload: str = None, /, cbNewLine=None):
        """The _cmd_io is an internal method which helps to execute a RAY-UI command.
        All commands are run in the following way:
        1. A command is sent to RAY-UI
        2. If Ray-UI acknowleges the command it prints it back
        3. Some extra output can happen (depending on the command)
        4. RAY-UI  writes info "success" or "failed"

        Args:
            cmd (str): string with command (e.g. "load" or "trace")
            payload (str, optional): possible payload for the command (e.g. rml
                                    file path for the load command). Defaults to None.
        Raises:
            RayPyError: in case of an unsupported reply

        Returns:
            bool: True on success, False on RAY-UI side error
        """
        if cmd == "load":
            self._simulation_done = False
        response = self._read_command_response(cmd, payload=payload, cbNewLine=cbNewLine)
        status = response["status"]
        if status == "success":
            if cmd == "trace":
                self._simulation_done = True
            return True
        elif status == "failed":
            return False
        elif (
            status == "ed failed"
        ):  # specical workaround case for the "loaded failed" reply to laod command
            return False
        else:
            raise RayPyError("Got unsupported reply from ray while waiting for command IO")

    def _cmd_collect(self, cmd: str, payload: str = None, /, cbNewLine=None):
        response = self._read_command_response(cmd, payload=payload, cbNewLine=cbNewLine)
        if response["status"] != "success":
            raise RayPyError(
                f"RAY-UI command '{cmd}' failed: " + (response["terminal"] or "unknown failure")
            )
        return response

    def _looper_cmd(self, subcommand, preset_file, **kwargs):
        payload = f"{subcommand} {self._quote_arg(preset_file)}"
        return self._cmd_collect("looper", payload, **kwargs)

    def _read_single_reply_line(self, cmd, payload=None, timeout=None):
        if payload is None:
            cmdstr = cmd
        else:
            cmdstr = f"{cmd} {payload}".rstrip()
        self._runner._write(cmdstr)
        return self._wait_for_single_reply_line(cmd, timeout=timeout)

    def _read_rawdata_size_line(self, payload, timeout=None):
        self._runner._write(f"rawdata {payload}")
        timecnt = 0.0
        cmd_seen = False
        while True:
            poll_timeout = self._read_wait_delay if timeout is not None else None
            line = self._runner._readline_with_timeout(timeout=poll_timeout)
            if line is None:
                if timeout is None:
                    continue
                timecnt += self._read_wait_delay
                if timecnt > timeout:
                    raise TimeoutError("timeout while waiting ray command io")
                continue
            if not cmd_seen:
                if line == "rawdata":
                    cmd_seen = True
                continue
            if line == "rawdata success":
                size_line = self._runner._readline_with_timeout(timeout=poll_timeout)
                if size_line is None:
                    raise TimeoutError("timeout while waiting rawdata payload size")
                try:
                    return int(size_line)
                except ValueError as exc:
                    raise RayPyError(f"rawdata reported invalid payload size: {size_line}") from exc
            if line.startswith("rawdata failed"):
                raise RayPyError(f"RAY-UI command 'rawdata' failed: {line}")

    def _read_command_response(self, cmd, payload=None, cbNewLine=None, timeout=None):
        if payload is None:
            cmdstr = cmd
        else:
            cmdstr = f"{cmd} {payload}".rstrip()
        self._runner._write(cmdstr)
        return self._wait_for_cmd_io(cmd, timeout=timeout, cbdataread=cbNewLine)

    def _wait_for_single_reply_line(self, cmd, timeout=None):
        timecnt = 0.0
        cmd_seen = False
        while True:
            poll_timeout = self._read_wait_delay if timeout is not None else None
            line = self._runner._readline_with_timeout(timeout=poll_timeout)
            if line is None:
                if timeout is None:
                    continue
                timecnt += self._read_wait_delay
                if timecnt > timeout:
                    raise TimeoutError("timeout while waiting ray command io")
                continue
            if not cmd_seen:
                if line == cmd:
                    cmd_seen = True
                continue
            return line

    def _wait_for_cmd_io(self, cmd, timeout=None, cbdataread=None):
        timecnt = 0.0
        cmd_seen = False
        lines = []
        while True:
            poll_timeout = self._read_wait_delay if timeout is not None else None
            line = self._runner._readline_with_timeout(timeout=poll_timeout)
            if line is None:
                if timeout is None:
                    continue
                timecnt += self._read_wait_delay
                if timecnt > timeout:
                    raise TimeoutError("timeout while waiting ray command io")
                continue
            if not cmd_seen:
                if line == cmd:
                    cmd_seen = True
                    continue
                if cbdataread is not None:
                    cbdataread(line)
                continue
            status = self._parse_status_line(cmd, line)
            if status is not None:
                return {
                    "status": status,
                    "terminal": line,
                    "lines": lines,
                }
            lines.append(line)
            if cbdataread is not None:
                cbdataread(line)

    @staticmethod
    def _quote_arg(value):
        text = str(value)
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _normalize_export_path(self, export_path):
        path = str(export_path)
        if getattr(self._runner, "_platform", config.opsys) != "Windows" or " " not in path:
            return path
        short_path = self._windows_short_path(path)
        return short_path or path

    @staticmethod
    def _split_csv_line(line):
        if not line:
            return []
        return [entry.strip() for entry in line.split(",") if entry.strip()]

    @staticmethod
    def _parse_status_line(cmd, line):
        if line == f"{cmd} success":
            return "success"
        if line == f"{cmd} failed" or line.startswith(f"{cmd} failed"):
            return "failed"
        if cmd == "load" and line == "loaded failed":
            return "failed"
        return None

    @staticmethod
    def _raise_on_failed_reply(cmd, line):
        if line is not None and line.startswith(f"{cmd} failed"):
            raise RayPyError(f"RAY-UI command '{cmd}' failed: {line}")

    @staticmethod
    def _windows_short_path(path):
        if os.name != "nt":
            return None
        buffer_len = 260
        while True:
            buffer = ctypes.create_unicode_buffer(buffer_len)
            result = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, buffer_len)
            if result == 0:
                return None
            if result < buffer_len:
                return buffer.value
            buffer_len = result + 1
