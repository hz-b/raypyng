# see https://untangle.readthedocs.io/en/latest/ for more info

#%pip install untangle

#import untangle
#t1 = untangle.parse('rml/beamline.rml')

import RayPyNG.xmltools as xml

e1 = xml.parse('rml/beamline.rml')
e2 = xml.parse('tests/rml/high_energy_branch_flux_1200.rml')


#e.lab.beamline.object[1].param[3]