from .simulate import Simulate
from .rml import ObjectElement
from .recipes import BeamWaist

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import sys
    

class PlotBeamwaist():
    '''
    To use this class one needs to trace and export RawRaysOutgoing for each optical element (no image planes)
    '''
    def __init__(self, directory:str, sim:Simulate):
        self.directory = 'RAYPy_Simulation_'+directory
        self._original_directory = directory
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
        self.count_fig        = 0
    
    def simulate_beamline(self, energy:float,/,source:ObjectElement=None,nrays:int=None, force:bool=False):
        #sim.params,sim.exports, sim.simulation_name = ResolvingPower(energy_range, elisa.DetectorAtFocus,ES,cff)
        rp = BeamWaist(energy,source=source,nrays=nrays,sim_folder=self._original_directory)

        # test resolving power simulations
        self._sim.run(rp, multiprocessing=5, force=force)
        #self._sim.beamwaist_simulation(energy,source=source,nrays=nrays,sim_folder=self._original_directory, force=force)
    
    def _parse_beamline_elements(self, debug=False):
        self.element_names_list = []
        self.distance_list=[]
        self.rotation_list=[]
        for ind, oe in enumerate(self._sim.rml.beamline._children):
                for par in oe:
                    try:
                        # append to distances
                        if ind != 0:
                            self.distance_list.append(float(par.worldPosition.z.cdata)-sum(self.distance_list))                            
                        else:    
                            self.distance_list.append(float(par.worldPosition.z.cdata))
                        # append to rotation
                        if ind == 0:
                            self.rotation_list.append(False)
                        elif hasattr(par, "azimuthalAngle"):
                            if par.azimuthalAngle.cdata == '0' or par.azimuthalAngle.cdata=='180':
                                self.rotation_list.append(False)
                            elif par.azimuthalAngle.cdata == '90' or par.azimuthalAngle.cdata=='270':
                                self.rotation_list.append(True)
                            else: 
                                raise ValueError('Only beamline elements with azimuthal angle 0,90,180,270 are supported', oe.name, par.azimuthalAngle.cdata)
                        else:
                            self.rotation_list.append(False)
                        # append to element names list, only if it is not an imageplane
                        #if oe.get_attribute('type') != 'ImagePlaneBundle' and oe.get_attribute('type') != 'ImagePlane':
                        self.element_names_list.append(oe.attributes().original()['name'])
                    except AttributeError:
                        print(oe.attributes().original()['name'], par.worldPosition.z.cdata)
                        pass
        if debug:
            print('DEBUG:: element_names_list', self.element_names_list)
            print('DEBUG:: distance_list', self.distance_list)
            print('DEBUG:: rotation_list', self.rotation_list)


    def trace_beamwaist(self, save_results:bool=True, element_names_list:list=None):
        self._parse_beamline_elements()
        # I overwrite the names for the moment, since I can not access them automatically
        if element_names_list != None:
            self.element_names_list=element_names_list
        for ind in range(len(self.element_names_list)):
            if ind+1 != len(self.element_names_list):
                self.add_element(name=self.element_names_list[ind],
                                z=self.distance_list[ind+1],
                                rot=self.rotation_list[ind])
        if save_results == True:
            self.save_results()
    
    def reduce_Nrays(self,factor):
        self.factor = factor
        
    def load_previous_results(self, element_names_list=None):
        self._parse_beamline_elements()
        if element_names_list != None:
            self.element_names_list=element_names_list
        start1  = time.time()
        print('Load results...')
        self.xh=np.loadtxt(os.path.join(self.directory,'xh.txt'))
        self.yh=np.loadtxt(os.path.join(self.directory,'yh.txt'))
        stop = time.time()
        print('time:', np.round(stop-start1,2),'s')
        
    def save_results(self):
        np.savetxt(os.path.join(self.directory, 'xh.txt'), self.xh)
        np.savetxt(os.path.join(self.directory, 'yh.txt'), self.yh)
            
    def add_element(self,name,z,rot=False):
        start1  = time.time()
        z       = np.arange(0,z+self.step_z,self.step_z)

        if self.previous_results == False:
            print('Tracing '+name)
            
            rays    = np.loadtxt(os.path.join(self.directory,'round_0', 
                                         '0_'+name
                                         +'-RawRaysOutgoing.csv'), 
                            skiprows=2)
            if self.factor != False:
                max_n_rays = int(rays.shape[0]/self.factor)
            if max_n_rays < 100:
                sys.exit('Set a lower reduction factor, there are no more rays to plot!')
            rays = rays[0:max_n_rays]
            
            
            if self.count_el == 0:
                self.xh,self.yh   = self.trace(z,rays,rot)
                #print("DEBUG:: self.xh.shape, self.yh.shape:",self.xh.shape, self.yh.shape)
            else:
                txh,tyh   = self.trace(z,rays,rot, name)
            if rot == True:
                txh=np.rot90(txh)
                tyh=np.rot90(tyh)
            if self.count_el != 0:
                #print("DEBUG:: txh.shape, tyh.shape:",txh.shape, tyh.shape)
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
        
        
    def trace(self,z,rays,rot=False, element=None):
        for n,z in enumerate(z):
            x,y      = self.trace_pos(rays,z)
            shiftx   = np.average(x)
            shifty   = np.average(y)
            y        = y-shifty
            x        = x-shiftx
            if n==0:
                xh         =  self.make_histogram(x)
                xh         =  xh[0]
                yh         =  self.make_histogram(y)
                yh         =  yh[0]
                argmax_0   =  np.argmax(yh)
                
            else:
                xh_temp    =  self.make_histogram(x)
                yh_temp    =  self.make_histogram(y)
                xh         =  np.concatenate((xh,xh_temp[0]), axis=0)
                yh         =  np.concatenate((yh,yh_temp[0]))
        xh=xh.reshape((n+1,xh_temp[0].shape[0]))  
        yh=yh.reshape((n+1,yh_temp[0].shape[0]))  

        xh=np.rot90(xh)
        if rot==False:
            return xh,np.rot90(yh)
        elif rot==True:
            return yh,np.rot90(np.flip(xh)) # no idea why I have to flip this
        
    def change_name(self, new_name, pos):
        self.element_names_list[pos] = new_name 
        
        
    def plot(self,save_img = True, img_name='test', extension='.png', show_img=False, annotate_OE=False,lim_top=False,lim_side=False, debug=False):
        dx, dy = self.step_z, self.step
        xmax = self.yh.shape[1]*self.step_z + dx
        y, x = np.mgrid[slice(-self.lim, self.lim + dy, dy),
            slice(0,xmax , dx)]
        x=x[:,:-1]
        y=y[:,:-1]
        if debug:
            print('######################')
            print('Dimension check')
            print('yh shape:  ', self.yh.shape)
            print('xh shape:  ', self.xh.shape)
            print('x shape:    ',x.shape)
            print('y shape:    ',y.shape)
            print('x :    ',x)
            print('self.yh.shape[1], self.step_z, dx', self.yh.shape, self.yh.shape[1], self.step_z, dx)
            print('self.yh.shape[1]*self.step_z + dx',self.yh.shape[1]*self.step_z + dx)
            print('DEBUG:: self.distances', self.distances)
            print('DEBUG:: self.distance_list', self.distance_list)
            print('DEBUG:: self.elements', self.elements)
            print('DEBUG:: self.elements_name_list', self.element_names_list)

        g=1.5
        plt.figure(self.count_fig)
        fig, (ax1, ax2) = plt.subplots(2,figsize=(6.4*g, 4.8*g))
        pcm=ax1.pcolormesh(x/1000,y,self.xh, cmap='inferno')
        ax1.clear()
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
        xtick_pos = []
        xtick_label = []
        # put correct ticks and labels
        plot_length = xmax/1000
        beamline_length = sum(self.distance_list)/1000
        beamline_el_pos = np.cumsum(self.distance_list)/1000
        xtick_pos = (beamline_el_pos*plot_length)/beamline_length
        xtick_label = np.round(beamline_el_pos,2)

        # label the elements
        if annotate_OE == True:
            for ind, text in enumerate(self.element_names_list):
                if ind !=len(self.element_names_list):
                    posy =  -self.lim
                    posx = xtick_pos[ind]

                if ind<len(self.element_names_list)-1:
                    if (xtick_pos[ind+1]-xtick_pos[ind])<1:
                        posy += 3
                ax1.text(posx,posy,text, rotation=60)
                ax2.text(posx,posy,text, rotation=60)
        
        # remove xticks and labels which are too close to eaeachhc other
        for ind in range(xtick_pos.shape[0]-2, 1, -1):
            if ind>0:# < xtick_pos.shape[0]-1:
                if np.abs(xtick_pos[ind]-xtick_pos[ind+1])<1:
                    xtick_label = np.delete(xtick_label,ind)
                    xtick_pos = np.delete(xtick_pos,ind)

        if debug:
            print('DEBUG:: plot_length', plot_length)
            print('DEBUG:: self.distance_list', self.distance_list)
            print('DEBUG:: beamline_length', beamline_length)
            print('DEBUG:: beamline_el_pos', beamline_el_pos)
            print('DEBUG:: xtick_label', xtick_label)
            print('DEBUG:: xtick_pos', xtick_pos)
        ax1.set_xticks(xtick_pos)
        ax1.set_xticklabels(xtick_label, rotation = 45, ha="right")
        ax2.set_xticks(xtick_pos)
        ax2.set_xticklabels(xtick_label, rotation = 45, ha="right")

        if lim_top != False:
            ax1.set_xlim(lim_top[0],lim_top[1])
            ax1.set_ylim(lim_top[2],lim_top[3])
        if lim_side != False:
            ax2.set_xlim(lim_side[0],lim_side[1])
            ax2.set_ylim(lim_side[2],lim_side[3])
        if save_img == True:
            plt.savefig(os.path.join(self.directory,img_name+extension))
        plt.tight_layout()
        plt.close(0)
        if show_img == True:
            plt.show()
        self.count_fig += 1
            
        return self.xh,self.yh,x/1000,y


