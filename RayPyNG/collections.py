
###############################################################################
# Generic superclasses for collections line dict() or list()

from collections import UserDict, UserList
import keyword

from collections.abc import MutableMapping,MutableSequence

import typing

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
# based on the collections.UserDict implementation from python 3.8.10
class MappedDict(MutableMapping):
    """MappedDict class implements a dictionary which will apply the given 
    function to each value added to it and also will keep a track of original 
    values.
    """
    def __init__(self, func:typing.Callable=None,dict=None, **kwargs):
        """Initializes instance of MappedDict class

        Args:
            func (typing.Callable, optional): function to be called on each
                new value added to the dictionary. Defaults to None.
            dict (optional): Optional initilizer, any dict-like object. 
                Defaults to None.

        Raises:
            TypeError: if suppled 'func' is not callable
        """
        if func is None:
            func = lambda x: x
        elif not callable(func):
            raise TypeError("callback parameter of 'MappedDict' object must be callable")
        self.__func = func        
        self.__data = {}
        self.__original_data = {}

        if dict is not None:
            self.update(dict)
        if kwargs:
            self.update(kwargs)

    def original(self):
        """prodives acccess to the original, unmodified data

        Returns:
            dict: dictionary with original data
        """
        return self.__original_data

    def __len__(self): return len(self.__data)
    def __getitem__(self, key):
        if key in self.__data:
            return self.__data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)
    def __setitem__(self, key, item):
        self.__original_data[key]=item
        self.__data[key] = self.__func(item)
    def __delitem__(self, key): 
        del self.__original_data[key]
        del self.__data[key]
    def __iter__(self):
        return iter(self.__data)

    # Modify __contains__ to work correctly when __missing__ is present
    def __contains__(self, key):
        return key in self.__data

    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self): return repr(self.__data)
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["__data"] = self.__dict__["__data"].copy()
        inst.__dict__["__original_data"] = self.__dict__["__original_data"].copy()
        inst.__dict__["__callback"] = self.__dict__["__callback"].copy()
        return inst

    def copy(self):
        if self.__class__ is MappedDict:
            return MappedDict(self.__original_data.copy())
        import copy
        data = self.__data
        try:
            self.__data = {}
            c = copy.copy(self)
        finally:
            self.__data = data
        c.update(self)
        return c

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d


###############################################################################
class SafeValueDict(MappedDict):
    def __init__(self, dict=None, **kwargs):
        super().__init__(protectName, dict, **kwargs)

