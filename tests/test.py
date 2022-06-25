
from RayPyNG.rml import RMLFile

rml1 = RMLFile('local/rml1.xml',template='rml/beamline.rml')
rml2 = RMLFile('local/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')

rml1.write()
rml2.write()
