from __future__ import annotations

from ..rml import ObjectElement
from .base import (
    Simulate,
    SimulationRecipe,
    default_exports,
    ensure_source,
    normalize_exported_objects,
    normalize_extra_args,
    validate_energy_range,
)


class ResolvingPower(SimulationRecipe):
    def __init__(
        self,
        energy_range,
        exported_object: ObjectElement,
        /,
        *args,
        source: ObjectElement = None,
        sim_folder: str = None,
    ):
        validate_energy_range(energy_range)
        self.source = source
        self.energy_range = energy_range
        self.exported_object = normalize_exported_objects(exported_object)
        self.args = normalize_extra_args(args)
        self.sim_folder = sim_folder

    def params(self, sim: Simulate):
        params = []
        self.source = ensure_source(sim, self.source)
        params.append({self.source.photonEnergy: self.energy_range})
        params.extend(self.args)

        for oe in sim.rml.beamline.children():
            if hasattr(oe, "reflectivityType"):
                params.append({oe.reflectivityType: 0})
        return params

    def exports(self, sim: Simulate):
        return default_exports(sim, self.exported_object)

    def simulation_name(self, sim: Simulate):
        return self.sim_folder or "RP"
