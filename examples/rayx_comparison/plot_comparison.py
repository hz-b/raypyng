"""Compare RAY-UI vs RAYX simulation results for the dipole beamline.

Run simulation_rayui.py and simulation_rayx.py first to generate the data.
Produces comparison_plots.png in this folder.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

this_dir = os.path.dirname(os.path.realpath(__file__))

# ── Load results ──────────────────────────────────────────────────────────────

def load(sim_name, element, export_type="RawRaysOutgoing"):
    path = os.path.join(
        this_dir, f"RAYPy_Simulation_{sim_name}", f"{element}_{export_type}.csv"
    )
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing: {path}\n"
            f"Run simulation_{sim_name}.py first."
        )
    df = pd.read_csv(path, index_col=0)
    df.columns = df.columns.str.strip()
    return df


rayui_det = load("rayui", "DetectorAtFocus")
rayx_det  = load("rayx",  "DetectorAtFocus")

energy_col  = "Dipole.photonEnergy"
slit_col    = "ExitSlit.totalHeight"
slit_values = sorted(rayui_det[slit_col].unique())

# ── Plot ──────────────────────────────────────────────────────────────────────

metrics = [
    ("PercentageRaysSurvived", "Throughput (%)"),
    ("HorizontalFocusFWHM",   "Horizontal focus FWHM (mm)"),
    ("VerticalFocusFWHM",     "Vertical focus FWHM (mm)"),
    ("Bandwidth",             "Bandwidth (eV)"),
]

n_rows = len(metrics)
fig, axes = plt.subplots(n_rows, 1, figsize=(9, 3.5 * n_rows), sharex=True)
fig.suptitle("RAY-UI vs RAYX — dipole beamline (DetectorAtFocus)", fontsize=13)

# Colour and linestyle per (engine, slit)
colors    = ["C0", "C1"]
rayui_ls  = "-"
rayx_ls   = "--"

for ax, (col, ylabel) in zip(axes, metrics):
    for i, slit in enumerate(slit_values):
        mask_ui = rayui_det[slit_col] == slit
        mask_rx = rayx_det[slit_col]  == slit

        label_ui = f"RAY-UI  slit={slit}"
        label_rx = f"RAYX    slit={slit}"

        ax.plot(
            rayui_det.loc[mask_ui, energy_col],
            rayui_det.loc[mask_ui, col],
            color=colors[i], ls=rayui_ls, marker="o", ms=4, label=label_ui,
        )
        ax.plot(
            rayx_det.loc[mask_rx, energy_col],
            rayx_det.loc[mask_rx, col],
            color=colors[i], ls=rayx_ls, marker="s", ms=4, label=label_rx,
        )

    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, ncol=2)

axes[-1].set_xlabel("Photon energy (eV)")

fig.tight_layout()
out = os.path.join(this_dir, "comparison_plots.png")
fig.savefig(out, dpi=150)
print(f"Saved: {out}")
plt.show()
