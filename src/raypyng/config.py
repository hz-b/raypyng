# this is shared configuration space
import os

"""ray_path contains default path to the ray installation
"""
ray_path = None

"""ray_binary contains name of the default binary or shell script
   depending on the operating system
"""
opsys = os.popen("uname").read().strip()
if opsys == "Darwin":
    ray_binary = "Ray-UI.app/Contents/MacOS/Ray-UI"
else:
    ray_binary = "rayui.sh"