import numpy as np
import matplotlib.pyplot as plt

from raypyng.postprocessing import PostProcessAnalyzed

# extract noanalyze data
noanalyze_det = np.loadtxt('RAYPy_Simulation_test_noAnalyze/DetectorAtFocus.dat')
energy    = np.loadtxt("RAYPy_Simulation_test_noAnalyze/input_param_Dipole_photonEnergy.dat")

# extract analyze data
p = PostProcessAnalyzed()
flux, flux_percent, flux_dipole = p.retrieve_flux_beamline(folder_name="RAYPy_Simulation_test_Analyze",
                                                            source="Dipole",
                                                            oe = "DetectorAtFocus",
                                                            nsimulations = energy.shape[0],
                                                            current=0.1)

bw,foc_x,foc_y = p.retrieve_bw_and_focusSize(folder_name="RAYPy_Simulation_test_Analyze",
                                            oe="DetectorAtFocus",
                                            nsimulations=energy.shape[0],
                                            rounds=1)


#plotting

fig, (axs) = plt.subplots(4, 2,figsize=(10,10))

ax = axs[0,0]
ax.plot(energy, noanalyze_det[:,0], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, flux_dipole, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Source photon flux Flux [ph/s/0.1%bw*0.1A]')
ax.set_title('Photons produced by the source')

ax = axs[0,1]
ax.plot(energy, noanalyze_det[:,1], 'b', linestyle='solid', label='noAnalyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Flux [n_rays]')
ax.set_title('Nrays reaching the detector')

ax = axs[1,0]
ax.plot(energy, noanalyze_det[:,2], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, flux_percent, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Rays [%]')
ax.set_title('Percentage Rays reaching the detector')

ax = axs[1,1]
ax.plot(energy, noanalyze_det[:,3], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, flux, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Photon Flux [ph/s/0.1%bw*0.1A]')
ax.set_title('Photon Flux at the detector')

ax = axs[2,0]
ax.plot(energy, noanalyze_det[:,4], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, bw, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('Bandwidth [eV]')
ax.set_title('Bandwidth')

ax = axs[2,1]
ax.plot(energy, noanalyze_det[:,5], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, foc_x, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('FWHM [a.u.]')
ax.set_title('Horizontal Focus')

ax = axs[3,0]
ax.plot(energy, noanalyze_det[:,6], 'b', linestyle='solid', label='noAnalyze')
ax.plot(energy, foc_y, 'r', linestyle='dashed', label='Analyze')
ax.legend()
ax.set_xlabel('Energy [eV]')
ax.set_ylabel('FWHM [a.u.]')
ax.set_title('Vertical Focus')

plt.tight_layout()
plt.savefig("plot_comparison_analyze_NoAnalyze_modes.png")
plt.show()

