import numpy as np
import pandas as pd

from .diodes_data.AXUV import AXUV_dict
from .diodes_data.GaAsP import GaAsP_dict


class Diode:
    def __init__(self, diode_dict, conversion_column):
        """
        Initializes the Diode class with a specific CSV file path and conversion column.

        Args:
            diode_filepath (str): Relative path to the CSV file containing diode data.
            conversion_column (str): Column name in the CSV file used for conversion calculations.

        """
        # # Getting the directory of the current script file
        # current_dir = os.path.dirname(__file__)
        # # Building the relative path to the CSV file
        # self.diode_filepath = os.path.join(current_dir, diode_filepath)
        # # Reading the CSV file
        # self.diode = pd.read_csv(self.diode_filepath)

        self.diode = diode_dict
        # Store the column name used for conversion factors
        self.conversion_column = conversion_column

    def check_boundary_conditions(self, energy_keV):
        """
        Checks if the provided energy is below the minimum energy specified in the diode data.

        Args:
            energy_keV (float or np.array): Energy value(s) in keV to check against the diode data.

        Returns:
            np.array: Boolean array where True indicates the energy is below the minimum.
        """
        # Check for energy values less than the minimum energy in the CSV file
        min_energy = self.diode["Energy[keV]"].min()
        return energy_keV < min_energy

    def convert_photons_to_amp(self, energy_eV, n_photons):
        """
        Converts photon counts at specific energy values to electrical current in amperes.

        Args:
            energy_eV (np.array): Array of energy values in electron volts.
            n_photons (np.array): Array of photon counts corresponding to the energies.

        Returns:
            np.array: Array of current values in amperes corresponding to the input photon counts.

        Raises:
            ValueError: If the energy and photon arrays do not have the same number of elements.
        """
        # Ensure both inputs are converted to numpy arrays
        energy_eV = np.atleast_1d(np.asarray(energy_eV))
        n_photons = np.atleast_1d(np.asarray(n_photons))
        # Check if energy_eV and n_photons have the same number of elements
        if energy_eV.shape != n_photons.shape:
            raise ValueError(
                "The 'energy_eV' and 'n_photons' arrays must have the same number of elements."
            )

        # Convert energy from eV to keV
        energy_keV = energy_eV / 1000.0

        # Initialize an array to store conversion factors
        conversion_factors = np.zeros_like(energy_keV, dtype=float)

        # Boundary condition checks
        below_boundary = self.check_boundary_conditions(energy_keV)

        # Calculate conversion factors
        conversion_factors = self.calculate_conversion_factors(energy_keV, below_boundary)

        # Calculate the current in amperes
        current_in_amperes = (
            n_photons / conversion_factors
        ) / 1e9  # Convert from nanoamperes to amperes

        return current_in_amperes

    def calculate_conversion_factors(self, energy_keV, below_boundary):
        """
        Calculates conversion factors photon counts to current.

        Args:
            energy_keV (np.array): Energy values in keV for which to find conversion factors.
            below_boundary (np.array): Array of booleans indicating energies below the
                                        minimum allowed.

        Returns:
            np.array: Array of conversion factors for each energy value.
        """
        conversion_factors = np.zeros_like(energy_keV, dtype=float)
        for i, energy in enumerate(energy_keV):
            if below_boundary[i]:
                conversion_factors[i] = np.nan  # Assign NaN for energies below the minimum
            elif energy in self.diode["Energy[keV]"].values:
                conversion_factors[i] = self.diode.loc[
                    self.diode["Energy[keV]"] == energy, self.conversion_column
                ].iloc[0]
            else:
                # Perform linear interpolation
                conversion_factors[i] = np.interp(
                    energy, self.diode["Energy[keV]"], self.diode[self.conversion_column]
                )
        return conversion_factors


def load_data_from_py_AXUV():
    # Convert the dictionary back to a DataFrame
    df = pd.DataFrame(list(AXUV_dict.items()), columns=["Energy[keV]", "Photon_to_nAmp_BestOf"])
    return df


def load_data_from_py_GaAsP():
    # Convert the dictionary back to a DataFrame
    df = pd.DataFrame(list(GaAsP_dict.items()), columns=["Energy[keV]", "Photon_to_nAmp"])
    return df


class AXUVDiode(Diode):
    def __init__(self):
        """
        Initializes AXUVDiode class.
        """
        axuv = load_data_from_py_AXUV()
        super().__init__(axuv, "Photon_to_nAmp_BestOf")


class GaASPDiode(Diode):
    def __init__(self):
        """
        Initializes GaASPDiode class.
        """
        gaasp = load_data_from_py_GaAsP()
        super().__init__(gaasp, "Photon_to_nAmp")
