import typing

from .dictionaries import *
from .attributes import *


###############################################################################
class XmlElement:
    """Representation of an XML element in its raw form

    Raises:
        AttributeError: _description_
    """
    #####################################
    def __init__(self, name:str, attributes:typing.MutableMapping, parent=None, **kwargs):
        """_summary_

        Args:
            name (str): element name
            attributes (dict): element attributes as a dict-like object
        """
        if name is not None and not isinstance(name,str):
            raise TypeError("name parameter of 'XmlElement' class must be a string or 'None', got {}".format(type(name)))
        self._original_name = name
        self._name = sanitizeName(name)
        if attributes is not None and not isinstance(attributes,typing.MutableMapping):
            raise TypeError("attributes parameter of 'XmlElement' class must be a dict-line object or 'None', got {}".format(type(attributes)))
        
        # converting attributes ...
        _attributes = SafeValueDict()
        if attributes is not None:
            if isinstance(attributes,MappedDict):
                _attribute_items = attributes.original().items()
            else:
                _attribute_items = attributes.items()
            for k,v in _attribute_items:
                _attributes[k] = v#XmlAttribute(v)
        self._attributes = _attributes

        self._children = []
        self.is_root = False
        self.cdata = ""
        self._parent = parent

    def get_full_path(self):
        """Returns the full path of the xml object

        Returns:
            str: path of the xml object
        """        
        if self._parent is None:
            return self.resolvable_name()
        else:
            return self._parent.get_full_path()+"."+self.resolvable_name()

    def resolvable_name(self):
        """Returns the name of the objects, removing lab.beamline.

        Returns:
            str: name of the object
        """        
        if self._parent is None:
            return self._name
        else:
            if hasattr(self._parent,"_name_attribute"):
                return self[self._parent._name_attribute]
            else:
                return self._name#"NOTFOUND"

    #@property
    def children(self):
        return self._children

    #@property
    def attributes(self):
        return self._attributes

    #@property
    def original_name(self):
        return self._original_name

    #@property
    def name(self):
        return self._name

    def add_child(self, element):
        """
        Store child elements.
        """
        self._children.append(element)

    def add_cdata(self, cdata):
        """
        Store cdata
        """
        self.cdata = self.cdata + cdata

    def get_attribute(self, key):
        """
        Get attributes by key
        """
        return self._attributes.get(key)

    def get_elements(self, name=None):
        """
        Find a child element by name
        """
        if name:
            return [e for e in self._children if e._name == name]
        else:
            return self._children


    # dictionary line access to the elements
    def __getitem__(self, key):
        return self.get_attribute(key)

    # attribute aka ./dot access to the fields
    def __getattr__(self, key):
        matching_children = [x for x in self._children if x._name == key]
        if matching_children:
            if len(matching_children) == 1:
                self.__dict__[key] = matching_children[0]
                return matching_children[0]
            else:
                self.__dict__[key] = matching_children
                return matching_children
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self._name, key))

    def __hasattribute__(self, name):
        if name in self.__dict__:
            return True
        return any(x._name == name for x in self._children)

    def __iter__(self):
        yield self

    def __str__(self):
        return "XmlElement <%s> with attributes %s, children %s and cdata %s" % (
            self._name,
            self._attributes,
            self._children,
            self.cdata,
        )

    def __repr__(self):
        if True:
            return "XmlElement(name = %s, attributes = %s, cdata = %s)" % (
                self._name,
                self._attributes,
                self.cdata,
            )
        else:
            return f'{self.id}'

    def __nonzero__(self):
        return self.is_root or self._name is not None

    def __eq__(self, val):
        return self.cdata == val


    def __hash__(self) -> int:
        return hash((tuple(self._children),tuple(self._attributes),tuple(self._name)))

    def __dir__(self):
        children_names = [x._name for x in self._children]
        return children_names

    def __len__(self):
        return len(self._children)

    def __contains__(self, key):
        return key in dir(self)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass#return True

###############################################################################
class XmlAttributedNameElement(XmlElement):
    def __init__(self, name_attribute:str, name: str, attributes: dict, **kwargs):
        super().__init__(name, attributes,**kwargs)
        self._name_attribute = name_attribute


    def __dir__(self):
        """enumerating child objects by its attibute name

        Returns:
            _type_: _description_
        """
        children_names = [x._attributes[self._name_attribute] for x in self._children]
        return children_names

    # def __setattr__(self, __name: str, __value) -> None:
    #     if __name!="_name" and __name!="_attributes" and __name!="children" and __name!="is_root"  and __name!="cdata" and __name!="_name_attribute":
    #         raise AttributeError("XmlAttributedNameElement object attribute '{}' is read-only".format(__name))

    # def __setattr__(self, __name: str, __value) -> None:
    #     if hasattr(self,__name):
    #         return super().__setattr__(__name, __value)
    #     else:
    #         raise AttributeError("XmlAttributedNameElement object attribute '{}' is read-only".format(__name))

    def __getattr__(self, key):
        matching_children = [x for x in self._children if x._attributes[self._name_attribute] == key]
        if matching_children:
            if len(matching_children) == 1:
                self.__dict__[key] = matching_children[0]
                return matching_children[0]
            else:
                self.__dict__[key] = matching_children
                return matching_children
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self._name, key))