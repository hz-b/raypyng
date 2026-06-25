"""Eval for simulation_permil.py.

Per-0.1%-bandwidth (per-mil) analysis: energy/bandwidth, transmission per 0.1%BW
in percent, and absolute flux per 0.1%BW in ph/s — one curve per grating.
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless: never open a window

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

this_file_dir = os.path.dirname(os.path.realpath(__file__))
simulation_folder = os.path.join(this_file_dir, "RAYPy_Simulation_Permil")
# loading the data at the DetectorAtFocus
oe = "DetectorAtFocus" + "_RawRaysOutgoing.csv"
data = pd.read_csv(os.path.join(simulation_folder, oe))

fig, (axs) = plt.subplots(3, 1, figsize=(15, 10))

# PerMil Bandwidth
axs[0].set_xlabel("Energy [keV]")
axs[0].set_ylabel("E/1000/bandwidth")
axs[0].set_title("Energy / 0.1% bandwidth")

# PerMil Flux %
axs[1].set_xlabel("Energy [eV]")
axs[1].set_ylabel("Flux Per 0.1%BW [%]")
axs[1].set_title("Transmission Per 0.1% bandwidth [%]")

# PerMil Flux absolute
axs[2].set_xlabel("Energy [eV]")
axs[2].set_ylabel("Flux PerMil [ph/sec/0.1BW]")
axs[2].set_title("Transmission Per 0.1% bandwidth")

for grating in [400, 1200]:
    data_plot = data[data["PG.lineDensity"] == grating]
    axs[0].plot(data_plot["PhotonEnergy"] / 1000, data_plot["EnergyPerMilPerBw"],
                label=f"grating {grating} l/mm")
    axs[1].plot(data_plot["PhotonEnergy"], data_plot["FluxPerMilPerBwPerc"])
    axs[2].plot(data_plot["PhotonEnergy"], data_plot["FluxPerMilPerBwAbs"])

axs[0].legend()
plt.tight_layout()
out_png = os.path.join(this_file_dir, "eval_permil.png")
plt.savefig(out_png)
print("[eval] saved:", out_png)
