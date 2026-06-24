###############################################################################
# RayUI process handling and RayUI command API

# from sre_constants import SUCCESS
import atexit
import os
import select
import shutil
import signal
import subprocess
import sys
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
        self, ray_path=config.ray_path, ray_binary=config.ray_binary, background=True, hide=False
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
        if ray_path is None:
            ray_path = self.__detect_ray_path()
        if ray_path is None:
            raise Exception("ray_path must be defined for now!")

        self._path = ray_path
        self._binary = ray_binary

        full_path = os.path.join(self._path, self._binary)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"{full_path} does not exist.")
        elif not os.access(full_path, os.X_OK):
            raise PermissionError(
                f"{full_path} exists but is NOT executable.\n"
                f"To make it executable, run:\n\n"
                f'    chmod +x "{full_path}"\n'
            )

        self._options = "-b" if background else ""
        self._process = None
        self._verbose = False
        if hide and config.opsys != "Darwin":
            # xvfb-run is Linux-only; on macOS the app runs headlessly via -b alone
            xvfb = shutil.which("xvfb-run")
            if xvfb is None:
                raise RayPyRunnerError(
                    "hide=True requires xvfb-run on Linux, but it was not found in PATH.\n"
                    "Install it with:  sudo apt-get install xvfb\n"
                    "Then retry, or pass hide=False to run with a visible window."
                )
            self._hide = [xvfb, "--auto-servernum", "--server-num=3000"]
        else:
            self._hide = []

        # internal configuration parameters
        self._auto_flush = True  # flush on write calls
        self._stdout_buffer = bytearray()

    def run(self):
        """Open one instance of RAY-UI using subprocess

        Raises:
            RayPyRunnerError: if the RAY-UI executable is not found raise an error

        """
        if not self.isrunning:
            fullpath = os.path.join(self._path, self._binary)
            if not os.path.isfile(fullpath):
                raise RayPyRunnerError("Ray executable {0} is not found".format(fullpath))
            cmd = [*self._hide, fullpath]
            if self._options:
                cmd.append(self._options)
            env = dict(os.environ)  # TODO:: rethink a bit about this line
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )
            os.set_blocking(self._process.stdout.fileno(), False)
            self._stdout_buffer.clear()
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
        if not self.isrunning:
            return None

        deadline = None if timeout is None else time.monotonic() + timeout
        stdout_fd = self._process.stdout.fileno()

        while True:
            newline_index = self._stdout_buffer.find(b"\n")
            if newline_index != -1:
                line = self._stdout_buffer[:newline_index]
                del self._stdout_buffer[: newline_index + 1]
                decoded_line = line.decode("utf8", errors="replace").rstrip("\r")
                if self._verbose:
                    print(decoded_line)
                return decoded_line

            if not self.isrunning:
                if self._stdout_buffer:
                    line = self._stdout_buffer.decode("utf8", errors="replace").rstrip("\r")
                    self._stdout_buffer.clear()
                    if self._verbose:
                        print(line)
                    return line
                return None

            wait_time = None
            if deadline is not None:
                wait_time = max(0.0, deadline - time.monotonic())
                if wait_time == 0.0:
                    return None

            readable, _, _ = select.select([stdout_fd], [], [], wait_time)
            if not readable:
                return None

            chunk = os.read(stdout_fd, 4096)
            if not chunk:
                if self._stdout_buffer:
                    line = self._stdout_buffer.decode("utf8", errors="replace").rstrip("\r")
                    self._stdout_buffer.clear()
                    if self._verbose:
                        print(line)
                    return line
                return None
            self._stdout_buffer.extend(chunk)

    def _close_pipes(self):
        for stream_name in ("stdin", "stdout", "stderr"):
            stream = getattr(self._process, stream_name, None)
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass
        self._stdout_buffer.clear()

    def __detect_ray_path(self) -> str:
        """Internal function to autodetect installation path of RAY-UI

        Raises:
            RayPyRunnerError: is case no RAY-UI installations can be detected

        Returns:
            str: string with the detected RAY-UI installation path
        """
        basepaths = ("~", "~/Applications", "/opt", "/Applications")
        installpaths = ("RAY-UI-development", "RAY-UI", "Ray-UI")
        pathlist = [
            os.path.expanduser(p)
            for p in [os.path.join(x, y) for x in basepaths for y in installpaths]
        ]
        for ray_path in pathlist:
            if os.path.isdir(ray_path):
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
        return self._cmd_io("load", rml_path, **kwargs)

    def save(self, rml_path, **kwargs):
        """Save an rml file

        Args:
            rml_path (path): path to save the rml file
        """
        return self._cmd_io("save", rml_path, **kwargs)

    def trace(self, analyze=True, **kwargs):
        """Trace an rml file (must have been loaded before).

        Args:
            analyze (bool, optional): If True RAY-UI will perform analysis of the rays.
                                      Defaults to True.

        """
        return self._cmd_io("trace", None if analyze else "noanalyze", **kwargs)

    def export(self, objects: str, parameters: str, export_path: str, data_prefix: str, **kwargs):
        """Export simulation results from RAY-UI.

        Args:
            objects (str): string with objects list, e.g. "Dipole,DetectorAtFocus"
            parameters (str): stromg with parameters to export,
            e.g. "ScalarBeamProperties,ScalarElementProperties"
            export_path (str): path where to save the data
            data_prefix (str): prefix for the putput files
        """
        payload = '"' + objects + '"' + " " + parameters + " " + export_path + " " + data_prefix
        return self._cmd_io("export", payload, **kwargs)

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
        if payload is None:
            payload = ""
        if cmd == "load":
            self._simulation_done = False
        cmdstr = cmd + " " + payload
        self._runner._write(cmdstr)
        status = self._wait_for_cmd_io(cmd, cbdataread=cbNewLine)
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

    def _wait_for_cmd_io(self, cmd, timeout=None, cbdataread=None):
        timecnt = 0.0
        line = ""
        # we shall see cmd twice - once as ACK for the execution
        # and once as status return
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
            if line.startswith(cmd):
                if cmd_seen:
                    break
                else:
                    cmd_seen = True
            else:
                if cbdataread is not None:
                    cbdataread(line)
        return line.lstrip(cmd).strip()
