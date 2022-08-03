from RayPyNG.simulate import Simulate
from .rml import ObjectElement

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import sys
from scipy.ndimage import rotate
    

class PlotBeamwaist():
    '''
    To use this class one needs to trace and export RawRaysOutgoing for each optical element (no image planes)
    '''
    def __init__(self, directory:str, sim:Simulate):
        self.directory = 'RAYPy_Simulation_'+directory
        if isinstance(sim,Simulate):
            self._sim = sim
        self.lim              = False
        self.step             = False
        self.z                = False
        self.step_z           = False
        self.rot              = False
        self.factor           = False
        self.previous_results = False
        self.count_el         = 0
        self.elements         = []
        self.distances        = [0]
        self.count_fig        = 0
    
    def simulate_beamline(self, energy:float,/,source:ObjectElement=None,sim_folder:str=None, force:bool=False):
        self._sim.beamwaist_simulation(energy,source=source,sim_folder=sim_folder, force=force)
    
    def _element_list(self):
        self.element_names_list = []
        self.distance_list=[]
        self.rotation_list=[]
        for ind, oe in enumerate(self._sim.rml.beamline._children):
                for par in oe:
                    try:
                        a=par.alignmentError
                        self.distance_list.append(float(par.worldPosition.z.cdata))
                        self.element_names_list.append('element_'+str(ind))
                        # print('DEBUG:: oe.name:', oe.name)
                        if ind == 0:
                            self.rotation_list.append(False)
                        else:
                            if par.azimuthalAngle.cdata == '0' or par.azimuthalAngle.cdata=='180':
                                self.rotation_list.append(False)
                            elif par.azimuthalAngle.cdata == '90' or par.azimuthalAngle.cdata=='270':
                                self.rotation_list.append(True)
                            else: 
                                raise ValueError('Only beamline elements with azimula angle 0,90,180,270 are supported', oe.name, par.azimuthalAngle.cdata)
                    except AttributeError:
                        pass
        #print('DEBUG:: element_names_list', self.element_names_list)
        #print('DEBUG:: distance_list', self.distance_list)
        #print('DEBUG:: rotation_list', self.rotation_list)
        # I overwrite the names for the moment, since I can not access them automatically
        self.element_names_list=['Dipole', 'M1', 'PremirrorM2', 'PG', 'M3', 'ExitSlit', 'KB1', 'KB2' ]
        for ind in range(len(self.element_names_list)):
            self.add_element(name=self.element_names_list[ind],
                            z=self.distance_list[ind],
                            rot=self.rotation_list[ind])
    
    def reduce_Nrays(self,factor):
        self.factor = factor
        
    def load_previous_results(self,previous_results, directory=False):
        start1  = time.time()
        self.previous_results = previous_results
        if self.previous_results == True:
            print('Load results...')
            self.xh=np.loadtxt(os.path.join(directory,'xh.txt'))
            self.yh=np.loadtxt(os.path.join(directory,'yh.txt'))
            stop = time.time()
            print('time:', np.round(stop-start1,2),'s')
        
    def save_results(self, save_results, directory):
        if save_results == True:
            np.savetxt(os.path.join(directory, 'xh.txt'), self.xh)
            np.savetxt(os.path.join(directory, 'yh.txt'), self.yh)
            
    def add_element(self,name,z,rot=False,step_z=False):
        self.elements.append(name)
        self.distances.append(z)
        start1  = time.time()
        z       = np.arange(0,z+self.step_z,self.step_z)

        if self.previous_results == False:
            print('Trace '+name)
            
            rays    = np.loadtxt(os.path.join(self.directory,'round_0', 
                                         '0_'+name
                                         +'-RawRaysOutgoing.csv'), 
                            skiprows=2)
            if self.factor != False:
                max_n_rays = int(rays.shape[0]/self.factor)
            if max_n_rays <= 100:
                sys.exit('Set a lower reduction factor, there are no more rays to plot!')
            rays = rays[0:max_n_rays]
            
            
            if self.count_el == 0:
                self.xh,self.yh   = self.trace(z,rays,self.lim,self.step,rot)
                print(self.xh.shape, self.yh.shape)
            else:
                txh,tyh   = self.trace(z,rays,self.lim,self.step,rot)
            if rot == True:
                txh=np.rot90(txh)
                tyh=np.rot90(tyh)
            if self.count_el != 0:
                print(txh.shape, tyh.shape)
                self.xh=np.concatenate((self.xh,txh),axis=1)
                self.yh=np.concatenate((self.yh,tyh),axis=1)

            stop = time.time()
            print('time:', np.round(stop-start1,2),'s')
        self.count_el += 1
        
    def define_hist(self,lim,step):
        self.lim  = lim
        self.step = step
    
    def define_zstep(self,step_z):
        self.step_z = step_z
    
        
    def trace_pos(self,rays,z):
        ox     = 3
        oy     = 4
        oz     = 5
        dx     = 6
        dy     = 7
        dz     = 8
        
        dxz = rays[:,dx]/rays[:,dz]
        x   = rays[:,ox] + dxz*(z-rays[:,oz])
        dyz = rays[:,dy]/rays[:,dz]
        y   = rays[:,oy] + dyz*(z-rays[:,oz])        
        return x,y

    def make_histogram(self,x):
        xh=np.histogram(x,bins=np.arange(-self.lim-self.step,
                                         self.lim+self.step,
                                         self.step))
        return xh
        
        
    def trace(self,z,rays,lim,step,rot=False):
        for n,z in enumerate(z):
            #print(z,n)

            x,y      = self.trace_pos(rays,z)
            shiftx   = np.average(x)
            shifty   = np.average(y)
            #print('average',shiftx,shifty)
            y        = y-shifty
            x        = x-shiftx
            if n==0:
                xh         =  self.make_histogram(x)
                xh         =  xh[0]
                yh         =  self.make_histogram(y)
                yh         =  yh[0]
                argmax_0   =  np.argmax(yh)
                
            else:
                print('else')
                xh_temp    =  self.make_histogram(x)
                yh_temp    =  self.make_histogram(y)
                xh         =  np.concatenate((xh,xh_temp[0]), axis=0)
                yh         =  np.concatenate((yh,yh_temp[0]))
                argmax     =  np.argmax(yh)
                #yh         = np.roll(yh,argmax_0-argmax)

        xh=xh.reshape((n+1,xh_temp[0].shape[0]))  
        yh=yh.reshape((n+1,yh_temp[0].shape[0]))  

        xh=np.rot90(xh)
        if rot==False:
            return xh,np.rot90(yh)
        elif rot==True:
            return yh,np.rot90(xh)
        
    def change_name(self, new_name, pos):
        self.elements[pos] = new_name 
        
        
    def plot(self,save_img = True, save_directory=False, img_name='test', extension='.png', show_img=False, annotate_OE=False,lim_top=False,lim_side=False):
        dx, dy = self.step_z, self.step
        y, x = np.mgrid[slice(-self.lim, self.lim + dy, dy),
            slice(0, self.yh.shape[1]*self.step_z + dx, dx)]
        print('######################')
        print('Dimension check')
        print('yh shape:  ', self.yh.shape)
        print('xh shape:  ', self.xh.shape)
        print('x shape:    ',x.shape)
        print('y shape:    ',y.shape)

        g=1.5
        plt.figure(self.count_fig)
        fig, (ax1, ax2) = plt.subplots(2,figsize=(6.4*g, 4.8*g))
        pcm=ax1.pcolormesh(x/1000,y,self.xh, cmap='inferno')
        ax1.clear()
        #pcm=ax2.pcolormesh(x/1000,y,self.yh, cmap='inferno')
        ax1.pcolormesh(x/1000,y,np.log(self.xh), cmap='inferno')
        ax2.pcolormesh(x/1000,y,np.log(self.yh), cmap='inferno')
        ax1.set_title('top view')
        ax2.set_title('side view')
        ax2.set_xlabel('[meters]')
        ax1.set_ylabel('Beam Width [mm]')
        ax2.set_ylabel('Beam Width [mm]')
        cbar1=fig.colorbar(pcm,ax=ax1) 
        cbar2=fig.colorbar(pcm,ax=ax2)
        cbar1.set_label('# of rays [a.u.]')#, rotation=-90) 
        cbar2.set_label('# of rays [a.u.]')
        posx=0
        if annotate_OE == True:
            for n, text in enumerate(self.elements):
                posx += self.distances[n]/1000
                if self.distances[n+1]/1000<=1:
                    posy += 2
                
                if lim_top != False:
                    if self.lim >= lim_top[2]:
                        posy =  lim_top[2]
                else:
                    posy =  -self.lim
                
                if self.distances[n+1]/1000<=1:
                    #print('I shift')
                    posy += 2
                    
                ax1.text(posx,posy,text, rotation=45)
                
                if lim_side != False:
                    if self.lim >= lim_side[2]:
                        posy =  lim_side[2]
                else:
                    posy =  -self.lim
                if self.distances[n+1]/1000<=1:
                    #print('I shift')
                    posy += 2
                ax2.text(posx,posy,text, rotation=45)
        if lim_top != False:
            ax1.set_xlim(lim_top[0],lim_top[1])
            ax1.set_ylim(lim_top[2],lim_top[3])
        if lim_side != False:
            ax2.set_xlim(lim_side[0],lim_side[1])
            ax2.set_ylim(lim_side[2],lim_side[3])
        if save_directory != False:
            plt.savefig(os.path.join(save_directory,img_name+extension))
        plt.tight_layout()
        plt.close(0)
        if show_img == True:
            plt.show()
        self.count_fig += 1
            
        return self.xh,self.yh,x/1000,y


