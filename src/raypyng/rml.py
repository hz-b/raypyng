###############################################################################
# Reading/Writing/Modifying RML files
from . import xmltools as xml
from .xmltools import XmlAttributedNameElement, XmlElement


###############################################################################
class BeamlineElement(XmlAttributedNameElement):
    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__("name", name, attributes, **kwargs)


###############################################################################
class ObjectElement(XmlAttributedNameElement):
    _BOOLEAN_TOGGLES = {
        "reflectivity_enabled": {
            "param": "reflectivityType",
            "true_value": "1",
            "false_value": "0",
            "true_comment": "DerivedbyMaterial",
            "false_comment": "100%",
        },
        "slope_error_enabled": {
            "param": "slopeError",
            "true_value": "0",
            "false_value": "1",
            "true_comment": "Yes",
            "false_comment": "No",
        },
        "alignment_error_enabled": {
            "param": "alignmentError",
            "true_value": "0",
            "false_value": "1",
            "true_comment": "Yes",
            "false_comment": "No",
        },
    }

    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__("id", name, attributes, **kwargs)

    def __getattr__(self, key):
        if key in self._BOOLEAN_TOGGLES:
            return object.__getattribute__(self, key)
        return super().__getattr__(key)

    def _require_toggle_param(self, param_name: str):
        if not hasattr(self, param_name):
            element_name = self.resolvable_name()
            raise AttributeError(
                f"Beamline element '{element_name}' does not define '{param_name}' in the RML"
            )
        return getattr(self, param_name)

    def _toggle_spec(self, property_name: str):
        return self._BOOLEAN_TOGGLES[property_name]

    def _read_boolean_toggle(self, property_name: str) -> bool:
        spec = self._toggle_spec(property_name)
        param_name = spec["param"]
        param = self._require_toggle_param(param_name)
        value = str(param.cdata).strip()
        if value == spec["true_value"]:
            return True
        if value == spec["false_value"]:
            return False

        comment = str(param.attributes().get("comment", "")).strip().lower()
        if comment == spec["true_comment"].lower():
            return True
        if comment == spec["false_comment"].lower():
            return False
        raise ValueError(
            f"Beamline element '{self.resolvable_name()}' has unsupported '{param_name}' value "
            f"'{param.cdata}'"
        )

    def _write_boolean_toggle(self, property_name: str, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError(f"{property_name} expects a bool, got {type(enabled).__name__}")

        spec = self._toggle_spec(property_name)
        param_name = spec["param"]
        param = self._require_toggle_param(param_name)
        param.attributes()["comment"] = spec["true_comment"] if enabled else spec["false_comment"]
        param.cdata = spec["true_value"] if enabled else spec["false_value"]

    @property
    def reflectivity_enabled(self) -> bool:
        return self._read_boolean_toggle("reflectivity_enabled")

    @reflectivity_enabled.setter
    def reflectivity_enabled(self, enabled: bool) -> None:
        self._write_boolean_toggle("reflectivity_enabled", enabled)

    @property
    def slope_error_enabled(self) -> bool:
        return self._read_boolean_toggle("slope_error_enabled")

    @slope_error_enabled.setter
    def slope_error_enabled(self, enabled: bool) -> None:
        self._write_boolean_toggle("slope_error_enabled", enabled)

    @property
    def alignment_error_enabled(self) -> bool:
        return self._read_boolean_toggle("alignment_error_enabled")

    @alignment_error_enabled.setter
    def alignment_error_enabled(self, enabled: bool) -> None:
        self._write_boolean_toggle("alignment_error_enabled", enabled)


###############################################################################
class ParamElement(XmlElement):
    def __init__(self, name: str, attributes: dict, **kwargs):
        super().__init__(name, attributes, **kwargs)

    def __dir__(self):
        """enumerating child objects by its attibute name"""
        children_names = [x._name for x in self._children]
        attr_name = list(self._attributes.keys())
        return children_names + attr_name + ["cdata"]

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

    Args:
            filename (str, optional): path to rml file. Defaults to None.
            template (str, optional): path to rml file to use as template.
                                      Defaults to None.
    """

    def __init__(self, filename: str = None, /, template: str = None) -> None:
        """
        Args:
            filename (str, optional): path to rml file. Defaults to None.
            template (str, optional): path to rml file to use as template.
                                      Defaults to None.
        """
        self._filename = filename
        self._template = template if template is not None else filename
        self.__known_classes = {
            "beamline": BeamlineElement,
            "object": ObjectElement,
            "param": ParamElement,
        }
        self.read()

    @property
    def template(self):
        return self._template

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    ###################################
    def read(self, file: str = None):
        """Read rml file

        Args:
            file (str, optional): file name to read.
                If set to None will use template file name defined during
                initilizatino of the class. Defaults to None.
        """
        if file is None:
            file = self._template
        self._root = xml.parse(file, known_classes=self.__known_classes)
        self.beamline = self._root.lab.beamline

    def xml(self):
        return xml.serialize(self._root).strip()

    def write(self, file: str = None):
        """Write the rml to :code:`file`

        Args:
            file (str, optional): filename . Defaults to None.
        """
        if file is None:
            file = self._filename
        with open(file, "w") as f:
            f.write(self.xml())

    def __str__(self) -> str:
        return f"RMLFile('{self._filename}',template='{self._template}')"

    def __repr__(self) -> str:
        return f"RMLFile('{self._filename}',template='{self._template}')"


###############################################################################
# test function for the data parsing
def parse(filename: str):
    __known_classes = {"beamline": BeamlineElement, "object": ObjectElement, "param": ParamElement}
    xml.parse(filename, known_classes=__known_classes)
