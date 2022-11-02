import unittest

import numpy as np
import os
import matplotlib.pyplot as plt
import shutil

import pathlib as pl

import sys
sys.path.insert(1, '../src')

from raypyng.postprocessing import PostProcessAnalyzed
from raypyng.simulate import Simulate

def compare_two_arrays(a,b, tol=10):
    equal= True
    for ind, _ in enumerate(a):
        #print(f"{a[ind]}, {b[ind]} ")
        perc_diff = np.abs(a[ind]-b[ind])/((a[ind]+b[ind])/2)*100
        #print(f'perc_diff {perc_diff}')
        if perc_diff > tol:
            equal = False
            print(f"perc_diff {perc_diff}")
        #print(f"equal {equal}")
    return equal



class TestNoAnalyze(unittest.TestCase):
    force = False
    nrays = 100000
    fig, (axs) = plt.subplots(3, 2,figsize=(10,10))
    
    def test0_Flux_simulations(self):
        """\n Test raypyng Analysis vs RAY-UI Analysis\n
        """
        # dirpath = "RAYPy_Simulation_test_NoAnalyze_comparison"
        # if os.path.exists(dirpath) and os.path.isdir(dirpath):
        #     shutil.rmtree(dirpath)
            
        
        this_file_dir=os.path.dirname(os.path.realpath(__file__))
        rml_file = os.path.join(this_file_dir,'rml/elisa.rml')

        sim = Simulate(rml_file, hide=True)

        rml=sim.rml
        elisa = sim.rml.beamline



        # define the values of the parameters to scan 
        energy    = np.arange(200, 2201,500)
        SlitSize  = np.array([0.1])
        cff       = np.array([2.25])
        nrays     = self.nrays

        # define a list of dictionaries with the parameters to scan
        params = [  
                    # set two parameters: "alpha" and "beta" in a dependent way. 
                    {elisa.Dipole.photonEnergy:energy}, 
                    # set a range of  values 
                    {elisa.ExitSlit.totalHeight:SlitSize},
                    # set values 
                    {elisa.PG.cFactor:cff},
                    {elisa.Dipole.numberRays:nrays}
                ]

        #and then plug them into the Simulation class
        sim.params=params

        # sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
        sim.simulation_name = 'test_NoAnalyze_comparison'

        # repeat the simulations as many time as needed
        sim.repeat = 1

        sim.analyze = False # don't let RAY-UI analyze the results
        sim.raypyng_analysis=True # let raypyng analyze the results

        ## This must be a list of dictionaries
        sim.exports  =  [{elisa.Dipole:'RawRaysOutgoing'},
                        {elisa.DetectorAtFocus:['RawRaysOutgoing']}
                        ]

        #uncomment to run the simulations
        result = sim.run(multiprocessing=5, force=self.force)
        self.assertTrue(result)
        

    def test1_RP_simulations(self):

        # dirpath = "RAYPy_Simulation_test_Analyze_comparison"
        # if os.path.exists(dirpath) and os.path.isdir(dirpath):
        #     shutil.rmtree(dirpath)
            

        this_file_dir=os.path.dirname(os.path.realpath(__file__))
        rml_file = os.path.join(this_file_dir,'rml/elisa.rml')

        sim = Simulate(rml_file, hide=True)

        rml=sim.rml
        elisa = sim.rml.beamline

        # define the values of the parameters to scan 
        energy    = np.arange(200, 2201,500)
        SlitSize  = np.array([0.1])
        cff       = np.array([2.25])
        nrays     = self.nrays

        # define a list of dictionaries with the parameters to scan
        params = [  
                    # set two parameters: "alpha" and "beta" in a dependent way. 
                    {elisa.Dipole.photonEnergy:energy}, 
                    # set a range of  values 
                    {elisa.ExitSlit.totalHeight:SlitSize},
                    # set values 
                    {elisa.PG.cFactor:cff},
                    {elisa.Dipole.numberRays:nrays}
                ]

        #and then plug them into the Simulation class
        sim.params=params

        # sim.simulation_folder = '/home/simone/Documents/RAYPYNG/raypyng/test'
        sim.simulation_name = 'test_Analyze_comparison'

        # repeat the simulations as many time as needed
        sim.repeat = 1

        sim.analyze = True # let RAY-UI analyze the results
        ## This must be a list of dictionaries
        sim.exports  =  [{elisa.Dipole:['ScalarElementProperties']},
                         {elisa.DetectorAtFocus:['ScalarBeamProperties']}
                        ]
        result = sim.run(multiprocessing=5, force=self.force)
        self.assertTrue(result)

    def test_2_source_flux(self):
        ppa = PostProcessAnalyzed()

        energy    = np.arange(200, 2201,500)


        # Flux RAY-UI
        repeat         = 1
        rml            = 'RAYPy_Simulation_test_Analyze_comparison'
        obj            = 'DetectorAtFocus'
        source         = 'Dipole'
        nsim           = energy.shape[0]
        self.flux_an, self.flux_percent_an, self.flux_dipole_an = ppa.retrieve_flux_beamline(rml,source,obj,nsim,repeat, current=0.1)

        # Flux raypyng

        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        dipole          = np.loadtxt(os.path.join(sim_folder,'Dipole.dat'))
        self.flux            = detectorAtFocus[:,3] 
        self.flux_dipole     = detectorAtFocus[:,0] 
        self.flux_percent    = detectorAtFocus[:,2]
        
        
        flux_dipole_result = compare_two_arrays(self.flux_dipole, self.flux_dipole_an, tol=0)
    
        # Plot Dipole
        ax = self.axs[0,0]
        ax.set_xlabel('Energy [eV]')
        ax.plot(energy, self.flux_dipole, 'b', label='RAY-UI')
        ax.plot(energy, self.flux_dipole_an, 'r', linestyle='dashed', label='raypyng')
        ax.set_ylabel('Flux [ph/s/0.1%bw]')
        ax.legend(loc=7)

        

        self.assertTrue(flux_dipole_result)
    
    def test_3_flux(self):
        ppa     = PostProcessAnalyzed()
        energy  = np.arange(200, 2201,500)

        # Flux RAY-UI
        repeat         = 1
        rml            = 'RAYPy_Simulation_test_Analyze_comparison'
        obj            = 'DetectorAtFocus'
        source         = 'Dipole'
        nsim           = energy.shape[0]
        self.flux_an, self.flux_percent_an, self.flux_dipole_an = ppa.retrieve_flux_beamline(rml,source,obj,nsim,repeat, current=0.1)

        # Flux raypyng

        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        dipole          = np.loadtxt(os.path.join(sim_folder,'Dipole.dat'))
        self.flux            = detectorAtFocus[:,3] 
        self.flux_dipole     = detectorAtFocus[:,0] 
        self.flux_percent    = detectorAtFocus[:,2]

        flux_result = compare_two_arrays(self.flux_an, self.flux, tol=30)

        # plot percentage flux
        ax = self.axs[1,0]
        ax.plot(energy,self.flux_an, 'r', label='ES 200 um, RAY-UI' )
        ax.plot(energy,self.flux, 'r', linestyle='dashed', label='ES 200 um, raypyng' )
        ax.set_xlabel(r'Energy [eV]')
        ax.set_ylabel('Flux [ph/s/0.1%bw]')
        ax.set_title('Beamline Transmission / Flux')
        ax.grid(which='both', axis='both')

        self.assertTrue(flux_result)

    def test_4_flux_percentage(self):
        ppa    = PostProcessAnalyzed()
        energy = np.arange(200, 2201,500)


        # Flux RAY-UI
        repeat         = 1
        rml            = 'RAYPy_Simulation_test_Analyze_comparison'
        obj            = 'DetectorAtFocus'
        source         = 'Dipole'
        nsim           = energy.shape[0]
        self.flux_an, self.flux_percent_an, self.flux_dipole_an = ppa.retrieve_flux_beamline(rml,source,obj,nsim,repeat, current=0.1)

        # Flux raypyng

        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        dipole          = np.loadtxt(os.path.join(sim_folder,'Dipole.dat'))
        self.flux            = detectorAtFocus[:,3] 
        self.flux_dipole     = detectorAtFocus[:,0] 
        self.flux_percent    = detectorAtFocus[:,2]

        flux_percent_result = compare_two_arrays(self.flux_percent_an, self.flux_percent_an, tol=5)
        



        
        # plot percentage flux
        ax = self.axs[0,1]
        ax.plot(energy,self.flux_percent_an, 'r', label='ES 200 um, RAY-UI' )
        ax.plot(energy,self.flux_percent, 'r', linestyle='dashed', label='ES 200 um, raypyng' )
        ax.set_xlabel(r'Energy [eV]')
        ax.set_ylabel('Transmission [%]')
        ax.set_title('Beamline Transmission / Flux')
        ax.grid(which='both', axis='both')

       

        self.assertTrue(flux_percent_result)

    def test_5_bandwidth(self):
        ppa     = PostProcessAnalyzed()
        energy  = np.arange(200, 2201,500)

        # Resolving Power RAY-UI
        repeat    = 1
        rml       = 'RAYPy_Simulation_test_Analyze_comparison'
        obj       = 'DetectorAtFocus'
        nsim      = energy.shape[0]
        self.bw_an, self.focx_an, self.focy_an = ppa.retrieve_bw_and_focusSize(rml,obj,nsim,repeat)

        # Resolving Power raypyng
        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        energy          = np.loadtxt(os.path.join(sim_folder,'input_param_Dipole_photonEnergy.dat'))
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        self.bw              = detectorAtFocus[:,4] 
        self.focx            = detectorAtFocus[:,5] 
        self.focy            = detectorAtFocus[:,6]

        bw_result = compare_two_arrays(self.bw, self.bw_an, tol=15)


        # plot bandwidth

        ax = self.axs[1,1]
        ax.plot(energy,self.bw_an,'r',label='RAY-UI')
        ax.plot(energy,self.bw,'r', linestyle='dashed',label='raypyng')
        ax.set_xlabel('Energy [eV]')
        ax.set_ylabel('Transmitted Bandwidth [eV]')
        ax.set_title('Transmitted bandwidth (tbw)')
        ax.grid(which='both', axis='both')
        ax.legend()

    
        self.assertTrue(bw_result)

    def test_6_focx(self):
        ppa    = PostProcessAnalyzed()
        energy = np.arange(200, 2201,500)

        # Resolving Power RAY-UI
        repeat    = 1
        rml       = 'RAYPy_Simulation_test_Analyze_comparison'
        obj       = 'DetectorAtFocus'
        nsim      = energy.shape[0]
        self.bw_an, self.focx_an, self.focy_an = ppa.retrieve_bw_and_focusSize(rml,obj,nsim,repeat)

        # Resolving Power raypyng
        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        energy          = np.loadtxt(os.path.join(sim_folder,'input_param_Dipole_photonEnergy.dat'))
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        self.bw              = detectorAtFocus[:,4] 
        self.focx            = detectorAtFocus[:,5] 
        self.focy            = detectorAtFocus[:,6]

        focx_result = compare_two_arrays(self.focx_an, self.focx, tol=10)

        # horizontal focus
        ax = self.axs[2,0]
        um = 1000 # scaling factor from mm to um
        ax.plot(energy, self.focx_an*um, 'r', label='RAY-UI')

        ax.plot(energy, self.focx*um, 'r', linestyle='dashed', label='raypyng')

        ax.set_xlabel('Energy [eV]')
        ax.set_ylabel('Focus Size [um]')
        ax.set_title('Horizontal focus')
        ax.legend()

        self.assertTrue(focx_result)
        

    def test_7_focy(self):
        ppa     = PostProcessAnalyzed()
        energy  = np.arange(200, 2201,500)

        # Resolving Power RAY-UI
        repeat    = 1
        rml       = 'RAYPy_Simulation_test_Analyze_comparison'
        obj       = 'DetectorAtFocus'
        nsim      = energy.shape[0]
        self.bw_an, self.focx_an, self.focy_an = ppa.retrieve_bw_and_focusSize(rml,obj,nsim,repeat)

        # Resolving Power raypyng
        sim_folder = 'RAYPy_Simulation_test_NoAnalyze_comparison'
        energy          = np.loadtxt(os.path.join(sim_folder,'input_param_Dipole_photonEnergy.dat'))
        detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
        self.bw              = detectorAtFocus[:,4] 
        self.focx            = detectorAtFocus[:,5] 
        self.focy            = detectorAtFocus[:,6]

        focy_result = compare_two_arrays(self.focy_an, self.focy, tol=10)

        #vertical focus
        ax = self.axs[2,1]
        um = 1000 # scaling factor from mm to um

        ax.plot(energy, self.focy_an*um, 'r', label='RAY-UI')
        ax.plot(energy, self.focy*um, 'r', linestyle='dashed', label='raypyng')

        ax.set_xlabel('Energy [eV]')
        ax.set_ylabel('Focus Size [um]')
        ax.set_title('Vertical focus')
        ax.legend()

        plt.tight_layout()
        self.assertTrue(focy_result)
        plt.savefig("test_2_comparison.png")


    
if __name__ == '__main__':
    unittest.main(verbosity=0)

# ppa = PostProcessAnalyzed()

# energy    = np.arange(200, 7201,1000)


# # Flux RAY-UI
# print("Flux RAY-UI")
# repeat         = 2
# rml            = 'RAYPy_Simulation_test_Analyze'
# obj            = 'DetectorAtFocus'
# source         = 'Dipole'
# nsim           = energy.shape[0]
# flux_an, flux_percent_an, flux_dipole_an = ppa.retrieve_flux_beamline(rml,source,obj,nsim,repeat, current=0.1)



# # Flux raypyng
# print("Flux raypyng")

# sim_folder = 'RAYPy_Simulation_test_NoAnalyze'
# detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
# dipole          = np.loadtxt(os.path.join(sim_folder,'Dipole.dat'))
# flux            = detectorAtFocus[:,3] 
# flux_dipole     = detectorAtFocus[:,0] 
# flux_percent    = detectorAtFocus[:,2]


# # Resolving Power RAY-UI
# print("RP RAY-UI")


# prepath   = ''
# repeat    = 2
# rml       = 'RAYPy_Simulation_test_Analyze'
# obj       = 'DetectorAtFocus'
# nsim      = energy.shape[0]
# bw_an, focx_an, focy_an = ppa.retrieve_bw_and_focusSize(rml,obj,nsim,repeat)



# # Resolving Power raypyng
# print("Flux raypyng")

# energy_rp = np.arange(200, 7201,1000)

# sim_folder = 'RAYPy_Simulation_test_NoAnalyze'
# energy          = np.loadtxt(os.path.join(sim_folder,'input_param_Dipole_photonEnergy.dat'))
# detectorAtFocus = np.loadtxt(os.path.join(sim_folder,'DetectorAtFocus.dat'))
# dipole          = np.loadtxt(os.path.join(sim_folder,'Dipole.dat'))
# bw              = detectorAtFocus[:,4] 
# focx            = detectorAtFocus[:,5] 
# focy            = detectorAtFocus[:,6]



# #plotting

# fig, (axs) = plt.subplots(3, 2,figsize=(10,10))



# # text
# ax = axs[0,0]



# # ML efficiency, Dipole Flux
# ax.set_xlabel('Energy [eV]')
# ax.plot(energy, flux_dipole, 'b', label='RAY-UI')
# ax.plot(energy, flux_dipole_an, 'r', linestyle='dashed', label='raypyng')
# ax.set_ylabel('Flux [ph/s/0.1%bw]')

# ax.legend(loc=7)






# # plot percentage flux
# ax = axs[0,1]

# ax.plot(energy,flux_percent_an, 'r', label='ES 200 um, RAY-UI' )

# ax.plot(energy,flux_percent, 'r', linestyle='dashed', label='ES 200 um, raypyng' )

# ax.set_xlabel(r'Energy [eV]')
# ax.set_ylabel('Transmission [%]')
# ax.set_title('Beamline Transmission / Flux')
# ax.grid(which='both', axis='both')


# ax.legend()






# # plot bandwidth

# ax = axs[1,0]
# ax.plot(energy,bw_an,'r',label='RAY-UI')

# ax.plot(energy,bw,'r', linestyle='dashed',label='raypyng')


# ax.set_xlabel('Energy [eV]')
# ax.set_ylabel('Transmitted Bandwidth [eV]')
# ax.set_title('Transmitted bandwidth (tbw)')
# ax.grid(which='both', axis='both')
# # ax.legend()


# # # plot RP

# ax = axs[1,1]
# ax.plot(energy,energy_rp/bw_an,'r',label='RAY-UI')

# ax.plot(energy,energy_rp/bw,'r', linestyle='dashed',label='raypyng')


# ax.set_xlabel('Energy [eV]')
# ax.set_ylabel('RP [a.u.]')
# ax.set_title('Resolving Power')
# ax.grid(which='both', axis='both')
# # ax.legend()



# # horizontal focus
# ax = axs[2,0]
# um = 1000 # scaling factor from mm to um
# ax.plot(energy, focx_an*um, 'r', label='RAY-UI')

# ax.plot(energy, focx*um, 'r', linestyle='dashed', label='raypyng')

# ax.set_xlabel('Energy [eV]')
# ax.set_ylabel('Focus Size [um]')
# ax.set_title('Horizontal focus')

# #vertical focus
# ax = axs[2,1]
# ax.plot(energy, focy_an*um, 'r', label='RAY-UI')

# ax.plot(energy, focy*um, 'r', linestyle='dashed', label='raypyng')

# ax.set_xlabel('Energy [eV]')
# ax.set_ylabel('Focus Size [um]')
# ax.set_title('Vertical focus')

# plt.tight_layout()

# plt.tight_layout()
# plt.show()






