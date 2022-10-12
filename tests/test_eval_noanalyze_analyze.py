import numpy as np
import matplotlib.pyplot as plt

noanalyze_det = np.loadtxt('RAYPy_Simulation_test_noAnalyze/DetectorAtFocus.dat')

energy    = np.arange(200, 10201,1000)

#plotting

fig, (axs) = plt.subplots(2, 2,figsize=(10,10))

ax = axs[0,0]
ax.plot(energy, noanalyze_det[:,0], 'b', linestyle='solid', label='noAnalyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Source photon flux Flux [ph/s/0.1%bw*0.1A]')
ax.set_title('Photons produced by the source')

ax = axs[0,1]
ax.plot(energy, noanalyze_det[:,1], 'b', linestyle='solid', label='noAnalyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Flux [n_rays]')
ax.set_title('Photons reaching the detector [a.u.]')


plt.show()