

#from types import NoneType


class ValueTree:
    def __init__(self,xtype=None,*args,**kwargs) -> None:
        if xtype is not None and xtype is not type(None):
            self.__value = xtype(*args,**kwargs)
        else:
            self.__value = None
        self.__leafs = {}


    def __setattr__(self, name: str, value) -> None:
        #if __name in self.__leafs:
        if name is None:
            return 
        if name.startswith("_"):
            super().__setattr__(name,value)
        else:
            self.__leafs[name] = ValueTree(type(value),value) 
        #pass

    def __getattr__(self, name: str) -> None:
        if name.startswith("_"):
            super().__getattr__(name)
        else:
            if isinstance(self.__leafs[name],ValueTree):
                return self.__leafs[name].__value
            else:
                return self.__leafs[name]

    

class Attributed:
    def __new__(cls: type[Self]) -> Self:
        pass

    def __init__(self,value, *args,**kwargs) -> None:
        pass


class IntTest(int):
    def __new__(cls, *args, **kwargs):
        return  super().__new__(cls, *args,**kwargs)

# some reading on metaclasses:
# https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
