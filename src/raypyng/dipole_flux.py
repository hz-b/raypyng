import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker
from matplotlib.ticker import FuncFormatter
from srxraylib.sources.srfunc import sync_ene


def _log_tick_formatter(x, _):
    """Custom formatter for log-scale tick labels with dynamic precision.

    Args:
        x (float): Tick value.
        _ (Any): Unused, required for compatibility with FuncFormatter.

    Returns:
        str: Formatted tick label.
    """
    if x >= 10:
        return f"{x:.0f}"
    elif x >= 0.1:
        return f"{x:.1f}"
    elif x >= 0.01:
        return f"{x:.2f}"
    else:
        return f"{x:.3f}"


class Dipole:
    """Synchrotron dipole radiation spectrum calculator."""

    def __init__(
        self, bending_radius_m=None, magnetic_field_T=None, beam_energy_GeV=2.5, current_A=0.1
    ):
        """Initializes the dipole with beam and magnetic parameters.

        Args:
            bending_radius_m (float or array-like, optional): Bending radius in meters.
            magnetic_field_T (float or array-like, optional): Magnetic field in Tesla.
            beam_energy_GeV (float): Beam energy in GeV.
            current_A (float): Beam current in Amperes.

        Raises:
            ValueError: If both or neither of `bending_radius_m` and `magnetic_field_T`
            are specified.
        """
        self.beam_energy_GeV = beam_energy_GeV
        self.current_A = current_A

        if (bending_radius_m is None) == (magnetic_field_T is None):
            raise ValueError(
                "Specify either 'bending_radius_m' or 'magnetic_field_T', but not both."
            )

        if bending_radius_m is not None:
            self.bending_radii = np.atleast_1d(bending_radius_m)
            self.fields = 3.335 * beam_energy_GeV / self.bending_radii
        else:
            self.fields = np.atleast_1d(magnetic_field_T)
            self.bending_radii = 3.335 * beam_energy_GeV / self.fields

        self.lambda_critical_A = 5.59 * self.bending_radii / beam_energy_GeV**3
        # self.lambda_critical_A = 18.6 / (self.fields * beam_energy_GeV**2)
        self.energy_critical_keV = 12.398 / self.lambda_critical_A
        self.gamma = 1957 * self.energy_critical_keV

    def __repr__(self):
        """String representation of the Dipole object.

        Returns:
            str: Formatted information about dipole parameters.
        """
        out = "Dipole(\n"
        for i, (B, R, Ec, lam, g) in enumerate(
            zip(
                self.fields,
                self.bending_radii,
                self.energy_critical_keV,
                self.lambda_critical_A,
                self.gamma,
                strict=False,
            )
        ):
            out += f"  Case {i+1}:\n"
            out += f"    Magnetic field     = {B:.3f} T\n"
            out += f"    Bending radius     = {R:.3f} m\n"
            out += f"    Critical energy    = {Ec:.3f} keV\n"
            out += f"    Critical wavelength= {lam:.3f} Å\n"
            out += f"    γ (Gamma)          = {g:.2f}\n"
            out += f"    Beam energy         = {self.beam_energy_GeV} GeV\n"
            out += f"    Beam current        = {(self.current_A*1000)} mA\n"
            out += ")"
        return out

    def calculate_spectrum(self, photon_energy_array, hdiv=1):
        """Calculates the photon flux spectrum for the dipole source.

        Args:
            photon_energy_array (np.ndarray): Photon energies in eV.
            hdiv (float or array-like): Horizontal divergence in mrad.
                Can be a scalar (applied uniformly) or an array matching the photon energy array.

        Returns:
            np.ndarray: Array of photon fluxes for each dipole case.
        """
        self.photon_energies = photon_energy_array
        if isinstance(hdiv, int):
            hdiv = np.ones_like(photon_energy_array) * hdiv
        self.all_fluxes = []

        for ec_ev, hdiv_val in zip(self.energy_critical_keV * 1000, hdiv, strict=False):
            flux = sync_ene(
                0,
                photon_energy_array,
                ec_ev=ec_ev,
                polarization=0,
                e_gev=self.beam_energy_GeV,
                i_a=self.current_A,
                hdiv_mrad=hdiv_val,
                psi_min=0.0,
            )
            self.all_fluxes.append(flux)

        return np.array(self.all_fluxes)

    def plot_spectrum(self, show=True, save_path=None, xscale="log", yscale="log"):
        """Plots the dipole radiation spectrum for all cases.

        Args:
            show (bool): If True, display the plot using `plt.show()`.
            save_path (str, optional): Path to save the figure (e.g., 'plot.png').
            xscale (str): X-axis scale, usually 'log' or 'linear'.
            yscale (str): Y-axis scale, usually 'log' or 'linear'.

        Returns:
            tuple: (matplotlib.figure.Figure, matplotlib.axes._subplots.AxesSubplot)
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        for i, flux in enumerate(self.all_fluxes):
            label = f"{self.fields[i]:.1f} T"
            ax.plot(self.photon_energies, flux, label=label)

        ax.set_xlabel("Photon Energy [keV]")
        ax.set_ylabel(f"Photon Flux [photons/s/{self.current_A}/0.1%BW]")
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)

        ax.xaxis.set_major_formatter(FuncFormatter(_log_tick_formatter))
        ax.xaxis.set_minor_formatter(ticker.NullFormatter())

        ax.set_title("Synchrotron Radiation Spectrum for Different Fields")
        ax.legend()
        ax.grid(True, which="both", ls="--")
        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300)
        if show:
            plt.show()

        return fig, ax
