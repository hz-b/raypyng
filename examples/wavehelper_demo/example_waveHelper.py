import os

import numpy as np

from raypyng.wave_helper import WaveHelper

this_file_dir = os.path.dirname(os.path.realpath(__file__))
WH = WaveHelper(os.path.join(this_file_dir, '..', 'WAVE'), 3, 'U49')

WH.report_available_energies(verbose=True)

energies = np.arange(80,570,10)
matching_en_list = WH.convert_energies_to_file_list(1,energies)

for energy_file in matching_en_list:
    print(f"filename: {energy_file}")

