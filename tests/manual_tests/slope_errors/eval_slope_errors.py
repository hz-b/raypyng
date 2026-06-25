"""Eval for simulation_slope_errors.py.

Photon energy vs bandwidth and flux (ph/s when source flux is known, else %),
one curve per cFactor. The scan also varies slope errors per simulation; this
view focuses on the energy/bandwidth/flux trend.
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never open a window

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    csv_path = os.path.join(this_file_dir, "RAYPy_Simulation_SlopeErrors",
                            "DetectorAtFocus_RawRaysOutgoing.csv")
    group_col = "PG.cFactor"
    title = "slope_errors: bandwidth & flux vs energy"

    if not os.path.exists(csv_path):
        raise SystemExit(f"[eval] expected analysis CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)

    # Prefer absolute flux in ph/s; fall back to a percentage measure.
    def first_nonzero(names):
        for n in names:
            if n in df.columns and np.nanmax(np.abs(pd.to_numeric(df[n], errors="coerce"))) > 0:
                return n
        return None

    abs_col = first_nonzero(["FluxPerMilPerBwAbs", "PhotonFlux"])
    if abs_col == "FluxPerMilPerBwAbs":
        flux_col, flux_label = abs_col, "Flux per 0.1%BW [ph/s]"
    elif abs_col == "PhotonFlux":
        flux_col, flux_label = abs_col, "Photon flux [ph/s]"
    else:
        flux_col = first_nonzero(["FluxPerMilPerBwPerc", "PercentageRaysSurvived"]) \
            or "PercentageRaysSurvived"
        flux_label = "Flux per 0.1%BW [%]" if flux_col == "FluxPerMilPerBwPerc" \
            else "Rays survived [%]"

    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    if group_col and group_col in df.columns and df[group_col].nunique() > 1:
        groups = sorted(df[group_col].unique())
    else:
        group_col, groups = None, [None]

    for g in groups:
        sub = df if g is None else df[df[group_col] == g]
        sub = sub.sort_values("PhotonEnergy")
        label = None if g is None else f"{group_col} = {g}"
        axs[0].plot(sub["PhotonEnergy"], sub["Bandwidth"], marker=".", label=label)
        axs[1].plot(sub["PhotonEnergy"], sub[flux_col], marker=".", label=label)

    axs[0].set(xlabel="Photon energy [eV]", ylabel="Bandwidth [eV]", title=title)
    axs[1].set(xlabel="Photon energy [eV]", ylabel=flux_label, title="Flux vs photon energy")
    for ax in axs:
        ax.grid(True, alpha=0.3)
    if group_col:
        axs[0].legend()
        axs[1].legend()
    fig.tight_layout()
    out_png = os.path.join(this_file_dir, "eval_slope_errors.png")
    fig.savefig(out_png, dpi=150)
    print("[eval] saved:", out_png)
