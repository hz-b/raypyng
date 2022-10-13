# see https://declxml.readthedocs.io/en/latest/guide.html for more info

import declxml

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class ObjectsDict(dict):
    def __init__(self, *args, **kwargs):
        super(ObjectsDict, self).__init__(*args, **kwargs)
        self.objects={}
        self.__dict__ = self.objects


class Beamline(ObjectsDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

param_processor = declxml.dictionary('param', [
    declxml.string('.'),
    declxml.string('.',attribute='id'),
    declxml.string('.',attribute='enabled'),
    declxml.string('.',attribute='auto', required=False),
    declxml.string('.',attribute='comment', required=False),
])

object_processor = declxml.dictionary('object', [
    declxml.string('.',attribute='name'),
    declxml.string('.',attribute='type'),
    declxml.array(param_processor,alias='params')
])

beamline_processor = declxml.dictionary('beamline', [
    declxml.array(object_processor,alias="objects")
])

rml_processor = declxml.dictionary('lab', [
    declxml.string('version'),
    declxml.array(beamline_processor),
    declxml.string('ExtraData') # do not know what is this , just grab it as a string
])

# testing dataset 1
ds1 = declxml.parse_from_file(rml_processor, 'rml/beamline.rml')

# testing dataset 2
ds2 = declxml.parse_from_file(rml_processor, 'tests/rml/high_energy_branch_flux_1200.rml')