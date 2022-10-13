

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

    

# class Attributed:
#     def __new__(cls: type[Self]) -> Self:
#         pass

#     def __init__(self,value, *args,**kwargs) -> None:
#         pass


class IntTest(int):
    def __new__(cls, *args, **kwargs):
        print(f"cls={cls}, args={args}, kwargs={kwargs}")
        return  super().__new__(cls, *args,**kwargs)

class TypeX:
    def __new__(cls, _type, *args, **kwargs):
        class X(_type):
            def __new__(cls, *args, **kwargs):
                print(f"cls = {cls} and its type is {type(cls)}")
                return  super().__new__(cls, *args,**kwargs)
            

        return  X(*args,**kwargs)

class TypeX2:
    def __new__(cls, _type, *args, **kwargs):
        class X(_type):
            def __new__(cls, *args, **kwargs):
                print(f"cls = {cls} and its type is {type(cls)}")
                return  super().__new__(cls, *args,**kwargs)
            

        return  X.__new__(*args,**kwargs)

class MetaType(type):
    def __new__(cls, clsname, bases, attribs):
        # change bases
        print(f'cls={cls},clsname={clsname},bases={bases},attribs={attribs}')
        return type(clsname, bases, attribs)

class TypeX3(metaclass=MetaType):
    def __new__(cls, *args, **kwargs):
        print(f"cls={cls}, args={args}, kwargs={kwargs}")
        if not args:
            raise TypeError("value or type is needed for creating AutoType object")
        _val_or_type, *args = args
        if isinstance(_val_or_type,type):
            return _val_or_type.__new__(cls,*args,**kwargs)
        else:
            _type = type(_val_or_type)
            return _type.__new__(cls,_val_or_type,*args,**kwargs)

class TypedBase:
    def __init__(self) -> None:
        self.tname = type(self)
    

def TypeFactory(*args, **kwargs):
        print(f"args={args}, kwargs={kwargs}")
        if not args:
            raise TypeError("value or type is needed for creating AutoType object")
        
        def new(_type):
            _cls = str(_type.__name__)+'.TypedBase'
            return type(_cls,(_type,TypedBase),{'__init__': lambda self,*args,**kwargs: super().__init__(self,*args,**kwargs)})

        _val_or_type, *args = args
        if isinstance(_val_or_type,type):
            _type = new(_val_or_type)
            print(f"_type={type}, args={args}, kwargs={kwargs}")
            return _type(*args,**kwargs)
        else:
            _type = new(type(_val_or_type))
            print(f"_type={type}, val={_val_or_type}, args={args}, kwargs={kwargs}")
            return new(_type)(_val_or_type,*args,**kwargs)


# some reading on metaclasses:
# https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python


# some ideas from https://stackoverflow.com/questions/3238350/subclassing-int-in-python

class ModifiedType(type):
    """
    ModifedType takes an exising type and wraps all its members
    in a new class, such that methods return objects of that new class.
    The new class can leave or change the behaviour of each
    method and add further customisation as required
    """

    # We don't usually need to wrap these
    _dont_wrap = {
    "__str__", "__repr__", "__hash__", "__getattribute__", "__init_subclass__", "__subclasshook__",
    "__reduce_ex__", "__getnewargs__", "__format__", "__sizeof__", "__doc__", "__class__"}

    @classmethod
    def __prepare__(typ, name, bases, base_type, do_wrap=None, verbose=False):
        return super().__prepare__(name, bases, base_type, do_wrap=do_wrap, verbose=verbose)

    def __new__(typ, name, bases, attrs, base_type, do_wrap=None, verbose=False):
        bases += (base_type,)

        #  Provide a call to the base class __new__
        attrs["__new__"] = typ.__class_new__

        cls = type.__new__(typ, name, bases, attrs)

        if "dont_wrap" not in attrs:
            attrs["dont_wrap"] = {}
        attrs["dont_wrap"].update(typ._dont_wrap)

        if do_wrap is not None:
            attrs["dont_wrap"] -= set(do_wrap)

        base_members = set(dir(base_type))
        typ.wrapped = base_members - set(attrs) - attrs["dont_wrap"]

        for member in typ.wrapped:
            obj = object.__getattribute__(base_type, member)
            if callable(obj):
                if verbose:
                    print(f"Wrapping {obj.__name__} with {cls.wrapper.__name__}")
                wrapped = cls.wrapper(obj)
                setattr(cls, member, wrapped)
        return cls

    def __class_new__(typ, *args, **kw):
        "Save boilerplate in our implementation"
        return typ.base_type.__new__(typ, *args, **kw)

# Create the new Unsigned type and describe its behaviour
class Unsigned(metaclass=ModifiedType, base_type=int):
    """
    The Unsigned type behaves like int, with all it's methods present but updated for unsigned behaviour
    """
    # Here we list base class members that we won't wrap in our derived class as the
    # original implementation is still useful. Other common methods are also excluded in the metaclass
    # Note you can alter the metaclass exclusion list using 'do_wrap' in the metaclass parameters
    dont_wrap = {"bit_length", "to_bytes", "__neg__", "__int__", "__bool__"}
    import functools

    def __init__(self, value=0, *args, **kw):
        """
        Init ensures the supplied initial data is correct and passes the rest of the
        implementation onto the base class
        """
        if value < 0:
            raise ValueError("Unsigned numbers can't be negative")

    @classmethod
    def wrapper(cls, func):
        """
        The wrapper handles the behaviour of the derived type
        This can be generic or specific to a particular method
        Unsigned behavior is:
            If a function or operation would return an int of less than zero it is returned as zero
        """
        @cls.functools.wraps(func)
        def wrapper(*args, **kw):
            ret = func(*args, **kw)
            ret = cls(max(0, ret))
            return ret
        return wrapper


# some ideas from https://www.geeksforgeeks.org/create-classes-dynamically-in-python/

# program to create class dynamically
  
# constructor
def constructor(self, arg):
    self.constructor_arg = arg
  
# method
def displayMethod(self, arg):
    print(arg)
  
# class method
@classmethod
def classMethod(cls, arg):
    print(arg)
  
class BaseClass:
    sparam = "Hello"

# creating class dynamically

class AttributeBase:
    def __init__(self,*args,**kwargs) -> None:
        self.param = 42
    

def AttributeFactory(*args,**kwargs):
    if not args:
        raise TypeError("value or type is needed for creating AttributeFactory object")
    type_or_value, *args = args
    if isinstance(type_or_value,type):
        _type = type_or_value
    else:
        _type = type(type_or_value)
        args = (type_or_value, *args)
    _sclass = type(f"Attribute<{_type}>", (AttributeBase, _type, ), {
        "__new__" : lambda __name, __bases, *args, **kwargs : _type.__new__(__name, __bases, *args, **kwargs)
    })
    return _sclass(*args,**kwargs)
  
