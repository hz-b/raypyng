"""Grating efficiency calculation via graxpy (RCWA).

Called after RAY-UI saves the updated RML so that auto-computed angles (alpha)
are resolved before the parameters are read.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .rml import RMLFile

logger = logging.getLogger(__name__)

_SUPPORTED_PROFILES = {"blaze", "laminar"}


def _require_graxpy():
    """Return the grax module, raising ImportError with install hint if absent."""
    try:
        import grax

        return grax
    except ImportError:
        raise ImportError(
            "graxpy is not installed or not available. "
            "Install it with: pip install raypyng[graxpy]"
        ) from None


def _float_param(oe: Any, name: str, default: float | None = None) -> float | None:
    """Read a float param from an RML object element, returning default on any failure."""
    try:
        return float(getattr(oe, name).cdata)
    except Exception:
        return default


def _str_param(oe: Any, name: str, default: str = "") -> str:
    """Read a string param value from an RML object element."""
    try:
        return str(getattr(oe, name).cdata).strip()
    except Exception:
        return default


def read_grating_params(rml_path: str | Path) -> list[dict]:
    """Parse an RML file and return grating parameter dicts for graxpy.

    Only returns gratings with an enabled laminar or blaze line profile. The RML
    must already have been saved by RAY-UI so that auto-computed params (alpha,
    beta) are up to date.

    Args:
        rml_path: Path to the RML file.

    Returns:
        List of parameter dicts, one per qualifying Plane Grating element.
    """
    rml = RMLFile(str(rml_path))

    # Find photon energy from source element
    energy_ev: float | None = None
    for oe in rml.beamline.children():
        if hasattr(oe, "numberRays"):
            energy_ev = _float_param(oe, "photonEnergy")
            break

    gratings = []
    for oe in rml.beamline.children():
        if oe["type"] not in ("PlaneGrating", "Plane Grating"):
            continue

        try:
            line_profile_param = oe.lineProfile
        except AttributeError:
            continue

        if line_profile_param.enabled != "T":
            continue

        try:
            profile_type = line_profile_param["comment"].strip().lower()
        except (KeyError, AttributeError):
            continue

        if profile_type not in _SUPPORTED_PROFILES:
            continue

        name = oe["name"]
        period_lpermm = _float_param(oe, "lineDensity")
        alpha_deg = _float_param(oe, "alpha")
        diffraction_order = int(_float_param(oe, "orderDiffraction") or 1)
        substrate_material = _str_param(oe, "materialSubstrate") or "Si"
        roughness_nm = _float_param(oe, "roughnessSubstrate", default=0.0)

        # Coating: use materialCoating1 when present and enabled; otherwise substrate only.
        coating1_material = _str_param(oe, "materialCoating1")
        coating1_thickness = _float_param(oe, "thicknessCoating1", default=0.0)
        try:
            coating1_enabled = oe.materialCoating1.enabled == "T"
        except AttributeError:
            coating1_enabled = False
        if coating1_enabled and coating1_material and coating1_thickness and coating1_thickness > 0:
            layer_material = coating1_material
            layer_thickness_nm = coating1_thickness
        else:
            # No coating: use substrate material with a 1 nm self-layer (effective substrate-only).
            layer_material = substrate_material
            layer_thickness_nm = 1.0

        if period_lpermm is None or alpha_deg is None:
            logger.warning("Skipping grating %s: missing lineDensity or alpha in RML", name)
            continue

        params: dict[str, Any] = {
            "name": name,
            "profile_type": profile_type,
            "period_lpermm": period_lpermm,
            "alpha_deg": alpha_deg,
            "diffraction_order": diffraction_order,
            "substrate_material": substrate_material,
            "layer_material": layer_material,
            "layer_thickness_nm": layer_thickness_nm,
            "roughness_sigma_nm": (roughness_nm if roughness_nm and roughness_nm > 0 else None),
            "energy_ev": energy_ev,
        }

        if profile_type == "laminar":
            depth_nm = _float_param(oe, "grooveDepth")
            width_to_period_ratio = _float_param(oe, "grooveRatio")
            if depth_nm is None or width_to_period_ratio is None:
                logger.warning(
                    "Skipping laminar grating %s: missing grooveDepth or grooveRatio",
                    name,
                )
                continue
            params["depth_nm"] = depth_nm
            params["width_to_period_ratio"] = width_to_period_ratio

        elif profile_type == "blaze":
            blaze_angle_deg = _float_param(oe, "blazeAngle")
            aspect_angle_deg = _float_param(oe, "aspectAngle")
            if blaze_angle_deg is None:
                logger.warning("Skipping blaze grating %s: missing blazeAngle", name)
                continue
            params["blaze_angle_deg"] = blaze_angle_deg
            if aspect_angle_deg is not None:
                anti_blaze = 180.0 - aspect_angle_deg - blaze_angle_deg
                params["anti_blaze_angle_deg"] = anti_blaze if anti_blaze >= 0.01 else None
            else:
                params["anti_blaze_angle_deg"] = None

        gratings.append(params)

    return gratings


def compute_grating_efficiency(
    rml_path: str | Path,
    *,
    fourier_orders: int = 15,
    x_resolution_nm: float = 0.1,
    z_resolution_nm: float = 0.1,
) -> dict[str, dict]:
    """Compute grating diffraction efficiency (p polarization) for all qualifying
    gratings in the RML file using graxpy RCWA.

    Args:
        rml_path: Path to the (already saved) RML file.
        fourier_orders: Number of Fourier orders for the RCWA solve.
        x_resolution_nm: Horizontal discretisation resolution in nm.
        z_resolution_nm: Vertical discretisation resolution in nm.

    Returns:
        Dict mapping grating element name to a result dict with keys:
        ``energy_ev``, ``grazing_angle_deg``, ``diffraction_order``, ``efficiency_p``.
    """
    grax = _require_graxpy()
    grating_params_list = read_grating_params(rml_path)

    results: dict[str, dict] = {}
    for params in grating_params_list:
        name = params["name"]
        energy_ev = params["energy_ev"]
        alpha_deg = params["alpha_deg"]

        if energy_ev is None:
            logger.warning("Skipping grating %s: could not determine photon energy", name)
            continue
        if alpha_deg == 0.0:
            logger.warning(
                "Skipping grating %s: alpha=0, RAY-UI may not have resolved angles yet",
                name,
            )
            continue

        try:
            common = dict(
                period_lpermm=int(round(params["period_lpermm"])),
                substrate_material=params["substrate_material"],
                layer_material=params["layer_material"],
                layer_thickness_nm=params["layer_thickness_nm"],
                z_resolution_nm=z_resolution_nm,
                x_resolution_nm=x_resolution_nm,
            )

            if params["profile_type"] == "laminar":
                grating = grax.LaminarGrating(
                    depth_nm=params["depth_nm"],
                    width_to_period_ratio=params["width_to_period_ratio"],
                    **common,
                )
            else:  # blaze
                grating = grax.BlazedGrating(
                    blaze_angle_deg=params["blaze_angle_deg"],
                    anti_blaze_angle_deg=params["anti_blaze_angle_deg"],
                    **common,
                )

            run_kwargs: dict[str, Any] = dict(
                grating=grating,
                energy_ev=float(energy_ev),
                grazing_angle_deg=float(alpha_deg),
                diffraction_order=params["diffraction_order"],
                fourier_orders=fourier_orders,
                polarization="p",
            )
            if params["roughness_sigma_nm"] is not None:
                run_kwargs["roughness_sigma_nm"] = params["roughness_sigma_nm"]

            result = grax.run_simulation(**run_kwargs)
            results[name] = {
                "energy_ev": float(energy_ev),
                "grazing_angle_deg": float(alpha_deg),
                "diffraction_order": params["diffraction_order"],
                "efficiency_p": float(result.selected_efficiency),
            }
            logger.info(
                "graxpy efficiency for %s: %.4f (E=%.1f eV, alpha=%.3f deg, order=%d)",
                name,
                result.selected_efficiency,
                energy_ev,
                alpha_deg,
                params["diffraction_order"],
            )
        except Exception as exc:
            logger.warning("graxpy simulation failed for grating %s: %s", name, exc)

    return results


def write_efficiency_csv(rml_path: str | Path, efficiencies: dict[str, dict]) -> Path:
    """Write per-simulation graxpy efficiency results to a CSV next to the RML file.

    Args:
        rml_path: Path to the RML file (determines output directory and filename stem).
        efficiencies: Dict returned by :func:`compute_grating_efficiency`.

    Returns:
        Path to the written CSV file.
    """
    rml_path = Path(rml_path)
    out_path = rml_path.parent / (rml_path.stem + "_graxpy_efficiency.csv")

    rows = [{"grating_name": name, **values} for name, values in efficiencies.items()]
    df = pd.DataFrame(
        rows,
        columns=[
            "grating_name",
            "energy_ev",
            "grazing_angle_deg",
            "diffraction_order",
            "efficiency_p",
        ],
    )
    df.to_csv(out_path, index=False)
    return out_path


def aggregate_graxpy_results(sim_path: str | Path) -> Path:
    """Aggregate all per-simulation graxpy CSV files into one summary CSV.

    Searches all ``round_*`` subdirectories under *sim_path* for files matching
    ``*_graxpy_efficiency.csv``, concatenates them, and writes the result to
    ``sim_path/graxpy_efficiency.csv``.

    Args:
        sim_path: Root simulation directory.

    Returns:
        Path to the aggregated CSV.
    """
    sim_path = Path(sim_path)
    csv_files = sorted(sim_path.glob("round_*/*_graxpy_efficiency.csv"))
    if not csv_files:
        logger.warning("No graxpy efficiency CSV files found under %s", sim_path)
        out_path = sim_path / "graxpy_efficiency.csv"
        pd.DataFrame(
            columns=[
                "grating_name",
                "energy_ev",
                "grazing_angle_deg",
                "diffraction_order",
                "efficiency_p",
            ]
        ).to_csv(out_path, index=False)
        return out_path

    df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
    out_path = sim_path / "graxpy_efficiency.csv"
    df.to_csv(out_path, index=False)
    logger.info("Aggregated graxpy efficiency for %d simulations → %s", len(csv_files), out_path)
    return out_path
