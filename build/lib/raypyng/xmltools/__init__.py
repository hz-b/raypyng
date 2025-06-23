###############################################################################
# XML helper class(es)
#
# Some code is based on the "untangle" package
# see https://github.com/stchris/untangle and https://untangle.readthedocs.io/en/latest/
# for more details

###############################################################################


# from .attributes import *
# from .dictionaries import *
from .elements import XmlAttributedNameElement
from .parser import XmlElement, parse

__all__ = ["XmlAttributedNameElement", "parse"]


###############################################################################
def serialize(element: XmlElement, /, indent="", filename=None):
    def serialize_children(strlist, element, indent, base_indent):
        if element.children() is not None:
            if len(element.children()) > 0:
                strlist.append("\n")
                for c in element.children():
                    strlist.append(serialize(c, indent=indent))
                strlist += [base_indent]
        if element.cdata is not None:
            strlist.append(element.cdata)
        return "".join(strlist)

    strlist = []
    if element.is_root:
        serialize_children(strlist, element, "", "")
    else:
        strlist = [indent + "<" + element.original_name()]
        if element.attributes() is not None and len(element.attributes()) > 0:
            strlist.append(" ")
            attrs = []
            for k, v in element.attributes().original().items():
                attrs += [k + '="' + v + '"']
            strlist.append(" ".join(attrs))
        strlist.append(">")

        serialize_children(strlist, element, indent + "    ", base_indent=indent)

        strlist += ["</", element.original_name(), ">\n"]
    result = "".join(strlist)
    return result
