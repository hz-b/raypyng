from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Iterable

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


def _slope_group_for_element(element: ObjectElement):
    group = []
    for field in ["slopeErrorMer", "slopeErrorSag"]:
        if hasattr(element, field):
            group.append(getattr(element, field))
    return group


def _slope_groups(beamline) -> OrderedDict:
    groups = OrderedDict()
    for element in beamline.children():
        group = _slope_group_for_element(element)
        if group:
            groups[element.resolvable_name()] = group
    return groups


def _build_slopes_scan(groups: OrderedDict, slope_values: dict):
    matrix = OrderedDict()
    for params in groups.values():
        for param in params:
            config = slope_values[param]
            values = config["slope_values"]
            reference_value = config["reference_value"]
            matrix[param] = [0, reference_value]

    for element_name, params in groups.items():
        param_values = [slope_values[param]["slope_values"] for param in params]
        num_steps = max(len(values) for values in param_values)
        for idx in range(num_steps):
            for other_name, other_params in groups.items():
                for param in other_params:
                    if other_name == element_name:
                        values = slope_values[param]["slope_values"]
                        fill_value = values[idx] if idx < len(values) else 0
                    else:
                        fill_value = 0
                    matrix[param].append(fill_value)
    return matrix


def _slope_columns(df: pd.DataFrame):
    return [col for col in df.columns if ".slopeError" in col]


def _group_columns(columns: Iterable[str]):
    groups = OrderedDict()
    for column in columns:
        element_name = column.split(".", 1)[0]
        groups.setdefault(element_name, []).append(column)
    return groups


def _normalize_slope_config(config):
    if isinstance(config, dict):
        if "slope_values" not in config or "reference_value" not in config:
            raise ValueError(
                "Each slope_values entry must define both 'slope_values' and 'reference_value'"
            )
        return {
            "slope_values": np.array(config["slope_values"]),
            "reference_value": config["reference_value"],
        }

    values, reference_value = config
    return {
        "slope_values": np.array(values),
        "reference_value": reference_value,
    }


def _non_metric_columns(df: pd.DataFrame):
    metric_columns = {
        "Unnamed: 0",
        "Simulation Number",
        "SourcePhotonFlux",
        "SourceBandwidth",
        "NumberRaysSurvived",
        "PercentageRaysSurvived",
        "PhotonEnergy",
        "Bandwidth",
        "HorizontalFocusFWHM",
        "VerticalFocusFWHM",
        "HorizontalDivergenceFWHM",
        "VerticalDivergenceFWHM",
        "HorizontalCenter",
        "VerticalCenter",
        "PhotonFlux",
        "EnergyPerMilPerBw",
        "FluxPerMilPerBwPerc",
        "FluxPerMilPerBwAbs",
        "AXUVCurrentAmp",
        "GaAsPCurrentAmp",
    }
    return [column for column in df.columns if column not in metric_columns]


def _find_context_columns(df: pd.DataFrame, scan_columns):
    context_columns = []
    for column in _non_metric_columns(df):
        if column in scan_columns or column.endswith(".photonEnergy"):
            continue
        unique_values = df[column].dropna().unique()
        if len(unique_values) > 1:
            context_columns.append(column)
    return context_columns


def _reference_context_values(df: pd.DataFrame, context_columns):
    references = {}
    for column in context_columns:
        non_null = df[column].dropna()
        if non_null.empty:
            continue
        references[column] = non_null.iloc[0]
    return references


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


def _filter_baseline(df: pd.DataFrame, scan_columns):
    mask = (df[scan_columns] == 0).all(axis=1)
    return df[mask]


def _filter_element_value(
    df: pd.DataFrame, groups: OrderedDict, element_name: str, value_map: dict
):
    filtered = df
    for group_name, columns in groups.items():
        if group_name == element_name:
            for column in columns:
                filtered = filtered[filtered[column] == value_map[column]]
        else:
            for column in columns:
                filtered = filtered[filtered[column] == 0]
    return filtered


def _filter_all_preferred(df: pd.DataFrame, preferred_values: dict, groups: OrderedDict):
    filtered = df
    for _element_name, columns in groups.items():
        for column in columns:
            filtered = filtered[filtered[column] == preferred_values[column]]
    return filtered


def _apply_context_filter(df: pd.DataFrame, context_values: dict):
    filtered = df
    for column, value in context_values.items():
        filtered = filtered[filtered[column] == value]
    return filtered


def plot_slopes_scan(
    simulation_folder,
    output_folder=None,
    exported_object_name="DetectorAtFocus",
    showplot=False,
    saveplot=True,
):
    simulation_folder = Path(simulation_folder)
    recap_path = simulation_folder / f"{exported_object_name}_RawRaysOutgoing.csv"
    df = pd.read_csv(recap_path)

    slope_columns = _slope_columns(df)
    slope_groups = _group_columns(slope_columns)
    context_columns = _find_context_columns(df, slope_columns)
    context_values = _reference_context_values(df, context_columns)
    filtered_df = _apply_context_filter(df, context_values)

    if output_folder is None:
        output_folder = simulation_folder / "plot" / "slopes"
    output_folder = Path(output_folder)
    saved_paths = []

    preferred_row = filtered_df[(filtered_df[slope_columns] != 0).all(axis=1)].head(1)
    preferred_values = {}
    if not preferred_row.empty:
        for column in slope_columns:
            preferred_values[column] = float(preferred_row.iloc[0][column])

    baseline = _filter_baseline(filtered_df, slope_columns)
    all_preferred = _filter_all_preferred(filtered_df, preferred_values, slope_groups)

    title = "Slope scan"
    if context_values:
        context_label = ", ".join(f"{column}={value:g}" for column, value in context_values.items())
        title = f"{title}, {context_label}"

    fig, axs = plt.subplots(4, 1, figsize=(12, 12))
    _plot_series(axs, baseline, "No slope errors")
    _plot_series(axs, all_preferred, "All slope errors reference")
    _decorate_plot(axs, title)
    summary_path = output_folder / "slopes_summary.png"
    if saveplot:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(summary_path)
        saved_paths.append(summary_path)
    if showplot:
        plt.show()
    plt.close(fig)

    for element_name, columns in slope_groups.items():
        value_rows = filtered_df[(filtered_df[columns] != 0).any(axis=1)]
        unique_maps = []
        for _, row in value_rows.iterrows():
            value_map = {column: float(row[column]) for column in columns}
            if all(value != 0 for value in value_map.values()) and value_map not in unique_maps:
                unique_maps.append(value_map)
        fig, axs = plt.subplots(4, 1, figsize=(12, 12))
        _plot_series(axs, baseline, "No slope errors")
        for value_map in unique_maps:
            label = ", ".join(
                f"{column.split('.')[-1]}={value:g}" for column, value in value_map.items()
            )
            filtered = _filter_element_value(filtered_df, slope_groups, element_name, value_map)
            _plot_series(axs, filtered, f"{element_name} {label}")
        _decorate_plot(axs, f"{title}, {element_name}")
        element_path = output_folder / f"slopes_{element_name}.png"
        if saveplot:
            element_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(element_path)
            saved_paths.append(element_path)
        if showplot:
            plt.show()
        plt.close(fig)

    return saved_paths


class Slopes(SimulationRecipe):
    def __init__(
        self,
        energy_range,
        exported_object: ObjectElement,
        /,
        *args,
        source: ObjectElement = None,
        slope_values=None,
        nrays: int = None,
        rounds: int = 1,
        sim_folder: str = None,
    ):
        validate_energy_range(energy_range)
        self.source = source
        self.energy_range = energy_range
        self.exported_object = normalize_exported_objects(exported_object)
        self.args = normalize_extra_args(args)
        self.slope_values = slope_values or {}
        self.nrays = nrays
        self.rounds = rounds
        self.sim_folder = sim_folder

    def params(self, sim: Simulate):
        params = []
        self.source = ensure_source(sim, self.source)

        set_beamline_toggle(sim, "reflectivity", "reflectivity_enabled", True)
        set_beamline_toggle(sim, "slope_errors", "slope_error_enabled", True)

        params.append({self.source.photonEnergy: self.energy_range})
        params.extend(self.args)
        if self.nrays is not None:
            params.append({self.source.numberRays: self.nrays})

        groups = _slope_groups(sim.rml.beamline)
        if not self.slope_values:
            raise ValueError("slope_values must be provided for the Slopes recipe")

        normalized_values = {}
        filtered_groups = OrderedDict()
        for element_name, params_group in groups.items():
            filtered_group = []
            for param in params_group:
                if param in self.slope_values:
                    normalized_values[param] = _normalize_slope_config(self.slope_values[param])
                    filtered_group.append(param)
            if filtered_group:
                filtered_groups[element_name] = filtered_group

        if not normalized_values:
            raise ValueError("No matching slope parameters were found in slope_values")

        params.append(_build_slopes_scan(filtered_groups, normalized_values))
        return params

    def exports(self, sim: Simulate):
        return default_exports(sim, self.exported_object)

    def simulation_name(self, sim: Simulate):
        return self.sim_folder or "Slopes"
