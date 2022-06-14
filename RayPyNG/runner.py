# Ray runner

from . import config
from .errors import RayPyRunnerError,RayPyError,TimeoutError
import os
import subprocess
import time

class RayUIRunner:
    """RayUIRunner class implements all logic to start a RayUI process
    """
    def __init__(self,ray_path=config.ray_path,ray_binary=config.ray_binary,background=True) -> None:
        if ray_path is None:
            ray_path = self.__detect_ray_path()
        else:
            raise Exception("ray_path must be defined for now!")
        self._path = ray_path
        self._binary = ray_binary
        self._options = "-b" if background else ""
        self._process = None

        # internal configuration parameters
        self._auto_flush = True     # flush on write calls
        self._cmd_timeout = 0.25    # default timeout for commands like quit

    def run(self):
        fullpath = os.path.join(self._path,self._binary)
        if not os.path.isfile(fullpath):
            raise RayPyRunnerError("Ray executable {0} is not found".format(fullpath))

        env = dict(os.environ) # TODO:: rethink a bit about this line 
        self._process = subprocess.Popen(
                                        fullpath+" -b", 
                                        shell=True, 
                                        stdin=subprocess.PIPE, 
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, 
                                        env=env
                                        )


    @property
    def isrunning(self):
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

    def quit(self):
        """quit rayUI
        """
        if self.isrunning:
            self._write("quit")
            try:
                self._process.wait(self._cmd_timeout)
            except subprocess.TimeoutExpired:
                raise RayPyRunnerError("Timeout while trying to quit")
        

    def _write(self, instr:str, endline="\n"):
        """Write command to RayUI interface

        Args:
            instr (str): _description_
            endline (str, optional): _description_. Defaults to "\n".

        Raises:
            RayPyRunnerError: _description_
        """
        if self.isrunning:
            payload = bytes(instr+endline,"utf8")
            self._process.stdin.write(payload)
            if self._auto_flush:
                self._process.stdin.flush()
        else:
            raise RayPyRunnerError("RayUI process is not started")

    def _readline(self)->str:
        if self.isrunning:
            return self._process.stdout.readline().decode('utf8').rstrip('\n')
        else:
            return None

    def __detect_ray_path(self) -> str:
        """Internal function to autodetect installation path of RayUI

        Raises:
            RayPyRunnerError: is case no ray installations can be detected

        Returns:
            str: string with the detected ray installation path
        """
        basepaths = ("~", "~/Applications","/opt","/Applications")
        installpaths = ("RAY-UI-development","RAY-UI")
        pathlist = [os.path.expanduser(p) for p in [os.path.join(x,y) for x in basepaths for y in installpaths]]

        for ray_path in pathlist:
            if os.path.isdir(ray_path):
                return ray_path
        raise RayPyRunnerError("Can not detect rayui installation path!")
 

 # sketich RayUI API calls
class RayUIAPI:
    def __init__(self,runner:RayUIRunner) -> None:
        if runner is None:
            raise RayPyError("Can not initialize RayUI API wrapper without runner")
        self._runner = runner
        self._read_wait_delay = 0.1

    def load(self,rml_path):
        return self._cmd_io("load",rml_path,status_prefix="loaded")

    def _cmd_io(self,cmd:str,payload:str=None, status_prefix=None):
        """_cmd_io is an internal method which helps to execute a rayui command.
        All commands are run in the following way:
        1. command send to ray
        2. if ray acknowleges the command it prints it back
        3. some extra output can happen (depending on the command)
        4. ray writes info "success" or "failed"

        Args:
            cmd (str): string with command (e.g. "load" or "trace")
            payload (str, optional): possible payload for the command (e.g. rml 
                                    file path for the load command). Defaults to None.
            status_prefix (_type_, optional): Sometimes status reply prefix differs from 
                                    the command. For example load command statuses are "loaded success"
                                    and "loaded failed". So if it is a case it can be addionally 
                                    specified. If set to None then same value is cmd would be used.
                                    Defaults to None.

        Raises:
            RayPyError: in case of an unsupported reply 

        Returns:
            bool: True on success, False ray side error
        """
        if status_prefix is None:
            status_prefix = cmd
        if payload is None:
            payload = ""
        cmdstr = cmd+" "+payload
        self._runner._write(cmdstr)
        self._wait_for_cmd_io(cmd, timeout = 2.0)
        status = self._wait_for_cmd_io(status_prefix)
        if status=="success":
            return True
        elif status=="failed":
            return False
        else:
            raise RayPyError("Got unsupported reply from ray while waiting for command IO")
        
    def _wait_for_cmd_io(self,cmd,timeout=None)->str:
        timecnt = 0.0
        line = ""
        while True:
            line = self._runner._readline()
            if line is None:
                continue
            if (line.startswith(cmd)):
                break
            time.sleep(self._read_wait_delay)
            timecnt+=self._read_wait_delay
            if timeout is not None and timecnt>timeout:
                raise TimeoutError("timeout while waiting ray command io")
        return line.lstrip(cmd).strip()


