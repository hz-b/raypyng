# this is shared configuration space
import platform

"""ray_path contains default path to the ray installation
"""
ray_path = None

"""ray_binary contains name of the default binary or shell script
   depending on the operating system
"""
opsys = platform.system()
if opsys == "Darwin":
    # RAY-UI is distributed as an installer that unpacks to a folder containing Ray-UI.app
    ray_binary = "Ray-UI.app/Contents/MacOS/Ray-UI"
elif opsys == "Windows":
    ray_binary = "rayui.exe"
else:
    ray_binary = "rayui.sh"
