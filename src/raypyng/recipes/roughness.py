from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..rml import ObjectElement
from .base import (
    Simulate,
    SimulationRecipe,
    default_exports,
    ensure_source,
    normalize_exported_objects,
    normalize_extra_args,
    set_beamline_toggle,
    validate_energy_range,
)


def _roughness_group_for_element(element: ObjectElement):
    group = []
    roughness_fields = [
        "roughnessSubstrate",
        "roughnessCoating1",
        "roughnessCoating2",
        "roughnessTopLayer",
    ]
    for field in roughness_fields:
        if not hasattr(element, field):
            continue
        param = getattr(element, field)
        if field != "roughnessSubstrate" and param.attributes().get("enabled") != "T":
            continue
        group.append(param)
    return group


def _roughness_groups(beamline) -> OrderedDict:
    groups = OrderedDict()
    for element in beamline.children():
        group = _roughness_group_for_element(element)
        if group:
            groups[element.resolvable_name()] = group
    return groups


def _build_roughness_scan(groups: OrderedDict, roughness_values, preferred_value):
    matrix = OrderedDict()
    for params in groups.values():
        for param in params:
            matrix[param] = [0, preferred_value]

    for element_name, _params in groups.items():
        for value in roughness_values:
            for other_name, other_params in groups.items():
                fill_value = value if other_name == element_name else 0
                for param in other_params:
                    matrix[param].append(fill_value)
    return matrix


def _roughness_columns(df: pd.DataFrame):
    return [col for col in df.columns if ".roughness" in col]


def _group_roughness_columns(columns: Iterable[str]):
    groups = OrderedDict()
    for column in columns:
        element_name = column.split(".", 1)[0]
        groups.setdefault(element_name, []).append(column)
    return groups


def _find_partition_column(df: pd.DataFrame):
    preferred = ["ExitSlit.openingHeight", "ExitSlit.totalHeight"]
    for column in preferred:
        if column in df.columns:
            return column
    return None


def _extract_plot_data(dataframe: pd.DataFrame):
    energy_col = next((c for c in dataframe.columns if c.endswith(".photonEnergy")), None)
    if energy_col is None:
        raise KeyError("Could not find a photonEnergy column in the simulation recap CSV")

    energy = dataframe[energy_col]
    bandwidth = dataframe["Bandwidth"]
    hfoc = dataframe["HorizontalFocusFWHM"] * 1000
    vfoc = dataframe["VerticalFocusFWHM"] * 1000
    return energy, bandwidth, hfoc, vfoc


def _plot_series(axs, dataframe: pd.DataFrame, label: str):
    energy, bandwidth, hfoc, vfoc = _extract_plot_data(dataframe)
    axs[0].plot(energy, bandwidth, label=label)
    axs[1].plot(energy, energy / bandwidth, label=label)
    axs[2].plot(energy, hfoc, label=label)
    axs[3].plot(energy, vfoc, label=label)


def _decorate_plot(axs, title: str):
    labels = [
        ("Transmitted Bandwidth [eV]", "Transmitted bandwidth"),
        ("Resolving Power [a.u.]", "Resolving Power"),
        ("Focus Size [um]", "Horizontal focus"),
        ("Focus Size [um]", "Vertical focus"),
    ]
    for ax, (ylabel, subplot_title) in zip(axs, labels, strict=False):
        ax.set_xlabel("Energy [eV]")
        ax.set_ylabel(ylabel)
        ax.set_title(subplot_title)
        ax.grid(which="both", axis="both")
    axs[0].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.suptitle(title)
    plt.tight_layout()


def _filter_baseline(df: pd.DataFrame, roughness_columns: List[str]):
    mask = (df[roughness_columns] == 0).all(axis=1)
    return df[mask]


def _filter_element_value(df: pd.DataFrame, groups: OrderedDict, element_name: str, value: float):
    filtered = df
    for group_name, columns in groups.items():
        if group_name == element_name:
            for column in columns:
                filtered = filtered[filtered[column] == value]
        else:
            for column in columns:
                filtered = filtered[filtered[column] == 0]
    return filtered


def _filter_all_preferred(
    df: pd.DataFrame, preferred_values: Dict[str, float], groups: OrderedDict
):
    filtered = df
    for element_name, columns in groups.items():
        for column in columns:
            filtered = filtered[filtered[column] == preferred_values[element_name]]
    return filtered


def plot_roughness_scan(
    simulation_folder,
    output_folder=None,
    exported_object_name="DetectorAtFocus",
    showplot=False,
    saveplot=True,
):
    simulation_folder = Path(simulation_folder)
    recap_path = simulation_folder / f"{exported_object_name}_RawRaysOutgoing.csv"
    df = pd.read_csv(recap_path)

    roughness_columns = _roughness_columns(df)
    roughness_groups = _group_roughness_columns(roughness_columns)
    partition_column = _find_partition_column(df)
    partitions = [None] if partition_column is None else sorted(df[partition_column].unique())

    if output_folder is None:
        output_folder = simulation_folder / "plot" / "roughness"
    output_folder = Path(output_folder)
    saved_paths = []

    preferred_row = df[(df[roughness_columns] != 0).all(axis=1)].head(1)
    preferred_values = {}
    if not preferred_row.empty:
        for element_name, columns in roughness_groups.items():
            preferred_values[element_name] = float(preferred_row.iloc[0][columns[0]])

    for partition in partitions:
        partition_df = df if partition is None else df[df[partition_column] == partition]
        baseline = _filter_baseline(partition_df, roughness_columns)
        all_preferred = _filter_all_preferred(partition_df, preferred_values, roughness_groups)

        if partition_column is None:
            suffix = "all"
            title = "Roughness scan"
        else:
            suffix = f"{partition:g}".replace(".", "p")
            title = f"Roughness scan, {partition_column}={partition:g}"

        fig, axs = plt.subplots(4, 1, figsize=(12, 12))
        _plot_series(axs, baseline, "No roughness")
        _plot_series(axs, all_preferred, "All roughness preferred")
        _decorate_plot(axs, title)
        summary_path = output_folder / f"roughness_summary_{suffix}.png"
        if saveplot:
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(summary_path)
            saved_paths.append(summary_path)
        if showplot:
            plt.show()
        plt.close(fig)

        for element_name, columns in roughness_groups.items():
            values = sorted(v for v in partition_df[columns[0]].unique() if v != 0)
            fig, axs = plt.subplots(4, 1, figsize=(12, 12))
            _plot_series(axs, baseline, "No roughness")
            for value in values:
                filtered = _filter_element_value(
                    partition_df, roughness_groups, element_name, value
                )
                _plot_series(axs, filtered, f"{element_name} {value:g} rms")
            _decorate_plot(axs, f"{title}, {element_name}")
            element_path = output_folder / f"roughness_{element_name}_{suffix}.png"
            if saveplot:
                element_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(element_path)
                saved_paths.append(element_path)
            if showplot:
                plt.show()
            plt.close(fig)

    return saved_paths


class Roughness(SimulationRecipe):
    def __init__(
        self,
        energy_range,
        exported_object: ObjectElement,
        /,
        *args,
        source: ObjectElement = None,
        roughness_values=None,
        preferred_value: float = 0.3,
        nrays: int = None,
        rounds: int = 1,
        sim_folder: str = None,
    ):
        validate_energy_range(energy_range)
        self.source = source
        self.energy_range = energy_range
        self.exported_object = normalize_exported_objects(exported_object)
        self.args = normalize_extra_args(args)
        self.roughness_values = np.array(
            roughness_values if roughness_values is not None else [0.1, 0.3, 0.5, 1.5]
        )
        self.preferred_value = preferred_value
        self.nrays = nrays
        self.rounds = rounds
        self.sim_folder = sim_folder

    def params(self, sim: Simulate):
        params = []
        self.source = ensure_source(sim, self.source)

        set_beamline_toggle(sim, "reflectivity", "reflectivity_enabled", True)
        set_beamline_toggle(sim, "slope_errors", "slope_error_enabled", False)

        params.append({self.source.photonEnergy: self.energy_range})
        params.extend(self.args)
        if self.nrays is not None:
            params.append({self.source.numberRays: self.nrays})

        groups = _roughness_groups(sim.rml.beamline)
        params.append(_build_roughness_scan(groups, self.roughness_values, self.preferred_value))
        return params

    def exports(self, sim: Simulate):
        return default_exports(sim, self.exported_object)

    def simulation_name(self, sim: Simulate):
        return self.sim_folder or "Roughness"
