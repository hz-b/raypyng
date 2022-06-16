###############################################################################
# XML helper class(es)
#
# Some code is based on the "untangle" package 
# see https://github.com/stchris/untangle and https://untangle.readthedocs.io/en/latest/
# fpr more details

###############################################################################

from xml.sax import make_parser, handler
from .collections import MappedList, MappedDict

import typing
import keyword

###############################################################################
class XmlChildrenList(list):
    pass


###############################################################################
def sanitizeName(name:str)->str:
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



###############################################################################
class XmlElement:
    """Representation of an XML element in its raw form

    Raises:
        AttributeError: _description_

    Returns:
        _type_: _description_

    Yields:
        _type_: _description_
    """
    #####################################
    def __init__(self, name:str, attributes:typing.MutableMapping, **kwargs):
        """_summary_

        Args:
            name (str): element name
            attributes (dict): element attributes as a dict-like object
        """
        if name is not None and not isinstance(name,str):
            raise TypeError("name parameter of 'XmlElement' class must be a string or 'None', got {}".format(type(name)))
        self._original_name = name
        self._name = sanitizeName(name)
        #self._name = name
        if attributes is not None and not isinstance(attributes,typing.MutableMapping):
            raise TypeError("attributes parameter of 'XmlElement' class must be a dict-line object or 'None', got {}".format(type(attributes)))
        self._attributes = attributes
        self._children = []
        self.is_root = False
        self.cdata = ""


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
        return "Element <%s> with attributes %s, children %s and cdata %s" % (
            self._name,
            self._attributes,
            self._children,
            self.cdata,
        )

    def __repr__(self):
        return "Element(name = %s, attributes = %s, cdata = %s)" % (
            self._name,
            self._attributes,
            self.cdata,
        )

    def __nonzero__(self):
        return self.is_root or self._name is not None

    def __eq__(self, val):
        return self.cdata == val

    def __dir__(self):
        children_names = [x._name for x in self._children]
        return children_names

    def __len__(self):
        return len(self._children)

    def __contains__(self, key):
        return key in dir(self)

###############################################################################
class XmlAttributedNameElement(XmlElement):
    def __init__(self, name_attribute:str, name: str, attributes: dict, **kwargs):
        super().__init__(name, attributes)
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

global_known_classes = {} # part of the development code
class Handler(handler.ContentHandler):
    
    #####################################
    def __init__(self,/,known_classes=None):
        self.root = XmlElement(None, None)
        self.root.is_root = True
        self.elements = []
        if known_classes is None:
            self._known_classes = global_known_classes
        else:
            self._known_classes = known_classes


    #####################################
    def startElement(self, name, attributes):
        """called on the start of an element in non-namespace mode.

        Args:
            name (_type_): _description_
            attributes (_type_): _description_
        """
        #print("DEBUG::startElement::name=",name)

        # store attributes in a dictionary
        attrs = SafeValueDict()
        for k, v in attributes.items():
            attrs[k] = v#self.protectName(v)
        
        # create a new element
        if name in self._known_classes.keys():
            element = self._known_classes[name](name, attrs)
        else:
            element = XmlElement(name, attrs)

        # and add it to the known element list
        if len(self.elements) > 0:
            self.elements[-1].add_child(element)
        else:
            self.root.add_child(element)
        self.elements.append(element)

    #####################################
    def endElement(self, name):
        """called the end of an element in non-namespace mode.

        Args:
            name (_type_): _description_
        """
        self.elements.pop()

    #####################################
    def characters(self, cdata):
        """adds character data to the current element

        Args:
            cdata (_type_): _description_
        """
        self.elements[-1].add_cdata(cdata.strip())

###############################################################################
def parse(filename:str, /, known_classes = None, **parser_features)->XmlElement:
    if filename is None:
        raise ValueError("parse() takes a filename")
    parser = make_parser()
    for feature, value in parser_features.items():
        parser.setFeature(getattr(handler, feature), value)
    sax_handler = Handler(known_classes=known_classes)
    parser.setContentHandler(sax_handler)
    parser.parse(filename)
    return sax_handler.root


###############################################################################
def serialize(element:XmlElement,/,indent = "", filename=None):
    def serialize_children(strlist,element,indent, base_indent):
        if element.children() is not None:
            if len(element.children()) > 0:
                strlist.append('\n')
                for c in element.children():
                    strlist.append(serialize(c,indent=indent))
                strlist += [base_indent]
        if element.cdata is not None:
                strlist.append(element.cdata)
        return ''.join(strlist)

    strlist = []
    if element.is_root:
        serialize_children(strlist,element,"","")
    else:
        strlist = [indent+'<'+element.original_name()]
        if element.attributes() is not None and len(element.attributes())>0:
            strlist.append(' ')
            attrs = []
            for k,v in element.attributes().original().items():
                attrs+=[k+'="'+v+'"']
            strlist.append(" ".join(attrs))
        strlist.append('>')
    
        serialize_children(strlist,element,indent+"    ",base_indent=indent)

        strlist += ['</',element.original_name(),'>\n']
    result =  ''.join(strlist)
    return result