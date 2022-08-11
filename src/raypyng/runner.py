###############################################################################
# RayUI process handling and RayUI command API

from sre_constants import SUCCESS
from . import config
from .errors import RayPyRunnerError,RayPyError,TimeoutError
import os
import subprocess,signal
import time
import psutil

###############################################################################
class RayUIRunner:
    """RayUIRunner class implements all logic to start a RayUI process
    """
    def __init__(self,ray_path=config.ray_path,ray_binary=config.ray_binary,background=True,hide=False) -> None:
        if ray_path is None:
            ray_path = self.__detect_ray_path()
        if ray_path is None:
            raise Exception("ray_path must be defined for now!")
        self._path = ray_path
        self._binary = ray_binary
        self._options = "-b" if background else ""
        self._process = None
        if hide:
            self._hide = "xvfb-run --auto-servernum --server-num=1 "
        else: 
            self._hide = ''



        # internal configuration parameters
        self._auto_flush = True     # flush on write calls

    def run(self):
        if not self.isrunning:
            fullpath = os.path.join(self._path,self._binary)
            if not os.path.isfile(fullpath):
                raise RayPyRunnerError("Ray executable {0} is not found".format(fullpath))
            fullpath = self._hide + fullpath
            env = dict(os.environ) # TODO:: rethink a bit about this line 
            self._process = subprocess.Popen(
                                            fullpath+" -b", 
                                            shell=True, 
                                            stdin=subprocess.PIPE, 
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT, 
                                            env=env
                                            )
        return self

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

    def kill(self):
        """kill RayUI process
        """
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
            _type_: PID of the process if it running, None otherwise
        """
        if self.isrunning:
            return self._process.pid
        else:
            return None

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
        """read a line from the stdout of the process and convert to a string

        Returns:
            str: line read from the input
        """
        if self.isrunning:
            line =  self._process.stdout.readline().decode('utf8').rstrip('\n')
            if True: # verbose
                print(line)
            return line
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
 
###############################################################################
class RayUIAPI:
    """RayUIAPI class implements (hopefully all) command interface of the RayUI
    """
    def __init__(self,runner:RayUIRunner=None) -> None:
        """_summary_

        Args:
            runner (RayUIRunner, optional): reference to existing runner. If set to None a new runner instance will be automaticlly created. Defaults to None.
        """
        if runner is None:
            runner = RayUIRunner().run()
        self._runner = runner
        self._read_wait_delay = 0.01    # if rayui does not send anything to stdio this delay will be used before next attempt to read
        self._quit_timeout = 300         # default timeout for commands like quit

    def quit(self):
        """quit rayUI if it is running
        """
        if self._runner.isrunning:
            self._runner._write("quit")
            try:
                self._runner._process.wait(self._quit_timeout)
            except subprocess.TimeoutExpired:
                raise TimeoutError("Timeout while trying to quit")
        
    def load(self,rml_path,**kwargs):
        return self._cmd_io("load",rml_path,**kwargs)

    def trace(self,analyze=True,**kwargs):
        # if analyze:
        #     cmd = "trace"
        # else:
        #     cmd ="trace noanalyze"
        return self._cmd_io("trace",None if analyze else "noanalyze", **kwargs)

    def export(self,objects:str, parameters:str, export_path:str, data_prefix:str, **kwargs):
        """_summary_

        Args:
            objects (str): string with objects list, e.g. "Dipole,DetectorAtFocus"
            parameters (str): stromg with parameters to export, e.g. "ScalarBeamProperties,ScalarElementProperties"
            export_path (str): path where to save the data
            data_prefix (str): prefix for the putput files

        Returns:
            _type_: _description_
        """
        #payload = objects + " " + parameters + " " + export_path + " " + data_prefix
        payload = '"'+objects + '"' + " " + parameters + " " + export_path + " " + data_prefix
        #print("DEBUG:: export payload:",payload)
        return self._cmd_io("export",payload,**kwargs)

    def _cmd_io(self,cmd:str,payload:str=None,/, cbNewLine=None):
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
        Raises:
            RayPyError: in case of an unsupported reply 

        Returns:
            bool: True on success, False ray side error
        """
        if payload is None:
            payload = ""
        cmdstr = cmd+" "+payload
        self._runner._write(cmdstr)
        #self._wait_for_cmd_io(cmd, timeout = 2.0)
        # if cmd == 'trace noanalyze':
        #     status = 'success'
        # else:
        status = self._wait_for_cmd_io(cmd,cbdataread=cbNewLine)
        if status=="success" or 'trace success':
            return True
        elif status=="failed":
            return False
        elif status=="ed failed": # specical workaround case for the "loaded failed" reply to laod command
            return False
        else:
            raise RayPyError("Got unsupported reply from ray while waiting for command IO")
        
    def _wait_for_cmd_io(self,cmd,timeout=None,cbdataread=None):
        timecnt = 0.0
        line = ""
        #cmd = cmd.split(" ")[0]
        while True:
            line = self._runner._readline()
            if line is None:
                time.sleep(self._read_wait_delay)
                timecnt+=self._read_wait_delay
                continue
            #if line == 'trace success':
            #    break
            if (line.startswith(cmd)):
                break
            else:
                if cbdataread is not None:
                    cbdataread(line)
                #print("VERBOSE::",line)
            if timeout is not None and timecnt>timeout:
                raise TimeoutError("timeout while waiting ray command io")
        return line.lstrip(cmd).strip()


