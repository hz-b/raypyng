import numpy as np
from raypyng.recipes import SimulationRecipe
from raypyng.simulate import Simulate


class ML(SimulationRecipe):
    """At one defined energy export a file for each
    optical elements
    """

    def __init__(self, nsim: float, exports: list, /, sim_folder: str = None, dirty_hack=False):
        """
        Args:
            energy_range (np.array, list): the energies to simulate in eV
            nrays (int): number of rays for the source
            sim_folder (str, optional): the name of the simulation folder. 
                            If None, the rml filename will be used. Defaults to None.

        """

        self.dirty_hack = dirty_hack
        self.nsim = int(nsim)
        self.energy = np.random.uniform(50, 2500, self.nsim)
        self.exports_list = exports
        self.sim_folder = sim_folder

        self.nrays = np.full(self.nsim, 8e6 + 1)  # np.random.uniform(1e3, 1e6+1,self.nsim)

        self.cff = np.random.uniform(1.01, 5, self.nsim)

    def params(self, sim: Simulate):
        params = []
        params_dict = {}

        # dirty hack:
        if self.dirty_hack:
            for i, oe in enumerate(sim.rml.beamline.children()):
                if hasattr(oe, "translationXerror") and i > 0:
                    oe.translationXerror.cdata = np.random.rand()
                    oe.translationYerror.cdata = np.random.rand()
                    oe.translationZerror.cdata = np.random.rand()
                    oe.rotationXerror.cdata = np.random.rand()
                    oe.rotationYerror.cdata = np.random.rand()
                    oe.rotationZerror.cdata = np.random.rand()

        # find source and add to param with defined user energy range
        # and fixed nrays range
        for i, oe in enumerate(sim.rml.beamline.children()):
            if hasattr(oe, "photonEnergy") and i == 0:
                self.source = oe
                params_dict[self.source.photonEnergy] = self.energy
                params_dict[self.source.numberRays] = self.nrays
            if hasattr(oe, "translationXerror") and i > 0:
                # fill with a special array value for better debugging
                params_dict[oe.translationXerror] = np.full(self.nsim, i / 100 + 0.1)
                params_dict[oe.translationYerror] = np.full(self.nsim, i / 100 + 0.2)
                params_dict[oe.translationZerror] = np.full(self.nsim, i / 100 + 0.3)
                params_dict[oe.rotationXerror] = np.full(self.nsim, i / 100 + 0.4)
                params_dict[oe.rotationYerror] = np.full(self.nsim, i / 100 + 0.5)
                params_dict[oe.rotationZerror] = np.full(self.nsim, i / 100 + 0.6)
            if hasattr(oe, "cFactor") and i > 0:
                params_dict[oe.cFactor] = self.cff
            if i == 6:
                params_dict[oe.totalHeight] = np.random.uniform(0.05, 1, self.nsim)
                params_dict[oe.translationXerror] = np.zeros(self.nsim)
                params_dict[oe.translationYerror] = np.zeros(self.nsim)
                params_dict[oe.translationZerror] = np.zeros(self.nsim)
                params_dict[oe.rotationXerror] = np.zeros(self.nsim)
                params_dict[oe.rotationYerror] = np.zeros(self.nsim)
                params_dict[oe.rotationZerror] = np.zeros(self.nsim)
        params.append(params_dict)
        # all done, return resulting params
        return params

    def exports(self, sim: Simulate):
        exports = []
        for oe in sim.rml.beamline.children():
            if oe["name"] in self.exports_list:
                exports.append({oe: "RawRaysOutgoing"})
        return exports

    def simulation_name(self, sim: Simulate):
        if self.sim_folder is None:
            return "ML"
        else:
            return self.sim_folder
