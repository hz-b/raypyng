import keyword

from ..collections import MappedDict, MappedList


###############################################################################
def sanitizeName(name: str) -> str:
    """convert name into python attribute safe name

    Args:
        name (str): _description_

    Returns:
        str: _description_
    """

    if name is None:
        return None

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
class SafeValueDict(MappedDict):
    def __init__(self, dict=None, **kwargs):
        super().__init__(sanitizeName, dict, **kwargs)


###############################################################################
class SafeValueList(MappedList):
    def __init__(self, initlist=None):
        super().__init__(sanitizeName, initlist)
