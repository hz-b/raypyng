import numpy as np

from raypyng.wave_helper import WaveHelper

WH = WaveHelper('WAVE', 3, 'U49')

WH.report_available_energies(verbose=True)

energies = np.arange(80,570,10)
matchin_en_list = WH.convert_energies_to_file_list(1,energies)

for ind, en in enumerate(matchin_en_list):
    print(f"Energy: {en}, filename:{matchin_en_list[ind]}")


