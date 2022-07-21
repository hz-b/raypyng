
# RayPy

RayPy is a python class written to make multiple simulations using RAY-UI.
Scans can be easily implemented and run using all the cpus available on your machine.
The class have been tested only under Ubuntu 18.04 and Debian 9.6, but it might work also under MacOS.

Python version = 3+

External libraries to install:
- lxml
- numpy
    

The folder is organized in the following way:
   - base/_RayPy.py_
   - base/_RayPy_utils.py_
   - base/_generate_ray_data.py_
   - base/rml/:
        - _beamline.rml_
        
_RayPy.py_
This is the file where the RayPy class is written. Feel free to take a look into it and modify it if you need to. This file must be in the same folder as your script.

_RayPy_utils.py_
In this file some extra functions used by the RayPy class are implemented. This files must be in the same folder as your script. 

_generate_ray_data.py_
This is the example file. It is heavily commented and you can follow it to implement your first scans. The general idea that you can implement as many scans and as complicated as you need. 
