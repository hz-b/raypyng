"""Plot photon energy vs bandwidth and flux for the raypyng example."""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never open a window

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    csv_path = os.path.join(
        this_file_dir,
        "RAYPy_Simulation_raypyng",
        "DetectorAtFocus_RawRaysOutgoing.csv",
    )
    df = pd.read_csv(csv_path)
    title = "raypyng: bandwidth and flux vs energy"
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    for slit_size in sorted(df["ExitSlit.totalHeight"].unique()):
        sub = df[df["ExitSlit.totalHeight"] == slit_size]
        sub = sub.sort_values("PhotonEnergy")
        label = f"ExitSlit.totalHeight = {slit_size}"
        axs[0].plot(sub["PhotonEnergy"], sub["Bandwidth"], marker=".", label=label)
        axs[1].plot(sub["PhotonEnergy"], sub["PhotonFlux"], marker=".", label=label)

    axs[0].set(xlabel="Photon energy [eV]", ylabel="Bandwidth [eV]", title=title)
    axs[1].set(xlabel="Photon energy [eV]", ylabel="Photon flux [ph/s]", title="Flux vs photon energy")
    for ax in axs:
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    out_png = os.path.join(this_file_dir, "eval_raypyng.png")
    fig.savefig(out_png, dpi=150)
    print("[eval] saved:", out_png)
