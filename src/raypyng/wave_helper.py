import os 
from natsort import natsorted
import re

import numpy as np

class WaveHelper():
    """Explore WAVE simulation folder and gives an easy way to convert energies into filenames

    The class expects the WAVE simulations to be stored in a folder called WAVE. 
    For instance for an undulator called 'U49' and harmonic=3, this filestructure is expected:
    * Wave
        *U49H1allrayfiles
        *U49H3allrayfiles
        *U49H5allrayfiles

        Args:
            wave_folder_path (str): the path to the WAVW folder where the WAVE simulations are stored
            harmonics (int): the number of harmonics present.(If harmonics=2, simulations for 1st and 3rd should exist)
            undulator (str): the undulator name as indicated in the simulation folders
        """    
    
    def __init__(self, wave_folder_path:str,harmonics:int, undulator:str,**kwargs) -> None:   
            
        self.wave_folder_path = wave_folder_path
        self.harmonics = harmonics
        self.undulator = undulator
        
        self._harmonic_to_folders_dict = {}
        self._harmonic_to_energy_files_dict = {}
        self._harmonic_to_energy_dict = {}
        self._harmonic_to_energies_array = {}
        self.energies_to_file_dict = {}



    def _find_harmonics_folder(self):
        folders_list = []
        wave_folder_content = os.listdir(self.wave_folder_path)
        for f in wave_folder_content:
            f_path = os.path.join(self.wave_folder_path,f)
            if f.startswith(self.undulator) and os.path.isdir(f_path) and f.endswith('allrayfiles'):
                folders_list.append(f_path)
        
        for ind, f in enumerate(sorted(folders_list)):
            self._harmonic_to_folders_dict[1+(ind*2)] = f

    def _find_energies(self):
        for harm in self._harmonic_to_folders_dict.keys():
            file_list = []
            energies_list = []
            for file in natsorted(os.listdir(self._harmonic_to_folders_dict[harm])):
                if file.endswith('fo.dat'):
                    file_list.append(file)
                    res = re.search('_(.*)eV_', file)
                    energies_list.append(int(res.group(1)))
            self._harmonic_to_energy_files_dict[harm] = file_list
            self._harmonic_to_energy_dict[harm] = energies_list
            
    
    def _make_numpy_array_from_energies(self):
        for harm in self._harmonic_to_energy_dict.keys():
            start = self._harmonic_to_energy_dict[harm][0]
            stop  = self._harmonic_to_energy_dict[harm][-1]
            step  = self._harmonic_to_energy_dict[harm][1]-self._harmonic_to_energy_dict[harm][0]
            if (np.arange(start, stop+step, step)== np.array(self._harmonic_to_energy_dict[harm])).all:
                self._harmonic_to_energies_array[harm] = np.arange(start, stop+step, step)
            else:
                self._harmonic_to_energies_array = False
                break

    def _make_energy_to_file_dict(self):
        for harm in self._harmonic_to_folders_dict.keys(): 
            energies_keys = self._harmonic_to_energy_dict[harm]
            energy_files = []
            for f in self._harmonic_to_energy_files_dict[harm]:
                energy_files.append(os.path.join(self._harmonic_to_folders_dict[harm], f))
            self.energies_to_file_dict[harm] = dict(zip(energies_keys, energy_files))


    def _explore_wave_folder(self, debug=False):
        self._find_harmonics_folder()
        self._find_energies()
        self._make_energy_to_file_dict()
        if debug:
            print(f"self._harmonic_to_folders_dict {self._harmonic_to_folders_dict}")
            print("")
            print("")
            print(f"self._harmonic_to_energy_files_dict {self._harmonic_to_energy_files_dict}")
            print("")
            print("")
            print(f"self._harmonic_to_energy_dict {self._harmonic_to_energy_dict}")
            print("")
            print("")
            print(f"self._harmonic_to_energies_array {self._harmonic_to_energies_array}")

    def report_available_energies(self, verbose=True):
        """Report about the availbale energies and explore the WAVE folder


        Args:
            verbose (bool, optional): If Ture a report about the neergie is printed. Defaults to True.
        """        
        self._explore_wave_folder()
        if verbose:
            print(f"I found the following harmonics: {self._harmonic_to_energy_dict.keys()}")
            if self._harmonic_to_energies_array is not False:
                print('the energy points for each harmonic are equally spaced')
                for harm in self._harmonic_to_energy_dict.keys():
                    print(f"Harmonic number {harm}, available energies:")
                    print(f"start {self._harmonic_to_energy_dict[harm][0]}")
                    print(f"stop {self._harmonic_to_energy_dict[harm][-1]}")
                    print(f"step {self._harmonic_to_energy_dict[harm][1]-self._harmonic_to_energy_dict[harm][0]}")
            else:
                for harm in self._harmonic_to_energy_dict.keys():
                    print(f"Harmonic number {harm}, available energies:")
                    print(self._harmonic_to_energy_dict[harm])

    def convert_energies_to_file_list(self, harmonic:int, energies:list):
        """Takes the harmonic and a list of energies and returns the files location

        Args:
            harmonic (int): the harmonic that you want to have
            energies (list): list of int, the x-ray energies

        Raises:
            ValueError: If an energy is not present in the WAVE simulation folder.

        Returns:
            list: list of absolute paths for each energy given as an input
        """        
        en_list = []
        en_to_file_dict = self.energies_to_file_dict[harmonic]
        for en in energies:
            if en in en_to_file_dict.keys():
                en_list.append(en_to_file_dict[en])
            else:
                raise ValueError(f"There is no file for harmonic {harmonic} energy {en}")
        return en_list

    
            

        
            



