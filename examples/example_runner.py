import os
import time
from raypyng.runner import RayUIRunner, RayUIAPI

r = RayUIRunner(ray_path=None, hide=True)
a = RayUIAPI(r)


# Start a RAY-UI instance
r.run()

# Confirm that it is running and print the process id
print('Confirm that RAY-UI is running:', r.isrunning)
print("RAY-UI is running with pid", r.pid)

# load an rml file
print("Loading rml file")
a.load('rml/elisa.rml')

print("Trace...")
a.trace(analyze=True)

print("Exporting")
this_file_dir=os.path.dirname(os.path.realpath(__file__))
a.export("Dipole,DetectorAtFocus", "RawRaysOutgoing", this_file_dir, 'test_export')


print("Killing the RAY-UI process")
r.kill()
# sometime it takes a while to kill the process
time.sleep(2)
print('Confirm that RAY-UI is running:', r.isrunning)




        