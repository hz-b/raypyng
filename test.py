"""
from RayPyNG import runner

r = runner.RayUIRunner()
a = runner.RayUIAPI(r)

r.run()

a.load("test")
"""


import xml.etree.ElementTree as ET
tree = ET.parse('rml/beamline.rml')
root = tree.getroot()

from collections import defaultdict

# code from https://www.delftstack.com/howto/python/convert-xml-to-dictionary-python/
def xml2dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(xml2dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

# see more here for the info: https://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self