from __future__ import annotations

from collections import OrderedDict
from numbers import Real
from pathlib import Path

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
)

ALIGNMENT_ERROR_PARAMETERS = (
    "translationXerror",
    "translationYerror",
    "translationZerror",
    "rotationXerror",
    "rotationYerror",
    "rotationZerror",
)


def _is_number(value) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _validate_required_number(name: str, value):
    if not _is_number(value):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")


def _validate_required_integer_like(name: str, value):
    _validate_required_number(name, value)
    if int(value) != value:
        raise ValueError(f"{name} must be an integer-like value, got {value}")


def _normalize_scan_points(n_scan_points: int) -> int:
    normalized = int(n_scan_points)
    if normalized % 2 == 0:
        adjusted = normalized + 1
        print(
            f"[PerElementVibrationScan] requested n_scan_points={normalized} is even; "
            f"using {adjusted} so the zero-vibration point is included."
        )
        return adjusted
    return normalized


def _normalize_transfer_factor(transfer_factor):
    if _is_number(transfer_factor):
        return {name: float(transfer_factor) for name in ALIGNMENT_ERROR_PARAMETERS}

    if not isinstance(transfer_factor, dict):
        raise TypeError(
            "transfer_factor must be a scalar or a dict keyed by alignment parameter name"
        )

    invalid_keys = sorted(set(transfer_factor) - set(ALIGNMENT_ERROR_PARAMETERS))
    if invalid_keys:
        raise ValueError(
            "transfer_factor contains unsupported alignment parameter names: "
            + ", ".join(invalid_keys)
        )

    normalized = {name: 30.0 for name in ALIGNMENT_ERROR_PARAMETERS}
    for name, value in transfer_factor.items():
        _validate_required_number(f"transfer_factor['{name}']", value)
        normalized[name] = float(value)
    return normalized


def _alignment_group_for_element(element: ObjectElement):
    if hasattr(element, "photonEnergy"):
        return None

    if not hasattr(element, "alignmentError"):
        return None

    params = OrderedDict()
    for field in ALIGNMENT_ERROR_PARAMETERS:
        if hasattr(element, field):
            params[field] = getattr(element, field)

    if not params:
        return None

    return {
        "toggle": element.alignmentError,
        "params": params,
    }


def _alignment_groups(beamline) -> OrderedDict:
    groups = OrderedDict()
    for element in beamline.children():
        group = _alignment_group_for_element(element)
        if group:
            groups[element.resolvable_name()] = group
    return groups


def _build_per_element_vibration_scan(
    groups: OrderedDict,
    max_rms_nm: float,
    transfer_factor,
    n_scan_points: int,
):
    matrix = OrderedDict()
    for group in groups.values():
        matrix[group["toggle"]] = []
        for param in group["params"].values():
            matrix[param] = []

    for active_element_name, active_group in groups.items():
        for param_name, _active_param in active_group["params"].items():
            factor = transfer_factor[param_name]
            scan_values = np.linspace(
                -max_rms_nm * factor,
                max_rms_nm * factor,
                n_scan_points,
            )

            for scan_value in scan_values:
                for element_name, group in groups.items():
                    matrix[group["toggle"]].append(0 if element_name == active_element_name else 1)
                    for other_param_name, param in group["params"].items():
                        if element_name == active_element_name and other_param_name == param_name:
                            matrix[param].append(float(scan_value))
                        else:
                            matrix[param].append(0.0)

    return matrix


def _alignment_toggle_columns(df: pd.DataFrame):
    columns = []
    for column in df.columns:
        if not column.endswith(".alignmentError"):
            continue
        element_name = column.split(".", 1)[0]
        if (
            f"{element_name}.photonEnergy" in df.columns
            or f"{element_name}.numberRays" in df.columns
        ):
            continue
        columns.append(column)
    return columns


def _parameter_columns_for_element(df: pd.DataFrame, element_name: str):
    columns = OrderedDict()
    for param_name in ALIGNMENT_ERROR_PARAMETERS:
        column = f"{element_name}.{param_name}"
        if column in df.columns:
            columns[param_name] = column
    return columns


def _scan_subset(
    df: pd.DataFrame,
    element_names: list[str],
    parameter_columns: dict[str, OrderedDict],
    active_element: str,
    active_parameter: str,
):
    active_column = parameter_columns[active_element].get(active_parameter)
    if active_column is None:
        return None

    filtered = df
    for element_name in element_names:
        toggle_column = f"{element_name}.alignmentError"
        toggle_value = 0 if element_name == active_element else 1
        filtered = filtered[filtered[toggle_column] == toggle_value]

        for param_name, column in parameter_columns[element_name].items():
            if element_name == active_element and param_name == active_parameter:
                continue
            filtered = filtered[filtered[column] == 0]

    # Every scan of a different parameter for the same element contributes the
    # same zero-perturbation row for the active column, so keep one row per
    # x-value to recover the requested n_scan_points.
    filtered = filtered.sort_values(active_column)
    filtered = filtered.drop_duplicates(subset=[active_column], keep="first")
    return filtered


def _bandwidth_variation_percent(subset: pd.DataFrame, x_column: str):
    zero_rows = subset[np.isclose(subset[x_column], 0.0)]
    if zero_rows.empty:
        return None

    reference_bandwidth = zero_rows.iloc[0]["Bandwidth"]
    if pd.isna(reference_bandwidth) or np.isclose(reference_bandwidth, 0.0):
        return None

    return 100.0 * (subset["Bandwidth"] - reference_bandwidth) / reference_bandwidth


def _relative_variation_percent(values: pd.Series, reference_value):
    if pd.isna(reference_value) or np.isclose(reference_value, 0.0):
        return values * np.nan
    return 100.0 * (values - reference_value) / reference_value


def _zero_reference_row(subset: pd.DataFrame, x_column: str):
    zero_rows = subset[np.isclose(subset[x_column], 0.0)]
    if zero_rows.empty:
        return None
    return zero_rows.iloc[0]


def _axis_grid(nrows: int, ncols: int, figsize):
    fig, axs = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)
    return fig, axs


def _mark_unsupported(ax, element_name: str, parameter_name: str):
    ax.text(
        0.5,
        0.5,
        f"{element_name}\n{parameter_name}\nunsupported",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )
    ax.set_xlabel("Perturbation value")
    ax.set_ylabel("")
    ax.grid(True, alpha=0.3)


def plot_per_element_vibration_scan(
    simulation_folder,
    output_folder=None,
    exported_object_name="DetectorAtFocus",
    showplot=False,
    saveplot=True,
):
    simulation_folder = Path(simulation_folder)
    recap_path = simulation_folder / f"{exported_object_name}_RawRaysOutgoing.csv"
    df = pd.read_csv(recap_path)

    element_names = [column.split(".", 1)[0] for column in _alignment_toggle_columns(df)]
    parameter_columns = {
        element_name: _parameter_columns_for_element(df, element_name)
        for element_name in element_names
    }

    if output_folder is None:
        output_folder = simulation_folder / "plot" / "per_element_vibration_scan"
    output_folder = Path(output_folder)
    saved_paths = []

    nrows = max(len(element_names), 1)
    ncols = len(ALIGNMENT_ERROR_PARAMETERS)

    fig_bw, axs_bw = _axis_grid(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows))
    fig_centers_abs, axs_centers_abs = _axis_grid(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows))
    fig_centers_rel, axs_centers_rel = _axis_grid(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows))

    for row_idx, element_name in enumerate(element_names):
        for col_idx, param_name in enumerate(ALIGNMENT_ERROR_PARAMETERS):
            ax_bw = axs_bw[row_idx][col_idx]
            ax_centers_abs = axs_centers_abs[row_idx][col_idx]
            ax_centers_rel = axs_centers_rel[row_idx][col_idx]
            subset = _scan_subset(df, element_names, parameter_columns, element_name, param_name)

            if subset is None:
                _mark_unsupported(ax_bw, element_name, param_name)
                _mark_unsupported(ax_centers_abs, element_name, param_name)
                _mark_unsupported(ax_centers_rel, element_name, param_name)
                continue

            x_column = parameter_columns[element_name][param_name]
            zero_reference = _zero_reference_row(subset, x_column)
            ax_bw.plot(subset[x_column], subset["Bandwidth"], marker=".")
            ax_bw.set_xlabel("Perturbation value")
            ax_bw.set_ylabel("Bandwidth [eV]")
            ax_bw.set_title(f"{element_name}\n{param_name}")
            ax_bw.grid(True, alpha=0.3)

            if zero_reference is not None:
                reference_bandwidth = zero_reference["Bandwidth"]
                if not (pd.isna(reference_bandwidth) or np.isclose(reference_bandwidth, 0.0)):
                    ax_bw_right = ax_bw.secondary_yaxis(
                        "right",
                        functions=(
                            lambda y, ref=reference_bandwidth: 100.0 * (y - ref) / ref,
                            lambda pct, ref=reference_bandwidth: ref * (1.0 + pct / 100.0),
                        ),
                    )
                    ax_bw_right.set_ylabel("Bandwidth variation vs 0 [%]")

            line_h_abs = ax_centers_abs.plot(
                subset[x_column],
                subset["HorizontalCenter"],
                marker=".",
                label="HorizontalCenter",
            )[0]
            ax_centers_abs.set_xlabel("Perturbation value")
            ax_centers_abs.set_ylabel("HorizontalCenter [mm]")
            ax_centers_abs.set_title(f"{element_name}\n{param_name}")
            ax_centers_abs.grid(True, alpha=0.3)

            ax_centers_abs_right = ax_centers_abs.twinx()
            line_v_abs = ax_centers_abs_right.plot(
                subset[x_column],
                subset["VerticalCenter"],
                marker=".",
                color="tab:orange",
                label="VerticalCenter",
            )[0]
            ax_centers_abs_right.set_ylabel("VerticalCenter [mm]")
            ax_centers_abs.legend(
                [line_h_abs, line_v_abs], ["HorizontalCenter", "VerticalCenter"], loc="best"
            )

            if zero_reference is None:
                horizontal_relative = subset["HorizontalCenter"] * np.nan
                vertical_relative = subset["VerticalCenter"] * np.nan
            else:
                horizontal_relative = _relative_variation_percent(
                    subset["HorizontalCenter"], zero_reference["HorizontalCenter"]
                )
                vertical_relative = _relative_variation_percent(
                    subset["VerticalCenter"], zero_reference["VerticalCenter"]
                )

            line_h_rel = ax_centers_rel.plot(
                subset[x_column],
                horizontal_relative,
                marker=".",
                label="HorizontalCenter",
            )[0]
            ax_centers_rel.set_xlabel("Perturbation value")
            ax_centers_rel.set_ylabel("HorizontalCenter variation vs 0 [%]")
            ax_centers_rel.set_title(f"{element_name}\n{param_name}")
            ax_centers_rel.grid(True, alpha=0.3)

            ax_centers_rel_right = ax_centers_rel.twinx()
            line_v_rel = ax_centers_rel_right.plot(
                subset[x_column],
                vertical_relative,
                marker=".",
                color="tab:orange",
                label="VerticalCenter",
            )[0]
            ax_centers_rel_right.set_ylabel("VerticalCenter variation vs 0 [%]")
            ax_centers_rel.legend(
                [line_h_rel, line_v_rel], ["HorizontalCenter", "VerticalCenter"], loc="best"
            )

    fig_bw.suptitle("Per-element vibration scan: Bandwidth")
    fig_bw.tight_layout()
    fig_centers_abs.suptitle("Per-element vibration scan: centers (absolute)")
    fig_centers_abs.tight_layout()
    fig_centers_rel.suptitle("Per-element vibration scan: centers (relative to 0)")
    fig_centers_rel.tight_layout()

    bandwidth_path = output_folder / "per_element_vibration_scan_bandwidth.png"
    centers_abs_path = output_folder / "per_element_vibration_scan_centers_absolute.png"
    centers_rel_path = output_folder / "per_element_vibration_scan_centers_relative.png"

    if saveplot:
        output_folder.mkdir(parents=True, exist_ok=True)
        fig_bw.savefig(bandwidth_path, dpi=150)
        fig_centers_abs.savefig(centers_abs_path, dpi=150)
        fig_centers_rel.savefig(centers_rel_path, dpi=150)
        saved_paths.extend([bandwidth_path, centers_abs_path, centers_rel_path])

    if showplot:
        plt.show()

    plt.close(fig_bw)
    plt.close(fig_centers_abs)
    plt.close(fig_centers_rel)
    return saved_paths


class PerElementVibrationScan(SimulationRecipe):
    def __init__(
        self,
        energy,
        export_element: ObjectElement,
        /,
        *args,
        source: ObjectElement = None,
        max_rms_nm=None,
        transfer_factor=30,
        nrays: int = None,
        n_scan_points: int = 5,
        rounds: int = 1,
        sim_folder: str = None,
    ):
        _validate_required_number("energy", energy)
        _validate_required_number("max_rms_nm", max_rms_nm)
        _validate_required_integer_like("nrays", nrays)
        _validate_required_integer_like("n_scan_points", n_scan_points)
        if int(n_scan_points) < 2:
            raise ValueError("n_scan_points must be at least 2")

        self.source = source
        self.energy = float(energy)
        self.export_element = normalize_exported_objects(export_element)
        self.args = normalize_extra_args(args)
        self.max_rms_nm = float(max_rms_nm)
        self.transfer_factor = _normalize_transfer_factor(transfer_factor)
        self.nrays = int(nrays)
        self.n_scan_points = _normalize_scan_points(n_scan_points)
        self.rounds = rounds
        self.sim_folder = sim_folder

    def params(self, sim: Simulate):
        params = []
        self.source = ensure_source(sim, self.source)

        set_beamline_toggle(sim, "reflectivity", "reflectivity_enabled", False)
        set_beamline_toggle(sim, "slope_errors", "slope_error_enabled", False)
        set_beamline_toggle(sim, "alignment_errors", "alignment_error_enabled", False)

        params.append({self.source.photonEnergy: self.energy})
        params.extend(self.args)
        params.append({self.source.numberRays: self.nrays})

        groups = _alignment_groups(sim.rml.beamline)
        params.append(
            _build_per_element_vibration_scan(
                groups,
                self.max_rms_nm,
                self.transfer_factor,
                self.n_scan_points,
            )
        )
        return params

    def exports(self, sim: Simulate):
        return default_exports(sim, self.export_element)

    def simulation_name(self, sim: Simulate):
        return self.sim_folder or "PerElementVibrationScan"
