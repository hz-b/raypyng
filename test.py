"""
from RayPyNG import runner

r = runner.RayUIRunner()
a = runner.RayUIAPI(r)

r.run()

a.load("test")
"""

from RayPyNG.rml import RMLFile

rml1 = RMLFile('tests/rml1.xml',template='rml/beamline.rml')
rml2 = RMLFile('tests/rml2.xml',template='tests/rml/high_energy_branch_flux_1200.rml')

rml1.write()
rml2.write()
