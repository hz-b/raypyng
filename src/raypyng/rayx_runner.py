import os

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


class RayXAPI:
    """Thin wrapper around rayx that mirrors the RayUIAPI load/trace/export interface."""

    def __init__(self):
        self._beamline = None
        self._rays_df = None

    def load(self, rml_path):
        rayx = _require_rayx()
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
        if export_type not in ("RawRaysOutgoing", "RawRaysIncoming"):
            raise NotImplementedError(
                f"RAYX engine only supports RawRaysOutgoing (got '{export_type}')"
            )

        name_to_idx = {el.name: i for i, el in enumerate(self._beamline.elements)}
        if element_name not in name_to_idx:
            raise ValueError(
                f"Element '{element_name}' not found in beamline. "
                f"Available: {list(name_to_idx)}"
            )

        mask = self._rays_df["object_id"] == name_to_idx[element_name]
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
