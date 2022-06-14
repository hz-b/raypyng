#

from .runner import RayUIRunner
from . import config

class RayPy:
    def __init__(self,rml_dir,rml_file) -> None:
        if rml_dir is None or rml_file is None:
            raise Exception("both rml dir and rml file must be specified for the RayPy instance creation")

        self._rml_dir = rml_dir
        self._rml_file = rml_file

        #self._runner = RayUIRunner()
    
    def SetRayLocation(self,ray_path:str):
        """Set default ray installation location

        Args:
            ray_path (str): string with a path to ray installation
        """
        config.ray_path = ray_path