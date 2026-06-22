"""Minimal rayx example: load a beamline, trace it, save rays at DetectorAtFocus."""

import os
import rayx
import rayx.core as rc

if __name__ == "__main__":
    this_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_dir, "../rayx_comparison/test_dipole.rml")

    # load and trace
    beamline = rc.import_beamline(rml_file)
    rays = beamline.trace()
    df = rayx.rays_to_df(rays)

    # find DetectorAtFocus index
    names = [el.name for el in beamline.elements]
    print("Elements:", names)
    idx = names.index("DetectorAtFocus")

    # filter rays that hit the detector
    det_df = df[df["object_id"] == idx].reset_index(drop=True)
    print(f"Rays at DetectorAtFocus: {len(det_df)}")
    print(det_df[["position_x", "position_y", "position_z", "energy"]].head())

    # save
    out = os.path.join(this_dir, "DetectorAtFocus_rays.csv")
    det_df.to_csv(out, index=False)
    print(f"Saved: {out}")
