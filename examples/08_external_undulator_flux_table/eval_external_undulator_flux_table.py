import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))

    undulator = pd.read_csv(
        os.path.join(
            this_file_dir,
            "..",
            "undulator",
            "undulator_harmonics_energy_photons.csv",
        )
    )
    detector = pd.read_csv(
        os.path.join(
            this_file_dir,
            "RAYPy_Simulation_external_undulator_flux_table",
            "DetectorAtFocus_RawRaysOutgoing.csv",
        )
    ).sort_values("PhotonEnergy")

    fig, axs = plt.subplots(2, 1, figsize=(10, 9), sharex=True)
    xmin = detector["PhotonEnergy"].min()
    xmax = detector["PhotonEnergy"].max()

    axs[0].plot(undulator["Energy1[eV]"], undulator["Photons1"], label="H1")
    axs[0].plot(undulator["Energy3[eV]"], undulator["Photons3"], label="H3")
    axs[0].set(
        ylabel="Photons at source [ph/s/0.1%BW]",
        title="Undulator harmonics from the supplied table",
    )
    axs[0].set_xlim(xmin, xmax)
    axs[0].grid(True, alpha=0.3)
    axs[0].legend()

    axs[1].plot(
        detector["PhotonEnergy"],
        detector["FluxPerMilPerBwAbs1"],
        marker="o",
        label="H1 at DetectorAtFocus",
    )
    axs[1].plot(
        detector["PhotonEnergy"],
        detector["FluxPerMilPerBwAbs3"],
        marker="o",
        label="H3 at DetectorAtFocus",
    )
    axs[1].set(
        xlabel="Photon energy [eV]",
        ylabel="Flux at DetectorAtFocus [ph/s/0.1%BW]",
        title="Beamline result read directly from the recap CSV",
    )
    axs[1].set_xlim(xmin, xmax)
    axs[1].grid(True, alpha=0.3)
    axs[1].legend()

    fig.tight_layout()
    out_png = os.path.join(this_file_dir, "eval_external_undulator_flux_table.png")
    fig.savefig(out_png, dpi=150)
    print("[eval] saved:", out_png)
