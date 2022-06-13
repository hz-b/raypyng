# -*- coding: utf-8 -*-
"""
Attention: this class was tested only in Ubuntu 18.04. It might work on MacOs evironment. It does not work in Windows. Go through this files, it is heavily commented and should explain you how to use this class. In the same folder as this script you must have RayPy.py and RayPy_utils.py. Additionally there should be a folder called rml and inside this folder your starting .rml file. 
(.rml files are the beamline configuration files saved by RAY-UI.)

Use Python 3.7.4
Python library to be installed
    -lxml
"""
from config import path_to_RAY, current_directory


import sys
# Insert here the path to the installatio folder of RAY-UI

sys.path.insert(1, path_to_RAY+'/RAYpy/')

import numpy as np
import matplotlib.pyplot as plt
from RayPy import *


### IMPORTANT !!!! ####
# Check how many CPU you have. Ray will be called once per CPU. 
n_cpu = 1


energy    =np.arange(40,3001,20)
SlitSize  =np.array([0.05])
grating   =np.array([1200])
cFactor   =np.array([2.25])
blaze     =np.array([0.9])
nrays     =5000


rml_file_list = ['high_energy_branch_flux_1200']



if __name__ == '__main__':
    mp.freeze_support()

for rml in rml_file_list:
    #######################
    ### INITIALIZE CLASS ##
    #######################

    # the arguments are the directory where the starting rml file is
    # and the name of the rml file (without extension)
    test = RayPy(directory = 'rml/', rml_file = rml)
    name = rml
    #######################
    ### SET RAY PARAM #####
    #######################


    # set the ray location, substitute the '...'
    #(pay attention to the slashes, the first and last one must be there)
    ray_loc = path_to_RAY+"/rayui.sh -b\n"
    # set the name of the objects you want to export, separated by a comma
    expo_obj= "Dipole,DetectorAtFocus"
    # set the name of what you want to export. 
    # If you are not sure, try to export it manually in RAY-UI
    expo_data = "ScalarBeamProperties,ScalarElementProperties"
    #expo_data = "ScalarBeamProperties"
    # set the number of cpu used (each cpu will open RAY-UI and trace your beamline)

    

    test.SetRayLocation(ray_loc)
    test.SetExportedObject(expo_obj)
    test.SetExportedData(expo_data)
    ##########################
    ### PRINT RML FILE TREE ##
    ##########################
    # This will print the structure of the rml file provided on the terminal
    # Can be used to quickly check the names and id of the objects

    #test.PrintXmlFile()


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


    obj_name = 'Dipole'
    par_id = 'photonEnergy'
    par_values=energy
    test.AddIndependentParameter(obj_name, par_id,par_values)
    
    obj_name = 'ExitSlit'
    par_id = 'totalHeight'
    par_values=np.full(energy.shape[0],SlitSize)
    test.AddDependentParameter(obj_name, par_id,par_values,0)
    
    obj_name = 'PG'
    par_id = 'cFactor'
    par_values=np.full(energy.shape[0],cFactor)
    test.AddDependentParameter(obj_name, par_id,par_values,0)
    
    
    obj_name = 'Dipole'
    par_id = 'numberRays'
    par_values=np.full(energy.shape[0], nrays)
    test.AddDependentParameter(obj_name, par_id,par_values,0)
    


    # First we create the rml files. These files willl be added in a folder called ScanParam_test
    
    ## ACHTUNG! this is commented because the beamlines are adjusted by hand!
    test.CreateRmlFiles(name, first_file=0 )
    
    test.CheckSimulations(name,current_directory=current_directory, cpus=n_cpu)
        
    

