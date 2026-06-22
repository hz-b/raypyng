import os

import numpy as np
import pandas as pd


def _require_rayx():
    try:
        import rayx

        return rayx
    except ImportError:
        raise ImportError(
            "rayx is not installed or not available on this platform. "
            "Install it with: pip install rayx[rayx]"
        ) from None


# RAY-UI uses 100 mA as the implicit ring current for dipole flux calculations
# when no ringCurrents field is present in the RML.
_RAYUI_DEFAULT_CURRENT_A = 0.1


def _rayui_update_rml(rml_path, ray_path=None, hide=False):
    """Pre-update an RML file by running a 1-ray RAY-UI trace and saving.

    RAY-UI resolves element positions, grating/mirror angles, and photon flux
    when it opens an RML.  Running a minimal trace and saving writes all those
    computed values back to disk so that rayx can use the fully-configured RML.
    The source's numberRays is temporarily forced to 1 to keep the trace fast,
    then restored to its original value after the save.
    """
    from .rml import RMLFile
    from .runner import RayUIAPI, RayUIRunner

    # Temporarily force numberRays=1 so the pre-update trace is near-instant
    rml = RMLFile(rml_path)
    original_nrays = None
    for oe in rml.beamline.children():
        if hasattr(oe, "numberRays"):
            try:
                original_nrays = int(float(oe.numberRays.cdata))
                oe.numberRays.cdata = "1"
            except (AttributeError, ValueError):
                pass
            break
    rml.write(rml_path)

    runner = RayUIRunner(ray_path=ray_path, hide=hide)
    try:
        runner.run()
        api = RayUIAPI(runner)
        api.load(rml_path)
        api.trace(analyze=False)
        api.save(rml_path)
    finally:
        runner.kill()

    # Restore the original numberRays so rayx traces the intended ray count
    if original_nrays is not None:
        rml = RMLFile(rml_path)
        for oe in rml.beamline.children():
            if hasattr(oe, "numberRays"):
                oe.numberRays.cdata = str(original_nrays)
                break
        rml.write(rml_path)


def _patch_source_params(rml_path):
    """Patch per-simulation RML source parameters that rayx mis-handles.

    Two fixes applied to the first source element found:

    1. photonFlux — rayx keeps the original RML value regardless of photonEnergy.
       We recompute it from the Dipole/Schwinger formula (100 mA default current),
       mirroring what RAY-UI writes back after each trace.

    2. energySpread — rayx ignores energySpreadUnit and treats the field as an
       absolute eV value.  When the unit is "%", we convert the percentage to an
       absolute eV spread so rayx generates the correct energy bandwidth.
       energySpreadUnit comment is changed to "eV" so that postprocessing's
       extract_bw_from_source returns NaN (rather than a nonsense value) for the
       secondary FluxPerMilPerBw* metrics; the primary Bandwidth column is always
       computed from the actual ray EN FWHM and is unaffected.
    """
    from raypyng.dipole_flux import Dipole as DipoleFlux
    from raypyng.rml import RMLFile

    rml = RMLFile(rml_path)
    modified = False

    for oe in rml.beamline.children():
        if not hasattr(oe, "photonEnergy"):
            continue
        try:
            photon_energy_eV = float(oe.photonEnergy.cdata)
        except (AttributeError, ValueError):
            break

        # Fix 1: photonFlux for Dipole sources
        if hasattr(oe, "bendingRadius"):
            try:
                E_GeV = float(oe.electronEnergy.cdata)
                R_m = float(oe.bendingRadius.cdata)
                hdiv_mrad = float(oe.horDiv.cdata)
                d = DipoleFlux(
                    bending_radius_m=R_m, beam_energy_GeV=E_GeV, current_A=_RAYUI_DEFAULT_CURRENT_A
                )
                flux = float(
                    d.calculate_spectrum(np.array([photon_energy_eV]), hdiv=np.array([hdiv_mrad]))[
                        0, 0
                    ]
                )
                oe.photonFlux.cdata = f"{flux:.6g}"
                modified = True
            except (AttributeError, ValueError):
                pass

        # Fix 2: energySpread percentage → absolute eV
        try:
            if oe.energySpreadUnit.comment == "%":
                spread_pct = float(oe.energySpread.cdata)
                spread_abs = photon_energy_eV * spread_pct / 100.0
                oe.energySpread.cdata = f"{spread_abs:.6g}"
                oe.energySpreadUnit._attributes["comment"] = "eV"
                modified = True
        except (AttributeError, ValueError):
            pass

        break  # only patch the first (source) element

    if modified:
        rml.write(rml_path)


class RayXAPI:
    """Thin wrapper around rayx that mirrors the RayUIAPI load/trace/export interface."""

    def __init__(self):
        self._beamline = None
        self._rays_df = None

    def load(self, rml_path):
        rayx = _require_rayx()
        _patch_source_params(rml_path)
        self._beamline = rayx.import_beamline(rml_path)
        self._rays_df = None

    def trace(self):
        rayx = _require_rayx()
        rays = self._beamline.trace()
        self._rays_df = rayx.rays_to_df(rays)

    def export(self, element_name, export_type, export_path, data_prefix):
        """Export ray data for one element in the tab-delimited format that PostProcess expects.

        Writes:  {export_path}/{data_prefix}{element_name}-{export_type}.csv
        Format:  1 comment line, 1 header line, then tab-delimited data rows.
        Columns: {element}_OX  _OY  _EN  _DX  _DY  _DZ  (matches RAY-UI RawRays convention).
        """
        if export_type != "RawRaysOutgoing":
            raise NotImplementedError(
                f"RAYX engine only supports RawRaysOutgoing; '{export_type}' is not implemented."
            )

        name_to_idx = {s.name: i for i, s in enumerate(self._beamline.sources)}
        name_to_idx.update(
            {
                el.name: len(self._beamline.sources) + j
                for j, el in enumerate(self._beamline.elements)
            }
        )
        if element_name not in name_to_idx:
            raise ValueError(
                f"Element '{element_name}' not found in beamline. "
                f"Available: {list(name_to_idx)}"
            )

        idx = name_to_idx[element_name]

        # Select rays that hit the target element AND every preceding element
        # (object_id 0 … idx-1). rayx does not trace elements sequentially; a
        # ray that scattered off a surface can reach the detector without going
        # through the full optical path. Using the shared path_id we intersect
        # the sets of ray identifiers at each element in the chain, keeping only
        # rays that made it through every step.
        surviving = set(self._rays_df.loc[self._rays_df["object_id"] == idx, "path_id"])
        for preceding in range(idx):
            surviving &= set(self._rays_df.loc[self._rays_df["object_id"] == preceding, "path_id"])

        mask = (self._rays_df["object_id"] == idx) & (self._rays_df["path_id"].isin(surviving))
        df = self._rays_df[mask]

        out = pd.DataFrame(
            {
                f"{element_name}_OX": df["position_x"].values,
                f"{element_name}_OY": df["position_y"].values,
                f"{element_name}_EN": df["energy"].values,
                f"{element_name}_DX": df["direction_x"].values,
                f"{element_name}_DY": df["direction_y"].values,
                f"{element_name}_DZ": df["direction_z"].values,
            }
        )

        filename = os.path.join(export_path, f"{data_prefix}{element_name}-{export_type}.csv")
        with open(filename, "w") as f:
            f.write("# rayx export\n")
            f.write("\t".join(out.columns) + "\n")
        out.to_csv(filename, sep="\t", index=False, header=False, mode="a")
