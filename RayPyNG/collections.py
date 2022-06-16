
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
# based on the collections.UserList implementation from python 3.8.10
class MappedList(MutableSequence):
    """MappedList class implements a list which will apply the given 
    function to each value added to it and also will keep a track of original 
    values.
    """
    def __init__(self, func:typing.Callable=None, initlist=None):
        """Initializes instance of MappMappedListedDict class

        Args:
            func (typing.Callable, optional): function to be called on each
                new value added to the dictionary. Defaults to None.
            initlist (_type_, optional): Optional initilizer, any iterable object.
                Defaults to None.

        Raises:
            TypeError:  if suppled 'func' is not callable
        """
        if func is None:
            func = lambda x: x
        elif not callable(func):
            raise TypeError("callback parameter of 'MappedList' object must be callable")
        self.__func = func        

        self.__data = []
        self.__original_data = []

        if initlist is not None:
            self.extend(initlist)


    def __repr__(self): return repr(self.__data)
    def __lt__(self, other): return self.__data <  self.__cast(other)
    def __le__(self, other): return self.__data <= self.__cast(other)
    def __eq__(self, other): return self.__data == self.__cast(other)
    def __gt__(self, other): return self.__data >  self.__cast(other)
    def __ge__(self, other): return self.__data >= self.__cast(other)
    def __cast(self, other):
        return other.__data if isinstance(other, MappedList) else other
    def __contains__(self, item): return item in self.__data
    def __len__(self): return len(self.__data)
    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.__data[i])
        else:
            return self.__data[i]
    def __setitem__(self, i, item):
        self.__original_data[i] = item
        self.__data[i] = self.__func(item)
    def __delitem__(self, i): 
        del self.__original_data[i]
        del self.__data[i]
    def __add__(self, other):
        if isinstance(other, MappedList):
            return self.__class__(self.__func,self.__original_data + other.__original_data)
        elif isinstance(other, type(self.__data)):
            return self.__class__(self.__func,self.__original_data + other)
        return self.__class__(self.__func,self.__original_data + list(other))
    def __radd__(self, other):
        if isinstance(other, MappedList):
            return self.__class__(self.__func,other.__original_data + self.__original_data)
        elif isinstance(other, type(self.__data)):
            return self.__class__(self.__func,other + self.__original_data)
        return self.__class__(self.__func,list(other) + self.__original_data)
    def __iadd__(self, other):
        if isinstance(other, MappedList):
            self.__data += other.__data
            self.__original_data += other.__original_data
        elif isinstance(other, type(self.__data)):
            self.__original_data += other
            self.__data += map(self.__func, other)
        else:
            self.__original_data += list(other)
            self.__data += map(self.__func, other)
        return self
    def __mul__(self, n):
        return self.__class__(self.__func, self.__orignal_data*n)
    __rmul__ = __mul__
    def __imul__(self, n):
        self.__original_data *= n
        self.__data *= n
        return self
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["__data"] = self.__dict__["__data"][:]
        inst.__dict__["__original_data"] = self.__dict__["__original_data"][:]
        inst.__dict__["__func"] = self.__dict__["__func"][:]
        return inst
    def append(self, item): 
        self.__original_data.append(item)
        self.__data.append(self.__func(item))
    def insert(self, i, item): 
        self.__original_data.insert(i, item)
        self.__data.insert(i, self.__func(item))
    def pop(self, i=-1): 
        self.__original_data.pop(i)
        return self.__data.pop(i)
    def remove(self, item): 
        self.__original_data.remove(item)
        self.__data.remove(item)
    def clear(self): 
        self.__original_data.clear()
        self.__data.clear()
    def copy(self): return self.__class__(self)
    def count(self, item): return self.__data.count(item)
    def index(self, item, *args): return self.__data.index(item, *args)
    def reverse(self): 
        self.__original_data.reverse()
        self.__data.reverse()
    def sort(self, /, *args, **kwds): 
        self.__original_data.sort(*args, **kwds)
        self.__data.sort(*args, **kwds)
    def extend(self, other):
        if isinstance(other, MappedList):
            self.__original_data.extend(other.__original_data)
            self.__data.extend(other.__data)
        else:
            self.__original_data.extend(other)
            self.__data.extend(map(self.__func,other))


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
        inst.__dict__["__func"] = self.__dict__["__func"].copy()
        return inst

    def copy(self):
        if self.__class__ is MappedDict:
            return MappedDict(self.__func,self.__original_data.copy())
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

