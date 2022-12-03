import os 
import numpy as np



################################################################
class WaveHelper():
    
    def __init__(self, wave_folder_path:str,harmonics:int, undulator,**kwargs) -> None:     
        self.wave_folder_path = wave_folder_path
        self.harmonics = harmonics
        self.undulator = undulator

    def _find_harmonics_folder(self):
        self.folders_dict = {}
        folders_list = []
        wave_folder_content = os.listdir(self.wave_folder_path)
        for f in wave_folder_content:
            f_path = os.path.join(self.wave_folder_path,f)
            if f.startswith(self.undulator) and os.path.isdir(f_path) and f.endswith('allrayfiles'):
                folders_list.append(f_path)
        
        for ind, f in enumerate(sorted(folders_list)):
            self.folders_dict[1+(ind*2)] = f

    def _find_energy_files(self):
        


    def _explore_wave_folder(self):
        self._find_harmonics_folder()
        self._find_energy_files()



