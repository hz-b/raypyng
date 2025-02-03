import numpy as np
from raypyng.diodes import AXUVDiode, GaASPDiode

axuv_diode = AXUVDiode()
print('AXUV Diode')
energy = np.array([1, 500, 1500, 2000, 2500])  # example energies in eV
n_photons = np.array([1e12, 1e12, 1e12, 2e12, 1.5e12])  # example number of photons
try:
    current = axuv_diode.convert_photons_to_amp(energy, n_photons)
    for e, p, c in zip(energy, n_photons, current):
        print(f"Energy: {e} eV, Photons: {p:.1e}, Current: {c:.3e} A")
except ValueError as e:
    print(e)

print()

print('GaAsP Diode')
gaasp_diode = GaASPDiode()
# Assuming same energy and photon values for example purposes
try:
    current = gaasp_diode.convert_photons_to_amp(energy, n_photons)
    for e, p, c in zip(energy, n_photons, current):
        print(f"Energy: {e} eV, Photons: {p:.1e}, Current: {c:.3e} A")
except ValueError as e:
    print(e)