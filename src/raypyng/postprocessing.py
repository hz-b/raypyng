from importlib.resources import path
import numpy as np
import os
import warnings
from natsort import natsorted, ns

from .rml import RMLFile


def prepend_line(file_name, line):
    """ Insert given string as a new line at the beginning of a file """
    # define name of temporary dummy file
    dummy_file = file_name + '.bak'
    # open original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Write given line to the dummy file
        write_obj.write(line + '\n')
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line[:-2])
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)



class RayProperties(np.ndarray):
    def __new__(cls,input=None,/,filename=None) -> None:
        dt_names = ['SourcePhotonFlux', 'NumberRaysSurvived', 'PercentageRaysSurvived', 'PhotonFlux', 'Bandwidth', 'HorizontalFocusFWHM', 'VerticalFocusFWHM']
        dt_formats = [float for n in dt_names]
        dt = np.dtype({'names':dt_names, 'formats':dt_formats})

        if input is None:
            if filename is None:
                input_array = np.zeros(1, dtype=dt)
            else:
                print("DEBUG:: opening filename", filename)
                input_array = np.genfromtxt(filename, dtype=float, delimiter='\t', names=True)
                print("DEBUG:: inoput_array", input_array)
        else:
            input_array = input.copy()
            input_array.dtype = dt

        obj = np.asarray(input_array).view(cls)
        return obj

    def save(self,filename):
        tmp = self.copy()
        if tmp.shape[0]>1:
            tmp.dtype = float
        print(f"DEBUG:: saving {filename}:\n{tmp}\n============")
        np.savetxt(filename,tmp,delimiter='\t',header="\t".join(self.dtype.names))
        

    def concat(self,other):
        return RayProperties(np.vstack((self,other)))


class PostProcess():
    """class to post-process the data. 

    It works only if the exported data are RawRaysOutgoing
    """
    def __init__(self) -> None:
    
        self.format_saved_files = '.dat'
        self.source = None
        pass

    def _list_files(self,dir_path:str, end_filename:str):
        """List all the files in dir_path ending with end_filename

        Args:
            dir_path (str): path to a folder
            end_filename (str): the listed files end with end_filename

        Returns:
            res (list): list of files in dir_path ending eith end_filename
        """        
        # list to store files
        res = []
        for file in os.listdir(dir_path):
            # check only text files
            if file.endswith(end_filename):
                res.append(os.path.join(dir_path,file))
        return natsorted(res, alg=ns.IGNORECASE)

    def _extract_bandwidth_fwhm(self,rays_bw:np.array):
        """calculate the fwhm of the rays_bw.

        Args:
            rays_bw (np:array): the energy of the x-rays

        Returns:
            float: fwhm
        """        
        return 2.3555*np.std(rays_bw)

    def _extract_focus_fwhm(self,rays_pos:np.array):
        """calculate the fwhm of rays_pos

        Args:
            rays_pos (np.array): contains positions of the x-rays

        Returns:
            float: fwhm
        """        
        return 2.3555*np.std(rays_pos)

    def _extract_intensity(self,rays:np.array):
        """calculate how many rays there are

        Args:
            rays (np.array): contains rays information
        """        
        return(rays.shape[0])
    
    def _save_file(self, filename:str, array:np.array, header:str=None):
        """This function is used to save files.

        Args:
            filename (str): file name(path)
            array (np.array): array to save 
            header (str): header for the file
        """        
        if header != None:
            np.savetxt(filename+self.format_saved_files,array, header=header)
        else:
            np.savetxt(filename+self.format_saved_files,array)

    def _load_file(self,filepath):
        """Load file and returns the array

        Args:
            filepath (str): the path to the file to load

        Returns:
            arr (np.array): The loaded numpy array
        """        
        arr = np.loadtxt(filepath)
        return arr
    
    def extract_nrays_from_source(self, rml_filename):
        """Extract photon flux from rml file, find source automatically

        Args:
            rml_filename (str): the rml file to use to extract the photon flux

        Returns:
            str: the photon flux
        """        
        s = RMLFile(rml_filename)
        for oe in s.beamline.children():
                if hasattr(oe,"photonFlux"):
                    self.source = oe
                    break
        return self.source.photonFlux.cdata, self.source.numberRays.cdata
    
    def postprocess_RawRays(self,exported_element:str=None, exported_object:str=None, dir_path:str=None, sim_number:str=None, rml_filename:str=None):
        """ PostProcess rountine of the RawRaysOutgoing extracted files.

        The method looks in the folder dir_path for a file with the filename:
        :code:`filename = os.path.join(dir_path,sim_number+exported_element + '-' + exported_object+'.csv')`
        for each file it calculates the number of rays, the bandwidth, and the horizontal and vertical focus size,
        it saves it in an array that is composed by :code:`[n_rays,bandwidth,hor_focus,vert_focus]`, that is then saved to
        :code:`os.path.join(dir_path, sim_number+exported_element+'_analyzed_rays.npy')`
        
        Args:
            exported_element (list, optional): a list of containing the exported elements name as str. Defaults to None.
            exported_object (str, optional): the exported object, tested only with RawRaysOutgoing. Defaults to None.
            dir_path (str, optional): the folder where the file to process is located. Defaults to None.
            sim_number (str, optional): the prefix of the file, that is the simulation number with a _prepended, ie `0_`. Defaults to None.
        """        
        source_photon_flux, source_n_rays  = self.extract_nrays_from_source(rml_filename)
        
        source_photon_flux = float(source_photon_flux)
        source_n_rays      = float(source_n_rays)
        filename = os.path.join(dir_path,sim_number+exported_element + '-' + exported_object+'.csv')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            #rays = np.loadtxt(filename, skiprows=2)
            rays = np.genfromtxt(filename, dtype=float, delimiter='\t', names=True,skip_header=1)
        ray_properties = RayProperties()
        if rays.shape[0]==0: # if no rays survived
            # source photon flux
            ray_properties['SourcePhotonFlux'] = source_photon_flux
            pass
        else:
            # source photon flux
            ray_properties['SourcePhotonFlux'] = source_photon_flux
            # number of rays reaching the oe
            ray_properties['NumberRaysSurvived'] = self._extract_intensity(rays)
            # percentage of survived photons
            ray_properties['PercentageRaysSurvived'] = ray_properties['NumberRaysSurvived']/source_n_rays*100
            # photon flux reaching the oe
            ray_properties['PhotonFlux'] = source_photon_flux/100*ray_properties['PercentageRaysSurvived']
            # bandwidth of the rays reaching the oe
            ray_properties['Bandwidth'] = self._extract_bandwidth_fwhm(rays[f'{exported_element}_EN'])
            # horizontal focus
            ray_properties['HorizontalFocusFWHM'] = self._extract_focus_fwhm(rays[f'{exported_element}_OX'])
            # vertical focus
            ray_properties['VerticalFocusFWHM'] = self._extract_focus_fwhm(rays[f'{exported_element}_OY'])
        
        new_filename = os.path.join(dir_path, sim_number+exported_element+'_analyzed_rays.dat')
        #self._save_file(new_filename, ray_properties)
        ray_properties.save(new_filename)
        return 

    def cleanup(self,dir_path:str=None, repeat:int=1, exp_elements:list=None):
        """Reads all the results of the postprocessing process and summarize 
        them in a single file for each exported object.
        
        This functions reads all the temporary files created by :code:`self.postptocess_RawRays()`
        saves one file for each exported element in dir_path, and deletes the temporary files.
        If more than one round of simulations was done, the values are averaged.

        Args:
            dir_path (str, optional): The path to the folder to cleanup. Defaults to None.
            repeat (int, optional): number of rounds of simulations. Defaults to 1.
            exp_elements (list, optional): the exported elements names as str. Defaults to None.
        """        
        header = "SourcePhotonFlux\t\t NumberRaysSurvived\t\t  PercentageRaysSurvived   PhotonFlux\t\t\t\tBandwidth\t\t\t\t HorizontalFocusFWHM\t  VerticalFocusFWHM"
        for d in exp_elements:
            for r in range(repeat):
                dir_path_round=os.path.join(dir_path,"round_"+str(r))
                files = self._list_files(dir_path_round, d[0]+"_analyzed_rays"+self.format_saved_files)
                for f_ind, f in enumerate(files):
                    if r == 0 and f_ind==0:
                        #analyzed_rays = self._load_file(f)
                        #analyzed_rays = np.reshape(analyzed_rays,(1,analyzed_rays.shape[0]))
                        analyzed_rays = RayProperties(filename=f)
                    elif r==0 and f_ind!=0:
                        #tmp=self._load_file(f)
                        #tmp = np.reshape(tmp,(1,tmp.shape[0]))
                        tmp = RayProperties(filename=f)
                        analyzed_rays = analyzed_rays.concat(tmp)
                    elif r>=1:
                        #tmp=self._load_file(f)
                        #tmp=tmp.reshape((tmp.shape[0]))
                        tmp = RayProperties(filename=f)
                        print(f"DEBIG:: r>=1 :: analyzed_rays={analyzed_rays}, tmp={tmp}")
                        #analyzed_rays[f_ind] += tmp
                        for n in analyzed_rays.dtype.names: analyzed_rays[n] += tmp[n]
                    else:
                        pass
            fn = os.path.join(dir_path, d[0])
            for n in analyzed_rays.dtype.names: analyzed_rays[n] /= repeat
            #self._save_file(fn,analyzed_rays,header=header)
            analyzed_rays.save(f"{fn}.dat")

class PostProcessAnalyzed():
    """class to analyze the data exported by RAY-UI
    """
    def __init__(self) -> None:
        pass

    def retrieve_flux_beamline(self, folder_name,source,oe,nsimulations,rounds=1,current=0.3):
        """Extract the flux from object ScalarBeamProperties and from source ScalarElementProperties.

        This function takes as arguments the name of the 
        simulation folder, the exported objet in RAY-UI and there
        number of simulations and returns the flux at the optical element in 
        percentage and in number of photons, and the flux produced
        by the dipole.
        It requires ScalarBeamProperties to be exported for the desired optical element,
        if the source is a dipole it requires ScalarElementProperties to be exported for the Dipole

        Args:
            folder_name (str): the path to the folder where the simulations are
            source (str): the source name
            oe (str): the optical element name
            nsimulations (int): the number of simulations
            rounds (int): the number of rounds of simulations
            current (float, optional): the ring current in Ampere. Defaults to 0.3.

        Returns:
            if the source is a Dipole:
                photon_flux (np.array) : the photon flux at the optical element
                flux_percent (np.array) : the photon flux in percentage relative to the source
                source_Photon_flux (np.array) : the photon flux of the source
            else:
                flux_percent (np.array) : the photon flux in percentage relative to the source
        """        
        scale_factor = current/0.1
        flux_percent = np.zeros(nsimulations)
        if source == 'Dipole':
            flux         = np.zeros(nsimulations)
            flux_dipole  = np.zeros(nsimulations)
        for n in range(nsimulations):
            try:
                for r in range(rounds):
                    temp = np.loadtxt(folder_name+'/round_'+str(r)+'/'+str(n)+'_'+oe+'-ScalarBeamProperties.csv',skiprows = 2)
                    flux_percent[n] += temp[25]/rounds
                    if source == 'Dipole':
                        dipole_abs_flux = np.loadtxt(folder_name+'/round_'+str(r)+'/'+str(n)+'_Dipole-ScalarElementProperties.csv',skiprows = 2)
                        flux[n]         += (dipole_abs_flux[12]*temp[25]/100)/rounds
                        flux_dipole[n]  += dipole_abs_flux[12]/rounds
                
            except OSError:
                print('######################')
                print(n, 'NOT FOUND:\n'+folder_name+'/round_'+str(r)+'/'+str(n)+'_'+oe+'-ScalarBeamProperties.csv')
                continue
        flux_percent = np.array(flux_percent)
        if source == 'Dipole':
            flux = np.array(flux)
            flux_dipole = np.array(flux_dipole)
            return flux*scale_factor, flux_percent, flux_dipole*scale_factor
        return flux_percent*scale_factor

    def retrieve_bw_and_focusSize(self,folder_name:str,oe:str,nsimulations:int,rounds:int):
        """Extract the bandwidth and focus size from ScalarBeamProperties of an object.

        Args:
            folder_name (str): the path to the folder where the simulations are 
            oe (str): the optical element name
            nsimulations (int): the number of simulations
            rounds (int): the number of rounds of simulations

        Returns:
            bw np.array: the bandwidth
            foc_x np.array: the horizontal focus
            foc_y np.array: the vertical focus
        """        
        bw_ind        =10
        fx_ind        =4
        fy_ind        =7
        bw            = np.zeros(nsimulations)
        foc_x         = np.zeros(nsimulations)
        foc_y         = np.zeros(nsimulations)
        n0=0
        for j in range(rounds):
            for n in range(nsimulations):
                try:
                    temp = np.loadtxt(folder_name+'/round_'+str(j)+
                                    '/'+str(n)+'_'+oe+'-ScalarBeamProperties.csv',
                                    skiprows = 2)
                    bw[n]     += (temp[bw_ind])/rounds
                    foc_x[n]  += (temp[fx_ind])/rounds
                    foc_y[n]  += (temp[fy_ind])/rounds
                    if n0==(nsimulations-1):
                        n0=0
                    else:
                        n0+=1
                    
                except OSError:
                    print('######################')
                    print('NOT FOUND:\n'+folder_name+'/round_'+str(j)+
                                    '/'+str(n)+'_'+oe+'-ScalarBeamProperties.csv')
                    bw[n]     += 0
                    foc_x[n]  += 0
                    foc_y[n]  += 0
        return bw,foc_x,foc_y

    def moving_average(self, x, w):
        """Computes the morivng average with window w on the array x

        Args:
            x (array): the array to average
            w (int): the window for the moving average

        Returns:
            np.array: the x array once the moving average was applied
        """        
        if w == 0:
            return x
        return np.convolve(x, np.ones(w), 'valid') / w


