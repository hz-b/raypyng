
###############################################################################
# Generic superclasses for collections line dict() or list()

from collections import UserDict
import keyword

###############################################################################
def protectName(name:str)->str:
    """convert name into python attribute safe name

    Args:
        name (str): _description_

    Returns:
        str: _description_
    """

    # repalce special characters with _
    name = name.replace("-", "_")
    name = name.replace(".", "_")
    name = name.replace(":", "_")

    # delete spaces
    name = name.replace(" ", "")

    # adding trailing _ for keywords
    if keyword.iskeyword(name):
        name += "_"
    return name


###############################################################################

###############################################################################
class SafeValueDict(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_values = dict()

    def __setitem__(self, key, item) -> None:
        self._original_values[key]=item
        return super().__setitem__(key, protectName(item))

    def original(self):
        return self._original_values

    # # Function to stop deletion
    # # from dictionary
    # def __del__(self):
    #     raise RuntimeError("Deletion not allowed")
         
    # # Function to stop pop from
    # # dictionary
    # def pop(self, s = None):
    #     raise RuntimeError("Deletion not allowed")
         
    # # Function to stop popitem
    # # from Dictionary
    # def popitem(self, s = None):
    #     raise RuntimeError("Deletion not allowed")