from __future__ import annotations

from ..rml import ObjectElement
from .base import Simulate, SimulationRecipe, ensure_source


class BeamWaist(SimulationRecipe):
    def __init__(
        self,
        energy: float,
        /,
        source: ObjectElement = None,
        nrays: int = None,
        sim_folder: str = None,
    ):
        if not isinstance(energy, (int, float)):
            raise TypeError("The energy must be an a int or float, while it is a", type(energy))

        self.source = source
        self.energy = energy
        self.nrays = nrays
        self.sim_folder = sim_folder

    def params(self, sim: Simulate):
        params = []
        self.source = ensure_source(sim, self.source)
        params.append({self.source.photonEnergy: self.energy})

        for oe in sim.rml.beamline.children():
            for par in oe:
                try:
                    params.append({par.reflectivityType: 0})
                except AttributeError:
                    pass
        return params

    def exports(self, sim: Simulate):
        return [{oe: ["RawRaysOutgoing"]} for oe in sim.rml.beamline.children()]

    def simulation_name(self, sim: Simulate):
        return self.sim_folder or "Beamwaist"
