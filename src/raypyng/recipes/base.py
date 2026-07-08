from __future__ import annotations

from typing import Iterable

import numpy as np

from ..rml import ObjectElement


class Simulate:
    pass


class SimulationRecipe:
    def params(self, sim):
        return None

    def exports(self, sim):
        return None

    def simulation_name(self, sim):
        return None


def ensure_source(sim: Simulate, source: ObjectElement = None) -> ObjectElement:
    if source is not None:
        if not isinstance(source, ObjectElement):
            raise TypeError(
                "The source must be an ObjectElement part of a beamline, while it is a",
                type(source),
            )
        return source

    for oe in sim.rml.beamline.children():
        if hasattr(oe, "photonEnergy"):
            return oe
    raise AttributeError("I did not find the source")


def normalize_exported_objects(exported_object):
    if isinstance(exported_object, list):
        normalized = exported_object
    else:
        normalized = [exported_object]

    for exp_obj in normalized:
        if not isinstance(exp_obj, ObjectElement):
            raise TypeError(
                "The exported_object must be an ObjectElement part of a beamline, while it is a",
                type(exp_obj),
            )
    return normalized


def validate_energy_range(energy_range):
    if not isinstance(energy_range, (range, np.ndarray, list, tuple)):
        raise TypeError(
            "The energy_range must be a range, numpy array, list, or tuple, while it is a",
            type(energy_range),
        )


def normalize_extra_args(args: Iterable):
    normalized = []
    for a in args:
        if not isinstance(a, dict):
            raise TypeError("The args must be dictionaries, while I found a", type(a))
        normalized.append(a)
    return normalized


def default_exports(sim: Simulate, exported_object):
    export = ["ScalarBeamProperties"] if sim.analyze else ["RawRaysOutgoing"]
    return [{exp_obj: export} for exp_obj in exported_object]


def set_beamline_toggle(sim: Simulate, method_name: str, property_name: str, value: bool):
    if hasattr(sim, method_name):
        getattr(sim, method_name)(value)
        return

    for oe in sim.rml.beamline.children():
        if hasattr(oe, property_name):
            setattr(oe, property_name, value)
