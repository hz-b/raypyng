import sys
sys.path.insert(1, '../src')

import numpy as np

from raypyng.wave_helper import WaveHelper

v = WaveHelper('WAVE', 3, 'U49')

v.report_available_energies(verbose=True)

matching_en = np.arange(80,570,10)
matchin_en_list = v.convert_energies_to_file_list(1,matching_en)

non_matching_en = np.arange(81,570,10)
non_matchin_en_list = v.convert_energies_to_file_list(1,non_matching_en)

# print(f"matchin_en_list {matchin_en_list}")
