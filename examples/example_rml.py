from raypyng.rml import RMLFile
import os



this_file_dir=os.path.dirname(os.path.realpath(__file__))
rml_file = os.path.join(this_file_dir,'rml/dipole_beamline.rml')

rml = RMLFile(rml_file)


print('rml type:', type(rml))

print('rml.filename:', rml.filename)

print('rml.beamline type:', type(rml.beamline))

# print all the elements in the beamline
for oe in rml.beamline.children():
    print('OE:', oe.resolvable_name())

# print all the parameters of the Dipole
for param in rml.beamline.Dipole.children():
    print('Dipole param: ', param.id)

# Modify a paramer of the Diple:
print('Dipole photon energy: ',rml.beamline.Dipole.photonEnergy.cdata)
rml.beamline.Dipole.photonEnergy.cdata = str(2000)
print('New Dipole photon energy: ',rml.beamline.Dipole.photonEnergy.cdata)

# Save the rml file with a new name
rml.write('rml/new_elisa.rml')

        