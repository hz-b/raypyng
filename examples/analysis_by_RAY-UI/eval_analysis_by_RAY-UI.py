"""Eval for simulation_analysis_by_RAY-UI.py.

This simulation uses RAY-UI analysis (ScalarBeamProperties), so flux is only
available as transmission efficiency (%). There is no combined CSV, so we read
looper.csv (energy per simulation) and the per-simulation
round_0/<N>_DetectorAtFocus-ScalarBeamProperties.csv files, then plot photon
energy vs bandwidth (energyH_width) and vs efficiency.
"""

import glob
import os

import matplotlib

matplotlib.use("Agg")  # headless: never open a window

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    sim_dir = os.path.join(this_file_dir, "RAYPy_Simulation_RAY-UI")
    oe = "DetectorAtFocus"
    title = "RAY-UI analysis: bandwidth & efficiency vs energy"
    out_png = os.path.join(this_file_dir, "eval_analysis_by_RAY-UI.png")

    looper_path = os.path.join(sim_dir, "looper.csv")
    if not os.path.exists(looper_path):
        raise SystemExit(f"[eval] expected simulation output not found: {looper_path}")
    looper = pd.read_csv(looper_path)
    energy_col = next((c for c in looper.columns if c.endswith("photonEnergy")), None)
    if energy_col is None:
        raise SystemExit(f"[eval] no photonEnergy column in {looper_path}")

    rows = []
    pattern = os.path.join(sim_dir, "round_0", f"*_{oe}-ScalarBeamProperties.csv")
    for path in sorted(glob.glob(pattern)):
        sim_no = int(os.path.basename(path).split("_", 1)[0])
        # First line is "sep=\t"; the real header is the second line.
        sbp = pd.read_csv(path, sep="\t", skiprows=1)
        bw = sbp.get(f"{oe}_energyH_width")
        eff = sbp.get(f"{oe}_efficiency")
        energy = looper.loc[looper["Simulation Number"] == sim_no, energy_col].iloc[0]
        rows.append({
            "PhotonEnergy": float(energy),
            "energyH_width": float(bw.iloc[0]) if bw is not None else np.nan,
            "efficiency": float(eff.iloc[0]) if eff is not None else np.nan,
        })
    if not rows:
        raise SystemExit(f"[eval] no ScalarBeamProperties files under {pattern}")
    df = pd.DataFrame(rows).sort_values("PhotonEnergy").reset_index(drop=True)

    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    axs[0].plot(df["PhotonEnergy"], df["energyH_width"], marker=".")
    axs[0].set(xlabel="Photon energy [eV]", ylabel="Bandwidth [eV]", title=title)
    axs[1].plot(df["PhotonEnergy"], df["efficiency"], marker=".", color="tab:orange")
    axs[1].set(xlabel="Photon energy [eV]", ylabel="Transmission efficiency [%]",
               title="Efficiency vs photon energy")
    for ax in axs:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print("[eval] saved:", out_png)
