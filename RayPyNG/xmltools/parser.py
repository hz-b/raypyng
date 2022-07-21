from xml.sax import make_parser, handler
from .elements import *
from .dictionaries import *


###############################################################################
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
        # local copy is nessesary, input object can change and we should not 
        # save reference to it

        # Shall it be moved into the 
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

