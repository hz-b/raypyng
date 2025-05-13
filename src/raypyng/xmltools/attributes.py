###############################################################################
class XmlAttribute:
    def __init__(self, xmlvalue=None) -> None:
        if xmlvalue is not None:
            self.__value = xmlvalue

    def set(self, value):
        self.__value = value

    def get(self):
        return self.__value

    def __str__(self):
        return str(self.__value)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"


###############################################################################
class XmlMappedAttribute(XmlAttribute):
    def __init__(self, xmlvalue=None, map=None) -> None:
        if map is None:
            raise ValueError("map parameter is required and can not be 'None'")
        self.__map = map
        super().__init__(xmlvalue)

        if xmlvalue in self.__map:
            self.set(self.__map[xmlvalue])
        else:
            raise ValueError(f"Invalid value for the XmlAttribute: {xmlvalue}")

    def __str__(self):
        for k, v in self.__map.items():
            if v == self.get():
                return k
        raise ValueError(f"Can not map to bool: {self.get()}")

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}',map={self.__map})"


###############################################################################
class XmlBoolAttribute(XmlMappedAttribute):
    def __init__(self, xmlvalue=None, true="True", false="False") -> None:
        m = {true: True, false: False}
        super().__init__(xmlvalue, m)
