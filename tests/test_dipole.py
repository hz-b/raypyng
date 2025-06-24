import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from raypyng import Dipole

magnetic_fields = np.array([0.6, 1.3, 2.0, 3.0])  # Tesla
energy_min=1 # eV
energy_max=10000 # eV
energy_step=100 #  eV
energy_eV = np.arange(energy_min, energy_max + energy_step, energy_step)
dip = Dipole(magnetic_field_T=magnetic_fields,
                                beam_energy_GeV=2.5,
                                current_A=0.1)
fluxes = dip.calculate_spectrum(energy_eV)
print(dip)

bending_radii = 3.335 * 2.5 / magnetic_fields

fig, ax = plt.subplots(figsize=(12, 10))
for index, radius in enumerate(bending_radii): 
    flux = pd.read_csv(os.path.join('RAYPy_Simulation_Dipole', 'Dipole_RawRaysOutgoing.csv'))
    filtered_flux = flux[np.abs(flux['Dipole.bendingRadius'] - radius) <= 0.1]
    filtered_flux['PhotonEnergy']
    filtered_flux['PhotonFlux']

    ax.plot(filtered_flux['PhotonEnergy'],
                filtered_flux['PhotonFlux'],
                label=f'RAY {magnetic_fields[index]} T')
    ax.plot(energy_eV, fluxes[index], linestyle='dotted', label='RayPyNG')
ax.set_yscale('log')
ax.set_yscale('log')
ax.grid(True, which="both", ls="--")
ax.set_xlabel("Photon Energy [eV]")
ax.set_ylabel(f"Photon Flux [photons/s/0.1A/0.1%BW]")
ax.set_title("SR Bending Magnet Spectrum for Different Magnetic Fields")
plt.legend()

fig.tight_layout()
plt.savefig('Dipole.png')
plt.show()
