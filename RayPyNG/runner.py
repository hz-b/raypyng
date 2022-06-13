# Ray runner

from tkinter.messagebox import NO


class RayRunner:
    def __init__(self,ray_path=None,ray_binary="rayui.sh",background=True) -> None:
        if ray_path is None:
            raise Exception("ray_path must be defined for now!")
        self._path = ray_path
        self._binary = ray_binary
        self._options = "-b" if background else ""

        