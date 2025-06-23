###############################################################################
# RayUI process handling and RayUI command API

# from sre_constants import SUCCESS
import atexit
import os
import subprocess
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
        self._options = "-b" if background else ""
        self._process = None
        self._verbose = False
        if hide:
            self._hide = "xvfb-run --auto-servernum --server-num=3000 "
        else:
            self._hide = ""

        # internal configuration parameters
        self._auto_flush = True  # flush on write calls

    def run(self):
        """Open one instance of RAY-UI using subprocess

        Raises:
            RayPyRunnerError: if the RAY-UI executable is not found raise an error

        """
        if not self.isrunning:
            fullpath = os.path.join(self._path, self._binary)
            if not os.path.isfile(fullpath):
                raise RayPyRunnerError("Ray executable {0} is not found".format(fullpath))
            fullpath = self._hide + fullpath
            env = dict(os.environ)  # TODO:: rethink a bit about this line
            self._process = subprocess.Popen(
                fullpath + " -b",
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
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
            poll_result = self._process.poll()
            if poll_result is not None:
                # we have an exit code, so process is not valid any more and clean it it up
                self._process = None
                return False
            else:
                return True

    def kill(self):
        """kill a RAY-UI process"""
        if self.isrunning:
            pid = self._process.pid
            process = psutil.Process(pid)
            for proc in process.children(recursive=True):
                proc.kill()
            process.kill()

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
        if self.isrunning:
            line = self._process.stdout.readline().decode("utf8").rstrip("\n")
            if self._verbose:  # verbose
                print(line)
            return line
        else:
            return None

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
            line = self._runner._readline()
            if line is None:
                time.sleep(self._read_wait_delay)
                timecnt += self._read_wait_delay
                continue
            if line.startswith(cmd):
                if cmd_seen:
                    break
                else:
                    cmd_seen = True
            else:
                if cbdataread is not None:
                    cbdataread(line)
            if timeout is not None and timecnt > timeout:
                raise TimeoutError("timeout while waiting ray command io")
        return line.lstrip(cmd).strip()
