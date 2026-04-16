import numpy as np

from raypyng.wave_helper import WaveHelper

WH = WaveHelper('WAVE', 3, 'U49')

WH.report_available_energies(verbose=True)

energies = np.arange(80,570,10)
matching_en_list = WH.convert_energies_to_file_list(1,energies)

for energy_file in matching_en_list:
    print(f"filename: {energy_file}")

