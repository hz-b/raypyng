"""Plot detector-at-focus bandwidth and transmission efficiency vs photon energy."""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never open a window

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    sim_dir = os.path.join(this_file_dir, "RAYPy_Simulation_RAY-UI")
    title = "ExitSlit: bandwidth & transmission efficiency vs energy"
    out_png = os.path.join(this_file_dir, "eval_analysis_by_RAY-UI.png")
    recap_path = os.path.join(sim_dir, "ExitSlit_ScalarBeamProperties.csv")

    df = pd.read_csv(recap_path)
    df = df[
        [
            "Dipole.photonEnergy",
            "ExitSlit_energyH_width",
            "ExitSlit_efficiency",
        ]
    ].apply(pd.to_numeric, errors="coerce")
    df = df.sort_values("Dipole.photonEnergy").reset_index(drop=True)

    fig, axs = plt.subplots(1, 1, figsize=(10, 8))
    axs.plot(
        df["Dipole.photonEnergy"],
        df["ExitSlit_energyH_width"],
        marker=".",
        color="tab:blue",
    )
    axs.set(
        xlabel="Photon energy [eV]",
        ylabel="Bandwidth [eV]",
        title=title,
    )

    axs.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print("[eval] saved:", out_png)
