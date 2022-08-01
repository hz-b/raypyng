import numpy as np
import matplotlib.pyplot as plt
import time
from scipy.ndimage import rotate
from ray_trace_lib import *    

'''
To use this class one has to trace and export RawRaysOutgoing for each optical element (no image planes)
When you add elements: 
    -name: the name is the name of the OE as defined in RAY-UI
    -z   : this is the distance (in mm) to the next OE
    -rot : the rotation has to be set to True if the azimuthal angle
           of the OE is either 90 or 270. It is possible to extend the class to calculate also in between angles.

Usage advice: do not start by exporting millions of rays with RAYUI. Start with 1e4 or 1e5 rays and check that you setup the class with your desired parameters, once you are satisfied with the plotting then increase the rays

The plot method returns the data it used for producing the plot, in case you want to customise the plot.

'''
 
hard = RayPy_PlotBeamline(directory='data/hard') # enter directory where your data is
hard.define_hist(lim=20,step=.1)  # lim should be larger than max beam waist
hard.define_zstep(step_z=1)      # in mm, step in optical direction to trace RAYS
hard.reduce_Nrays(factor = 1)   # this reduces the n of rays by the factor you set
hard.load_previous_results(True, directory='data/hard') # set the firs argument to true if you already saved the results of the trace

hard.add_element(name='Dipole',        z=12500, rot=False)
hard.add_element(name='M1',            z=2000,  rot=True)
hard.add_element(name='Plane Mirror 1',z=5302,  rot=True)
hard.add_element(name='Premirror M2',  z=498,   rot=False)
hard.add_element(name='PG',            z=1500,  rot=False)
hard.add_element(name='M3',            z=13000, rot=True)
hard.add_element(name='ExitSlit',      z=3500,  rot=False)
hard.add_element(name='KB1',           z=300,   rot=True)
hard.add_element(name='KB2',           z=3000,  rot=False)
hard.change_name(new_name = 'PM1', pos=2)
hard.change_name(new_name = 'M2',  pos=3)
hard.save_results(save_results=True, directory='data/hard')

xh,yh,x,y=hard.plot(save_img=True,save_directory='plot',img_name='high_energy_branch',extension='.png',show_img=False,annotate_OE=True)

xh,yh,x,y=hard.plot(save_img=True,save_directory='plot',img_name='high_energy_branch_zoom',extension='.png',show_img=False,annotate_OE=True,lim_top=[38.5,41.5,-3,3],lim_side=[38.5,41.5,-.7,.7])

# one can use xh,yh,x,y to buld his own plots:
# suggested usage: ax.pcolormesh(x,y,np.log(self.xh), cmap='inferno')


