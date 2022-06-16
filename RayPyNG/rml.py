###############################################################################
# Reading/Writing/Modifying RML files
from . import xmltools as xml
from .xmltools import XmlAttributedNameElement,XmlElement

###############################################################################
class BeamlineElement(XmlAttributedNameElement):
    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__("name",name, attributes, **kwargs)

###############################################################################
class ObjectElement(XmlAttributedNameElement):
    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__("id",name, attributes, **kwargs)


###############################################################################
class ParamElement(XmlElement):
    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__(name, attributes, **kwargs)

    def __dir__(self):
        """enumerating child objects by its attibute name

        Returns:
            _type_: _description_
        """
        children_names = [x._name for x in self._children]
        attr_name = list(self._attributes.keys())
        return children_names + attr_name + ['cdata']

    def __getattr__(self, key):
        matching_children = [x for x in self._children if x._name == key]
        if key in self._attributes:
            matching_children.append(self._attributes[key])
        if matching_children:
            if len(matching_children) == 1:
                self.__dict__[key] = matching_children[0]
                return matching_children[0]
            else:
                self.__dict__[key] = matching_children
                return matching_children
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self._name, key))


###############################################################################
class RMLFile:
    """Read/Write wrapper for the Ray RML files
    """
    def __init__(self,filename:str=None,/,template:str=None) -> None:
        self._filename=filename
        self._template = template if template is not None else filename
        self.__known_classes = {"beamline":BeamlineElement, 
                                "object":ObjectElement,
                                "param":ParamElement}
        self.read()
        self.beamline = self._root.lab.beamline
        


    ###################################
    def read(self,file:str=None):
        """read rml file

        Args:
            file (str, optional): file name to read. If set to None will use template file name defined during initilizatino of the class. Defaults to None.
        """
        if file is None:
            file = self._template
        self._root = xml.parse(file,known_classes = self.__known_classes)      

    def write(self,file:str=None):
        if file is None:
            file = self._filename
        xmlstr = xml.serialize(self._root)
        #print(xmlstr)
        with open(file,"w") as f:
            f.write(xmlstr)

###############################################################################
# test function for the data parsing
def parse(filename:str):
    __known_classes = {"beamline":BeamlineElement, 
                        "object":ObjectElement,
                        "param":ParamElement}
    xml.parse(filename,known_classes = __known_classes)        
