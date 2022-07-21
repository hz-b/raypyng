# -*- coding: utf-8 -*-
"""
Attention: this class was tested only in Ubuntu 18.04. It might work on MacOs evironment. It does not work in Windows. Go through this files, it is heavily commented and should explain you how to use this class. In the same folder as this script you must have RayPy.py and RayPy_utils.py. Additionally there should be a folder called rml and inside this folder your starting .rml file. 
(.rml files are the beamline configuration files saved by RAY-UI.)

Use Python 3.7.4
Python library to be installed
    -lxml
"""

import sys
from RayPy import *


#######################
### INITIALIZE CLASS ##
#######################

# the arguments are the directory where the starting rml file is
# and the name of the rml file (without extension)
test = RayPy(directory = 'rml/', rml_file = 'beamline')


#######################
### SET RAY PARAM #####
#######################


# set the ray location, substitute the '...'
#(pay attention to the slashes, the first and last one must be there)
ray_loc = '/.../RAY-UI-development/'
# set the name of the objects you want to export, separated by a comma
expo_obj= "Screen1,Screen3"
# set the name of what you want to export. 
# If you are not sure, try to export it manually in RAY-UI
expo_data = "FootprintAllRays"
# set the number of cpu used (each cpu will open RAY-UI and trace your beamline)
n_cpu = 1


test.SetRayLocation(ray_loc)
test.SetExportedObject(expo_obj)
test.SetExportedData(expo_data)


##########################
### PRINT RML FILE TREE ##
##########################

# This will print the structure of the rml file provided on the terminal
# Can be used to quickly check the names and id of the objects

test.PrintXmlFile()

#######################
##### ScanParam #######
#######################
# Here set which parameters you want to scan.

# If you have two indipendent parameters with values a1,a2 and b1,b2
# and one parameter dependent on a with values c1,c2, you will obtain the 
# following scans
# a1,b1,c1
# a1,b2,c1
# a2,b1,c2
# a2,b2,c2

# 0-th independent parameter to scan 
obj_name = 'Spherical Grating'
par_id = 'radius'
par_values=np.arange(180000, 260000.1, 80000)
test.AddIndependentParameter(obj_name, par_id,par_values)

# 1-st independent parameter to scan 
obj_name = 'Spherical Grating'
par_id = 'horOffset'
par_range=np.arange(-7, 7.1, 14)
test.AddIndependentParameter(obj_name, par_id,par_range)

# 0-th  dependent parameter to scan 
# The dependency of a dependent parameter must be given. 
# In this case it depends on the indipendent parameter 0 
# (the first one we added, start counting from zero)
obj_name = 'Spherical Grating'
par_id = 'vlsParameterB2'
par_values=np.arange(0.7e-5, 1.91e-5, 1.2e-5)
test.AddDependentParameter(obj_name, par_id,par_values,dependency=0)

# First we create the rml files. These files willl be added in a folder called ScanParam_test
# the simulations will be repeated three times, and saved in three different folders
test.CreateRmlFiles('test', first_file=0, repeat=3)

# Uncomment the next line when you are ready to start the simulations
# If you set cpus = False, or you don't set it at all, all the available cpus will be used
# You can use the same function to check if all the simulations have been performed and saved,
# and eventually simulate the missing files

test.CheckSimulations('test', cpus=n_cpu, current_directory = '.../', repeat = 3)
