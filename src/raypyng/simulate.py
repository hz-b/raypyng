import csv
import itertools
import json
import logging
import multiprocessing
import os
import re
import shutil
import signal
import sys
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

import numpy as np
import pandas as pd
import psutil
from tqdm import tqdm

from .helper_functions import RingBuffer
from .postprocessing import PostProcess
from .recipes import SimulationRecipe
from .rml import ObjectElement, ParamElement, RMLFile
from .runner import RayUIAPI, RayUIRunner

_RAWRAYS_ITEM_IDS = frozenset({"RawRaysOutgoing", "RawRaysIncoming", "RawRaysBeam"})


def _write_rawrays_csv(raw_array, element_name: str, csv_path: str) -> None:
    """Write a rawdata numpy structured array to a tab-separated CSV file.

    Produces the same format that RAY-UI used to write directly, with a sep=\\t
    compatibility header and element-prefixed column names.
    """
    df = pd.DataFrame({f"{element_name}_{col}": raw_array[col] for col in raw_array.dtype.names})
    with open(csv_path, "w") as f:
        f.write("sep=\t\n")
        df.to_csv(f, sep="\t", index=False)


_ETA_NRAYS_CALIBRATION_POINTS = (
    (1.0e4, 2.6),
    (5.0e4, 2.8),
    (1.0e5, 3.9),
    (5.0e5, 16.5),
)
_ETA_SAFETY_FACTOR = 4.0
_ETA_MIN_SECONDS = 5.0


class _ReadOnlyList(list):
    """List-like view that raises on in-place mutation.

    Simulate.params and Simulate.exports rely on setter-side validation and
    derived-state recomputation, so mutating the returned value directly is unsafe.
    """

    def __init__(self, iterable, property_name):
        super().__init__(iterable)
        self._property_name = property_name

    def _raise(self):
        raise TypeError(
            f"In-place mutation of '{self._property_name}' is not supported. "
            f"Assign a new list instead, for example: "
            f"sim.{self._property_name} = sim.{self._property_name} + [new_item]"
        )

    def append(self, item):
        self._raise()

    def extend(self, iterable):
        self._raise()

    def insert(self, index, item):
        self._raise()

    def pop(self, index=-1):
        self._raise()

    def remove(self, item):
        self._raise()

    def clear(self):
        self._raise()

    def reverse(self):
        self._raise()

    def sort(self, *args, **kwargs):
        self._raise()

    def __setitem__(self, key, value):
        self._raise()

    def __delitem__(self, key):
        self._raise()

    def __iadd__(self, other):
        self._raise()

    def __imul__(self, other):
        self._raise()


################################################################
class SimulationParams:
    """Handles the setup and management of simulation parameters for RAY-UI simulations.

    This class is responsible for organizing simulation parameters, both independent and dependent,
    and generating the necessary parameter sets for conducting simulations.

    Attributes:
        rml (RMLFile or str): The RML file or the path to the RML file used as the template
                            for simulations.
        params (list of dict):  A list of dictionaries where each dictionary represents a
                                set of parameters to simulate. Each key in the dictionary
                                is a ParamElement, and its value is the parameter value(s)
                                to simulate.
    """

    def __init__(self, rml=None, param_list=None, **kwargs) -> None:
        """Initializes the SimulationParams class with a RML file and a list
        of parameter dictionaries.

        Args:
            rml (RMLFile or str, optional): The RML file or the path to the RML
                                    file used as the template for simulations.
            param_list (list of dict, optional): A list of dictionaries where each
                                    dictionary represents a set of parameters
                                    to simulate. Defaults to None.
        """
        self._rml = self._initialize_rml(
            rml, **kwargs
        )  # Initializes the RML file or RMLFile object
        self.params = param_list or []  # List of dictionaries for parameters to simulate
        self.ind_param_values = []  # Independent parameter values for simulations
        self.ind_par = []  # Independent parameters
        self.dep_param_dependency = []  # Dependencies between parameters
        self.dep_value_dependency = []  # Values dependent on other parameters
        self.dep_par = []  # Dependent parameters

    def _initialize_rml(self, rml, **kwargs):
        """Initializes the RML file or RMLFile object based on the provided RML path or object.

        Args:
            rml (RMLFile or str): The RML file or the path to the RML file used as
                                    the template for simulations.

        Returns:
            RMLFile: An initialized RMLFile object.
        """
        if rml is None:
            raise ValueError("An RML file or RMLFile object must be provided.")
        elif isinstance(rml, RMLFile):
            return rml
        elif isinstance(rml, str):
            return RMLFile(rml, **kwargs)
        else:
            raise ValueError(
                f"The rml should be either a string point to n rml file or \
                an instance of the RMLFile class. You passed a {type(rml)}"
            )

    @property
    def rml(self):
        return self._rml

    @property
    def params(self):
        return _ReadOnlyList(self._params, "params")

    @params.setter
    def params(self, value):
        copied_value = self._copy_params_list(value)
        self._validate_params(copied_value)
        self._params = copied_value
        self._extract_param()

    def _copy_params_list(self, value):
        if not isinstance(value, list):
            return value

        copied_params = []
        for item in value:
            if not isinstance(item, dict):
                copied_params.append(item)
                continue

            copied_item = {}
            for key, param_value in item.items():
                if isinstance(param_value, list):
                    copied_item[key] = list(param_value)
                elif isinstance(param_value, (float, int, str)):
                    copied_item[key] = param_value
                elif hasattr(param_value, "__iter__"):
                    copied_item[key] = list(param_value)
                else:
                    copied_item[key] = param_value
            copied_params.append(copied_item)

        return copied_params

    def _validate_params(self, value):
        """Validates the input parameter list to ensure it is in the correct format.

        Args:
            value (list): The parameter list to be validated.

        Raises:
            TypeError: If the input value is not a list or if the elements of the
                        list are not dictionaries.
        """
        if not isinstance(value, list):
            raise TypeError("params must be a list")
        for item in value:
            if not isinstance(item, dict):
                raise TypeError("Each element in params must be a dictionary")
            self._validate_param_keys_values(item)

    def _validate_param_keys_values(self, param):
        """Validates the keys and values of a parameter dictionary.

        Args:
            param (dict): The parameter dictionary to be validated.

        Raises:
            TypeError: If the keys are not instances of ParamElement or
                        if the values are not valid types.
        """
        for key, value in param.items():
            if not isinstance(key, ParamElement):
                raise TypeError(f"Keys must be ParamElement instances, found {type(key)}")
            self._validate_value_type(param, value, key)

    def _validate_value_type(self, param, value, key):
        if not isinstance(value, (list, float, int, str)) and not hasattr(value, "__iter__"):
            raise TypeError(f"Invalid type for parameter {key}: {type(value)}")
        if not isinstance(value, list):
            param[key] = [value] if isinstance(value, (float, int, str)) else list(value)

    def compute_skip_factors(self, skip_params):
        result = [1] * len(skip_params)
        for i in range(len(skip_params) - 2, -1, -1):
            result[i] = skip_params[i + 1] * result[i + 1]
        if result:
            result[-1] = 0
        return result

    def _extract_param(self):
        """Extracts and organizes parameters from the input parameter list.

        Returns:
            tuple: A tuple containing the organized parameters and their values.
        """
        self._reset_extraction_variables()

        skip_params = []
        self.count_dep_params = 0

        for parameters_dict in self.params:
            if len(parameters_dict.keys()) > 1:
                skip_params.append(len(next(iter(parameters_dict.values()))))
        self.skip_params = self.compute_skip_factors(skip_params)
        for parameters_dict in self.params:
            self._process_parameter_dict(parameters_dict)

    def _reset_extraction_variables(self):
        """Reset or initialize variables for a new extraction."""
        self.ind_param_values, self.ind_par = [], []
        self.dep_param_dependency, self.dep_value_dependency, self.dep_par = {}, [], []

    def _validate_dependency_length(self, parameters_dict, independent_key, dependent_key):
        """Ensure dependent parameters match the length of their independent counterparts."""
        if len(parameters_dict[dependent_key]) != len(parameters_dict[independent_key]):
            raise ValueError(f"Dependent parameter lengths do not match for {dependent_key}.")

    def _get_dependency_indices(self):
        """Get indices of independent parameters that dependent parameters rely on."""
        return [self.ind_par.index(dep) for dep in self.dep_param_dependency.values()]

    def _check_if_enabled(self, param):
        """Check if a parameter is enabled

        Args:
            param (RML object): an parameter to simulate

        Returns:
            (bool): True if the parameter is enabled, False otherwise
        """
        return param.enabled == "T"

    def _enable_param(self, param):
        """Set :code:`enabled='T'` and :code:`auto='F'` in a beamline object

        Args:
            param (RML object): beamline object
        """
        if not self._check_if_enabled(param):
            param.enabled = "T"
        try:
            param.auto = "F"
        except AttributeError:
            pass

    def _write_value_to_param(self, param, value):
        """Write a value to a parameter.

        Additionally it makes sure that enable is T
        and auto is F

        Args:
            param (RML object): beamline object
            value (str,int,float): the value to set the beamline object to
        """
        self._enable_param(param)
        if not isinstance(value, str):
            value = str(value)
        param.cdata = value

    def _calc_number_sim(self):
        """Calculates the total number of simulations based on the provided parameters.

        Returns:
            int: The total number of simulations.
        """
        from functools import reduce
        from operator import mul

        sim_per_round = reduce(mul, (len(value_list) for _, value_list in self.ind_param_values), 1)
        return sim_per_round

    def _process_parameter_dict(self, parameters_dict):
        """Process each dictionary of parameters."""
        keys = list(parameters_dict.keys())
        items = list(parameters_dict.items())

        # First key is always considered independent
        independent_param = keys[0]
        independent_values = items[0][1]
        self.ind_par.append(independent_param)
        self.ind_param_values.append((independent_param, independent_values))

        # If no dependent params, nothing else to do
        if len(keys) == 1:
            return

        # Register dependent param relationships
        for dep_param in keys[1:]:
            self.dep_param_dependency[dep_param] = independent_param
            if dep_param not in self.dep_par:
                self.dep_par.append(dep_param)

        # Create list of ring buffer
        num_values = len(independent_values)
        for dep_param in keys[1:]:
            self.dep_value_dependency.append(
                RingBuffer(skip=self.skip_params[self.count_dep_params])
            )
            index = len(self.dep_value_dependency) - 1
            for i in range(num_values):
                dep_value = parameters_dict[dep_param][i]
                self.dep_value_dependency[index].add(dep_value)
        self.count_dep_params += 1

    def simulation_parameters_generator(self):
        """Generates a dictionary of parameters for each simulation
        based on the input parameter list.

        Yields:
            dict: A dictionary of parameters for a single simulation.
        """

        # Unpack independent parameters and their value lists
        keys, value_lists = zip(*self.ind_param_values, strict=False)

        # Generate all combinations of independent values
        self._calc_number_sim()
        # Loop through each simulation index
        for values_combination in itertools.product(*value_lists):
            # Start with independent parameters
            simulation_params = dict(zip(keys, values_combination, strict=False))
            if self.dep_par:
                for value_index, dep_par in enumerate(self.dep_par):
                    simulation_params[dep_par] = self.dep_value_dependency[value_index].next()
            yield simulation_params


################################################################
class Simulate:
    """A class that takes care of performing the simulations with RAY-UI

    Args:
        rml (RMLFile/string, optional): string pointing to an rml file with
                                        the beamline template, or an RMLFile
                                        class object. Defaults to None.
        hide (bool, optional): force hiding of GUI leftovers, xvfb needs
                               to be installed. Defaults to False.
        ray_path (str, optional): the path to the RAY-UI installation folder.
                                  If None, the program will look for RAY-UI in
                                  the standard installation paths.
    """

    def __init__(
        self,
        rml=None,
        hide=False,
        ray_path=None,
        engine="ray-ui",
        graxpy_efficiency=False,
        graxpy_fourier_orders=15,
        graxpy_x_resolution_nm=0.1,
        graxpy_z_resolution_nm=0.1,
        **kwargs,
    ) -> None:
        """Initialize the class with a rml file

        Args:
            rml (RMLFile/string, optional): string pointing to an rml file with
                                            the beamline template, or an RMLFile
                                            class object. Defaults to None.
            hide (bool, optional): force hiding of GUI leftovers, xvfb needs
                                   to be installed. Defaults to False.
            ray_path (str, optional): the path to the RAY-UI installation folder.
                                      If None, the program will look for RAY-UI in
                                      the standard installation paths.
            engine (str, optional): simulation engine to use. ``"ray-ui"`` (default)
                                    or ``"rayx"`` (requires ``pip install rayx``).
            graxpy_efficiency (bool, optional): compute grating diffraction efficiency
                                                using graxpy after each simulation.
                                                Requires ``pip install raypyng[graxpy]``.
                                                Defaults to False.
            graxpy_fourier_orders (int, optional): number of Fourier orders for the
                                                   graxpy RCWA solve. Defaults to 15.
            graxpy_x_resolution_nm (float, optional): horizontal profile discretisation
                                                       resolution in nm. Defaults to 0.1.
            graxpy_z_resolution_nm (float, optional): vertical profile discretisation
                                                      resolution in nm. Defaults to 0.1.

        Raises:
            Exception: If the rml file is not defined an exception is raised
        """
        if rml is not None:
            if isinstance(rml, RMLFile):
                self._rml = rml
            else:  # assume that parameter is the file name as required for RMLFile
                self._rml = RMLFile(None, template=rml)
        else:
            raise Exception("rml file must be defined")

        self._rml = (
            rml if isinstance(rml, RMLFile) else RMLFile(None, template=rml) if rml else None
        )
        self.path = None  # Path for simulation execution
        self.prefix = "RAYPy_Simulation"  # Simulation prefix
        self._hide = hide  # Hide GUI leftovers
        self._engine = engine  # Simulation engine ("ray-ui" or "rayx")
        self.analyze = True  # Enable RAY-UI analysis
        self._repeat = 1  # Number of simulation repeats
        self.raypyng_analysis = False  # Enable RAYPyNG analysis
        self.ray_path = ray_path  # RAY-UI installation path
        self.overwrite_rml = True  # Overwrite RML files
        self._sim_folder = None  # Simulation folder name
        self.batch_size = 50
        self._simulation_timeout = 20.0  # max idle secs; updated live in _wait_for_simulation_batch
        self._batch_number = None

        self._simulation_name = None  # Custom simulation name
        self._exports = []  # Files to export after simulation
        self._exports_list = []  # Processed list of exports
        self._undulator_table = None  # holder for undulator table pandas dataframe
        self._efficiency = None  # holder for efficiency pandas dataframe
        self.sp = None  # SimulationParams instance
        self.sim_list_path = []  # Paths to RML files
        self.sim_path = None  # Simulation directory path
        self.durations = []  # Durations of simulations
        self.remove_rawrays = False  # remove or not the rawrays files
        self.total_duration = None  # Total duration of all simulations
        self.completed_simulations = None  # Count of completed simulations
        self._possible_exports = [
            "AnglePhiDistribution",  # possible exports when RAY-UI analysis is active
            "AnglePsiDistribution",
            "BeamPropertiesPlotSnapshot",
            "EnergyDistribution",
            "FootprintAbsorbedRays",
            "FootprintAllRays",
            "FootprintOutgoingRays",
            "FootprintPlotSnapshot",
            "FootprintWastedRays",
            "Intensity2D",
            "IntensityPlotSnapshot",
            "IntensityX",
            "IntensityYZ",
            "PathlengthDistribution",
            "RawRaysBeam",
            "RawRaysIncoming",
            "RawRaysOutgoing",
            "ScalarBeamProperties",
            "ScalarElementProperties",
        ]
        self._possible_exports_without_analysis = [
            "RawRaysIncoming",  # possible exports when RAY-UI analysis is not active
            "RawRaysOutgoing",
        ]
        self.graxpy_efficiency = graxpy_efficiency
        self.graxpy_fourier_orders = graxpy_fourier_orders
        self.graxpy_x_resolution_nm = graxpy_x_resolution_nm
        self.graxpy_z_resolution_nm = graxpy_z_resolution_nm

    @property
    def possible_exports(self):
        """A list of the files that can be exported by RAY-UI

        Returns:
            list: list of the names of the possible exports for RAY-UI
        """
        return self._possible_exports

    @property
    def possible_exports_without_analysis(self):
        """A list of the files that can be exported by RAY-UI when the
        analysis option is turned off

        Returns:
            list: list of the names of the possible exports for RAY-UI when analysis is off
        """
        return self._possible_exports_without_analysis

    @property
    def rml(self):
        """RMLFile object instantiated in init"""
        return self._rml

    @property
    def simulation_name(self):
        """A string to append to the folder where the simulations will be executed."""
        return self._simulation_name

    @simulation_name.setter
    def simulation_name(self, value):
        self._simulation_name = value
        self._sim_folder = self.prefix + "_" + self._simulation_name

    @property
    def analyze(self):
        """Turn on or off the RAY-UI analysis of the results.
        The analysis of the results takes time, so turn it on only if needed

        Returns:
            bool: True: analysis on, False: analysis off
        """
        return self._analyze

    @analyze.setter
    def analyze(self, value):
        if not isinstance(value, bool):
            raise ValueError("Only bool are allowed")
        self._analyze = value

    @property
    def raypyng_analysis(self):
        """Turn on or off the RAYPyNG analysis of the results.

        Returns:
            bool: True: analysis on, False: analysis off
        """
        return self._raypyng_analysis

    @raypyng_analysis.setter
    def raypyng_analysis(self, value):
        if not isinstance(value, bool):
            raise ValueError("Only bool are allowed")
        self._raypyng_analysis = value

    @property
    def repeat(self):
        """The simulations can be repeated an arbitrary number of times

        If the statitcs are not good enough using 2 millions of rays is suggested
        to repeat them instead of increasing the number of rays

        Returns:
            int: the number of repetition of the simulations, by default is 1
        """
        return self._repeat

    @repeat.setter
    def repeat(self, value):
        if not isinstance(value, int):
            raise ValueError("Only int are allowed")
        self._repeat = value

    @property
    def path(self):
        """The path where to execute the simlations

        Returns:
            string: by default the path is the current path from which
            the program is executed
        """
        return self._path

    @path.setter
    def path(self, value):
        if value is None:
            value = os.getcwd()
        if not isinstance(value, str):
            raise ValueError("Only str are allowed")
        if not os.path.exists(value):
            raise ValueError("The path does not exist")
        self._path = value

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        if not isinstance(value, str):
            raise ValueError("Only str are allowed")
        self._prefix = value

    @property
    def efficiency(self):
        """The parameters to scan, as a list of dictionaries.

        For each dictionary the keys are the parameters elements
        of the beamline, and the values are the
        values to be assigned.
        """

        return self._efficiency

    @efficiency.setter
    def efficiency(self, value):
        self._validate_efficiency(value)
        self._efficiency = value

    def _validate_efficiency(self, value):
        # Check if the value is an instance of pandas DataFrame
        if not isinstance(value, pd.DataFrame):
            raise TypeError("The efficiency must be a pandas DataFrame.")

        # Check that the column names are "Efficiency" and 'Energy[eV]'
        required_columns = {"Efficiency", "Energy[eV]"}
        if not required_columns.issubset(value.columns):
            raise ValueError(
                f"The DataFrame must contain the following \
                             columns: {required_columns}"
            )

    @property
    def undulator_table(self):
        """The undulator table, as a pandas DataFrame."""

        return self._undulator_table

    @undulator_table.setter
    def undulator_table(self, value):
        self._validate_undulator_table(value)
        self._undulator_table = value

    def _validate_undulator_table(self, value):
        # check that source is not Dipole or Undulator File
        for oe in self._rml.beamline.children():
            if hasattr(oe, "numberRays"):
                if oe["type"] == "Dipole" or oe["type"] == "Undulator File":
                    raise Exception(
                        f'The undulator table can not be used with source type \
                        "Dipole" and "Undulator File", the source type in the rml \
                        file is {oe["type"]}'
                    )

        # Check if the value is an instance of pandas DataFrame
        if not isinstance(value, pd.DataFrame):
            raise TypeError("The undulator_table must be a pandas DataFrame.")

        # Check if the number of columns is even
        num_columns = value.shape[1]  # shape[1] returns the number of columns
        if num_columns % 2 != 0:
            raise ValueError("The DataFrame must have an even number of columns.")

        # Validate column names according to specified patterns
        for i in range(0, num_columns, 2):  # Iterate over even indices representing odd columns
            expected_energy_name = f"Energy{2 * (i // 2 + 1) - 1}[eV]"
            expected_harmonic_name = f"Photons{2 * (i // 2 + 1) - 1}"
            if value.columns[i + 1] != expected_harmonic_name:
                raise ValueError(
                    f"Expected column {i} to be named '{expected_harmonic_name}',\
                          but got '{value.columns[i]}'."
                )

            if value.columns[i] != expected_energy_name:
                raise ValueError(
                    f"Expected column {i + 1} to be named '{expected_energy_name}', \
                        but got '{value.columns[i + 1]}'."
                )

    @property
    def exports(self):
        """Get the list of files to export after the simulation is complete."""
        copied_exports = []
        for export_dict in self._exports:
            copied_exports.append(
                {
                    object_element: list(export_files)
                    for object_element, export_files in export_dict.items()
                }
            )
        return _ReadOnlyList(copied_exports, "exports")

    @exports.setter
    def exports(self, value):
        """
        Validates and sets the exports list for simulation results.

        Args:
            value (list): A list of dictionaries specifying the exports configuration.

        Raises:
            TypeError: If the input is not a list or the contents of the list are not as expected.
        """
        copied_value = self._copy_export_list(value)
        self._validate_export_list(copied_value)
        self._exports = copied_value
        self._exports_list = self._generate_exports_list(copied_value)

    def _copy_export_list(self, value):
        if not isinstance(value, list):
            return value

        copied_exports = []
        for export_dict in value:
            if not isinstance(export_dict, dict):
                copied_exports.append(export_dict)
                continue

            copied_exports.append(
                {
                    object_element: (
                        list(export_files) if isinstance(export_files, list) else export_files
                    )
                    for object_element, export_files in export_dict.items()
                }
            )
        return copied_exports

    def _validate_export_list(self, export_list):
        """
        Validates that the provided export list is properly formatted.

        Args:
            export_list (list): The exports list to validate.

        Raises:
            TypeError: If the export list is not a list or contains non-dictionary items.
        """
        if not isinstance(export_list, list):
            raise TypeError("The exports must be a list.")
        for export_dict in export_list:
            self._validate_export_dict(export_dict)

    def _validate_export_dict(self, export_dict):
        """
        Validates that each dictionary in the export list is correctly structured.

        Args:
            export_dict (dict): A dictionary representing an export configuration.

        Raises:
            TypeError: If the export configuration is not a dictionary or has
                        incorrect key/value types.
        """
        if not isinstance(export_dict, dict):
            raise TypeError("Each export configuration must be a dictionary.")
        for object_element, export_files in export_dict.items():
            self._validate_export_entry(object_element, export_files)

    def _validate_export_entry(self, object_element, export_files):
        """
        Validates each export entry within the export configuration dictionary.

        Args:
            object_element (ObjectElement): The object element associated with the export.
            export_files (str or list): The file or files to be exported for the object element.

        Raises:
            TypeError: If the keys are not instances of ObjectElement or if
                        export_files are not correctly specified.
        """
        if not isinstance(object_element, ObjectElement):
            raise TypeError("Keys of the export dictionary must be instances of ObjectElement.")
        if not isinstance(export_files, list):
            raise ValueError("The exported files should be written as a list")
        if not all(isinstance(file, str) for file in export_files):
            raise TypeError("Export files must be specified as a list of strings.")
        self._validate_export_files_existence(export_files)

    def _validate_export_files_existence(self, export_files):
        """
        Validates that the specified export files are eligible for export based on current settings.

        Args:
            export_files (list): A list of filenames to be exported.

        Raises:
            ValueError: If any of the specified files cannot be exported based
                        on the current configuration.
        """
        possible_exports = (
            self.possible_exports if self.analyze else self.possible_exports_without_analysis
        )
        for file in export_files:
            if file not in possible_exports:
                raise ValueError(f"Cannot export {file}. Check spelling or analysis settings.")

    def _generate_exports_list(self, export_list):
        """
        Generates a comprehensive list of exports based on the provided export configurations.

        Args:
            export_list (list): The validated list of export configurations.

        Returns:
            list: A list of tuples, each containing the name of an object element
                    and a filename to export.
        """
        exports_list = []
        for export_dict in export_list:
            for object_element, export_files in export_dict.items():
                if isinstance(export_files, str):
                    export_files = [export_files]  # Ensure it's a list
                for file in export_files:
                    exports_list.append((object_element.attributes().original()["name"], file))
        return exports_list

    def _iter_unique_export_pairs(self):
        """Yield unique (object_name, export_type) pairs in first-seen order."""
        seen = set()
        for export_pair in self._exports_list:
            if export_pair in seen:
                continue
            seen.add(export_pair)
            yield export_pair

    @property
    def params(self):
        """The parameters to scan, as a list of dictionaries.

        For each dictionary the keys are the parameters elements of the beamline,
        and the values are the values to be assigned.
        """
        if hasattr(self.sp, "params"):
            value = self.sp.params
        else:
            value = _ReadOnlyList([], "params")
        return value

    @params.setter
    def params(self, value):
        if not isinstance(value, SimulationParams):
            self.sp = SimulationParams(self.rml)
            self.sp.params = value
        else:
            self.sp = value

    def _save_parameters_to_file(self, dir):
        """Save user input parameters to file.

        It takes the values from the SimulationParams class

        Args:
            dir (str): the folder where to save the parameters
        """
        for i, p in enumerate(self.sp.ind_par):
            filename = str(p.get_full_path().removeprefix("lab.beamline."))
            filename = "input_param_" + filename.replace(".", "_")
            filename += ".dat"
            filepath = os.path.join(dir, filename)
            with open(filepath, "w") as f:
                values = self.sp.ind_param_values[i]
                for item in values[1]:
                    f.write(f"{item}\n")

        for i, p in enumerate(self.sp.dep_par):
            filename = str(p.get_full_path().removeprefix("lab.beamline."))
            filename = "input_param_" + filename.replace(".", "_")
            filename += ".dat"
            filepath = os.path.join(dir, filename)
            with open(filepath, "w") as f:
                dependency = self.sp.dep_value_dependency[i]
                for values in dependency._data:
                    f.write(f"{values}\n")

    def rml_list(self, recipe=None, overwrite_rml=True):
        """
        Creates the folder structure and RML files needed for simulation.
        This method organizes simulation parameters into RML files and prepares
        the directory structure for simulations, which is useful for
        pre-simulation checks and manual adjustments.

        Args:
            recipe (SimulationRecipe, optional): Recipe to use for setting
                                                up the simulation. Defaults to None.
            overwrite_rml (bool, optional): If True, existing RML files will be overwritten.
                                                Defaults to True.

        """
        self.overwrite_rml = overwrite_rml
        self._setup_simulation_environment(recipe)
        self._initialize_simulation_directory()

        if overwrite_rml:
            recap_csv_path = os.path.join(self.sim_path, "looper.csv")
            if os.path.exists(recap_csv_path):
                os.remove(recap_csv_path)
            recap_txt_path = os.path.join(self.sim_path, "looper.txt")
            if os.path.exists(recap_txt_path):
                os.remove(recap_txt_path)
            self._recap_header_written = False

        for round_number in range(self.repeat):
            sim_number = 0
            for params in self.sp.simulation_parameters_generator():
                _ = self._generate_rml_file(sim_number, round_number, params)
                if round_number == 0:
                    self._update_simulation_recap_files(params, sim_number)
                sim_number += 1
        self._save_parameters_to_file(self.sim_path)

    def _initialize_simulation_directory(self):
        """Initializes the directory structure for simulations."""
        self.sim_list_path = []
        self.sim_path = os.path.join(self.path, f"{self.prefix}_{self.simulation_name}")
        if not os.path.exists(self.sim_path):
            os.makedirs(self.sim_path)
        for round_n in range(self.repeat):
            round_folder_path = os.path.join(self.sim_path, "round_" + str(round_n))
            if not os.path.exists(round_folder_path):
                os.makedirs(round_folder_path)

    def _generate_rml_file(self, sim_number, round_n, param_set):
        """
        Generates an RML file for a given simulation setup.

        Args:
            sim_folder (str): The folder where the RML file should be saved.
            sim_number (int): The simulation number within the current round.
            param_set (dict): The parameter set for the current simulation.

        Returns:
            str: The path to the generated RML file.
        """
        round_folder = "round_" + str(round_n)
        rml_path = os.path.join(
            self.sim_path, round_folder, f"{sim_number}_{self.simulation_name}.rml"
        )

        for param, value in param_set.items():
            self.sp._write_value_to_param(param, value)
        if self.overwrite_rml or not os.path.exists(rml_path):
            self.rml.write(rml_path)
        self.sim_list_path.append(rml_path)
        return rml_path

    def _update_simulation_recap_files(self, params, simulation_number):
        """Updates or creates recap CSV and TXT files summarizing the simulations.

        Args:
            params (list): The parameters for the current simulation batch.
            simulation_number (int): The number of the simulation being processed.
        """
        # Paths for the recap files in the main simulation directory
        recap_csv_path = os.path.join(self.sim_path, "looper.csv")
        recap_txt_path = os.path.join(self.sim_path, "looper.txt")

        # Issue A: use a flag instead of 2x os.path.exists per simulation
        needs_header = not getattr(self, "_recap_header_written", False)

        # Prepare data for CSV and TXT files
        header = ["Simulation Number"] + [
            f"{param._parent['name']}.{param['id']}" for param in params
        ]
        row = [str(simulation_number)] + [param for param in params.values()]

        # Update CSV file
        with open(recap_csv_path, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if needs_header:
                writer.writerow(header)
            writer.writerow(row)

        # Prepare and update TXT file with nice formatting
        with open(recap_txt_path, "a") as txtfile:
            if needs_header:
                txtfile.write(" ".join(header) + "\n")

            column_widths = [
                max(
                    len(str(simulation_number)),
                    max(len(h), max(len(str(r)) for r in row)),
                )
                for h, r in zip(header, row, strict=False)
            ]
            formatted_row = " ".join(
                str(r).ljust(w) for r, w in zip(row, column_widths, strict=False)
            )
            txtfile.write(formatted_row + "\n")

        self._recap_header_written = True

    def _sim_output_is_fresh(self, sim_index, repeat, since):
        """True only if all output files exist AND have mtime >= since (wall-clock seconds)."""
        round_folder = "round_" + str(repeat)
        folder = os.path.join(self.sim_path, round_folder)
        for export_config in self._exports_list:
            if self.raypyng_analysis:
                path = os.path.join(
                    folder,
                    f"{sim_index}_{export_config[0]}_analyzed_rays_{export_config[1]}.dat",
                )
            else:
                path = os.path.join(
                    folder, f"{sim_index}_{export_config[0]}-{export_config[1]}.csv"
                )
            try:
                if not os.path.exists(path) or os.path.getmtime(path) < since:
                    return False
            except OSError:
                return False
        return True

    def _is_simulation_missing(self, sim_index, repeat):
        """
        Checks if a simulation is missing based on the existence of its export files.

        Args:
            simulation_index (int): The index of the simulation in the simulation list.

        Returns:
            bool: True if the simulation is missing any export files, False otherwise.
        """
        round_folder = "round_" + str(repeat)
        folder = os.path.join(self.sim_path, round_folder)
        for export_config in self._exports_list:
            if self.raypyng_analysis:
                export_file = os.path.join(
                    folder,
                    f"{sim_index}_{export_config[0]}_analyzed_rays_{export_config[1]}.dat",
                )
            else:
                export_file = os.path.join(
                    folder, f"{sim_index}_{export_config[0]}-{export_config[1]}.csv"
                )
            if not os.path.exists(export_file):
                return True  # Missing at least one export file

        return False

    def _missing_simulations_for_round(self, round_number):
        """Return missing simulation indices for a round using a single directory scan."""
        round_folder = os.path.join(self.sim_path, "round_" + str(round_number))
        expected_ids = set(range(self.sp._calc_number_sim()))

        if self.raypyng_analysis:
            expected_suffixes = [
                f"_{export_config[0]}_analyzed_rays_{export_config[1]}.dat"
                for export_config in self._exports_list
            ]
        else:
            expected_suffixes = [
                f"_{export_config[0]}-{export_config[1]}.csv"
                for export_config in self._exports_list
            ]

        found_per_export = {suffix: set() for suffix in expected_suffixes}
        self.logger.info(f"Scanning round {round_number} outputs in {round_folder}")

        with os.scandir(round_folder) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                filename = entry.name
                for suffix in expected_suffixes:
                    if not filename.endswith(suffix):
                        continue
                    sim_index = filename[: -len(suffix)].split("_", 1)[0]
                    if sim_index.isdigit():
                        sim_index = int(sim_index)
                        if sim_index in expected_ids:
                            found_per_export[suffix].add(sim_index)
                    break

        completed_ids = expected_ids.copy()
        for suffix, found_ids in found_per_export.items():
            self.logger.info(
                f"Round {round_number}: found {len(found_ids)}/{len(expected_ids)} "
                f"files for {suffix}"
            )
            completed_ids &= found_ids

        return sorted(expected_ids - completed_ids)

    def _make_exports_list(self, sim_number, round_n):
        exports_list = []
        path = os.path.join(self.sim_path, "round_" + str(round_n))
        for d in self.exports:
            for exp_oe in d.keys():
                for exp in d[exp_oe]:
                    temp_exp_list = []
                    temp_exp_list.append(exp_oe["name"])
                    temp_exp_list.append(exp)
                    temp_exp_list.append(path)
                    temp_exp_list.append(str(sim_number) + "_")
                    exports_list.append(temp_exp_list)
        return exports_list

    def _format_eta(self, seconds):
        """Format seconds into days, hours, and minutes."""
        if seconds < 60:
            return f"{max(1, int(round(seconds)))}s"
        days, seconds = divmod(int(seconds), 86400)
        hours, seconds = divmod(int(seconds), 3600)
        minutes, seconds = divmod(int(seconds), 60)
        if days > 0:
            return f"{days} day(s), {int(hours):02d}h:{int(minutes):02d}min"
        if hours == 0:
            return f"{int(minutes):02d}min:{int(seconds):02d}s"
        else:
            return f"{int(hours):02d}h:{int(minutes):02d}min"

    def _initialize_progress_bar(self, total_simulations, description="Simulations Completed"):
        bar_format = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {postfix}]"
        progress_bar = tqdm(total=total_simulations, bar_format=bar_format, desc=description)
        return progress_bar

    def _print_simulations_info(self):
        total_simulations = self.sp._calc_number_sim() * self.repeat

        # Prepare data for printing
        data = [
            ["RML File ", os.path.basename(self._rml._template)],
            ["Simulation Name", self._sim_folder],
            ["Independent Parameters", len(self.sp.ind_par)],
            ["Dependent Parameters", len(self.sp.dep_par)],
            ["Rounds of Simulations", self._repeat],
            ["Total Number of Simulations", total_simulations],
        ]
        if getattr(self, "_initial_eta_seed", None):
            data.extend(
                [
                    [
                        f"Rough Total ETA ({self._workers} workers)",
                        self._format_eta(self._initial_eta_seed["total_seconds"]),
                    ],
                ]
            )

        # Determine column widths by the longest item in each column
        col_widths = [max(len(str(item)) for item in col) for col in zip(*data, strict=False)]

        print()
        print("Simulation Info")

        # Print the data rows
        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        for row in data[0:]:
            print(f"{row[0]:<{col_widths[0]}} | {row[1]:>{col_widths[1]}}")

        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        print()

    def _init_logging(self):
        """Initializes logging for the simulation."""
        log_filename = os.path.join(self.sim_path, "simulation.log")
        logging.basicConfig(
            filename=log_filename,
            filemode="a",
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Simulation started, using {self._workers} workers")

    def _resolve_multiprocessing_workers(self, multiprocessing):
        if isinstance(multiprocessing, str):
            mode = multiprocessing.lower()
            if mode not in {"auto", "max"}:
                raise ValueError(
                    "The 'multiprocessing' argument must be an integer greater than 0, "
                    "or one of: 'auto', 'max'."
                )

            cpu_count = os.cpu_count() or 1
            available_ram_gb = max(1, int(psutil.virtual_memory().available / (1024**3)))

            if mode == "auto":
                return max(1, min(cpu_count, available_ram_gb - 2))
            return max(1, min(cpu_count, available_ram_gb))

        if not isinstance(multiprocessing, int) or multiprocessing < 1:
            raise ValueError(
                "The 'multiprocessing' argument must be an integer greater than 0, "
                "or one of: 'auto', 'max'."
            )
        return multiprocessing

    def run(
        self,
        recipe=None,
        multiprocessing=1,
        force=False,
        overwrite_rml=True,
        force_exit=False,
        remove_rawrays=False,
        remove_round_folders=False,
    ):
        """
        Execute simulations with optional recipe, multiprocessing, and file management options.

        This method orchestrates the setup and execution of simulations, managing multiprocessing,
        file generation, and progress tracking.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup.
                                                    Defaults to None.
            multiprocessing (int or str, optional): Number of processes for parallel execution,
                                                    or 'auto'/'max' to derive it from available
                                                    CPUs and RAM. Defaults to 1.
            force (bool, optional): Force re-execution of simulations.
                                                    Defaults to False.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
            force_exit (bool, optional): emergency fallback that calls os._exit when the
                                            simulations are complete. Defaults to False.
            remove_rawrays (bool, optional): removes RawRaysIncoming and RawRaysOutgoing files,
                                                if present.
            remove_round_folders (bool, optional): remove the round folders after the simulations
                                                    are done.
        """
        multiprocessing = self._resolve_multiprocessing_workers(multiprocessing)
        run_start = time.monotonic()

        if self.graxpy_efficiency and self._engine == "ray-ui":
            raise ValueError(
                "graxpy_efficiency is not supported with the 'ray-ui' engine: "
                "RAY-UI already computes grating efficiency internally."
            )
        if remove_rawrays and not self.raypyng_analysis:
            raise Exception(
                "Setting remove_rawrays to True is allowed only raypyng_analysis is set to True"
            )
        if remove_rawrays:
            self.remove_rawrays = remove_rawrays
        self._setup_simulation_environment(recipe)
        self._validate_run_configuration()

        if self._engine == "ray-ui":
            runner = RayUIRunner(ray_path=self.ray_path, hide=True)
            runner.kill()
        elif self._engine == "rayx":
            try:
                import rayx  # noqa: F401
            except ImportError:
                raise ImportError(
                    "rayx is not installed or not available on this platform. "
                    "Install it with: pip install raypyng[rayx]"
                ) from None
        else:
            raise ValueError(f"Unknown engine '{self._engine}'. Choose 'ray-ui' or 'rayx'.")

        if self.graxpy_efficiency:
            try:
                import grax  # noqa: F401
            except ImportError:
                raise ImportError(
                    "graxpy is not installed. Install it with: pip install raypyng[graxpy]"
                ) from None

        self._batch_number = 0
        self._workers = multiprocessing
        self.batch_size = int(self._workers) * 5
        self._prepare_simulation_environment(overwrite_rml)
        self._init_logging()
        if getattr(self, "_initial_eta_seed", None):
            self.logger.info(
                "Rough ETA seed from numberRays (%s): first round %s, total %s",
                self._initial_eta_seed["basis"],
                self._format_eta(self._initial_eta_seed["first_round_seconds"]),
                self._format_eta(self._initial_eta_seed["total_seconds"]),
            )
        total_simulations = self.sp._calc_number_sim() * self.repeat
        self.simulations_checked = False
        self._executor_has_unfinished_futures = False

        pbar = self._initialize_progress_bar(total_simulations, description="Simulations Completed")
        self._seed_progress_bar_eta(pbar)
        try:
            self._execute_simulations(multiprocessing, force, total_simulations, pbar)
            self.logger.info("Simulation completed successfully.")
        except KeyboardInterrupt:
            self.logger.error("Simulation Interrupted.", exc_info=True)
            self.cleanup_child_processes()
            raise
        except Exception:
            self.logger.error("Simulation failed.", exc_info=True)
            self.cleanup_child_processes()
            raise
        finally:
            pbar.close()
        if self.raypyng_analysis:
            self.logger.info("Starting cleanup")
            pp = PostProcess()
            pp.cleanup(self.sim_path, self.repeat, export_pairs=self._exports_list)
            self.logger.info("Done with the cleanup")
            if self.analyze is False and self.raypyng_analysis is True:
                self.logger.info("Create Pandas Recap Files")
                self._create_results_dataframe()
            self._write_analysis_metadata_file()
        elif self.analyze:
            self.logger.info("Create RAY-UI recap files")
            self._create_rayui_results_dataframe()
        if self.graxpy_efficiency:
            from .graxpy_efficiency import aggregate_graxpy_results

            out = aggregate_graxpy_results(self.sim_path)
            self.logger.info("graxpy efficiency aggregated to %s", out)
        if remove_round_folders:
            self._remove_round_folders()
        total_elapsed = time.monotonic() - run_start
        elapsed_str = self._format_eta(total_elapsed)
        print(f"\nTotal runtime: {elapsed_str}", flush=True)
        self.logger.info("Total runtime: %s", elapsed_str)
        self.logger.info("End of the Simulations")
        if force_exit:
            self.cleanup_child_processes()
            os._exit(0)

    @staticmethod
    def _is_rayui_or_xvfb_process(proc):
        """Return True only for leftover RAY-UI / Xvfb processes.

        The multiprocessing resource_tracker and the ProcessPoolExecutor worker
        processes (``spawn_main``) must never be terminated here: killing the
        resource_tracker corrupts its bookkeeping and triggers
        'resource_tracker: process died unexpectedly' warnings plus KeyErrors.
        The executor reaps its own workers via shutdown(); we only mop up the
        RAY-UI/Xvfb subprocesses those workers may have left behind.
        """
        rayui_markers = ("ray-ui", "rayui")
        try:
            name = (proc.name() or "").lower()
            cmdline = " ".join(proc.cmdline()).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

        # Never touch Python multiprocessing machinery.
        if "resource_tracker" in cmdline or "spawn_main" in cmdline:
            return False

        if "xvfb" in name or "xvfb" in cmdline:
            return True
        return any(marker in name or marker in cmdline for marker in rayui_markers)

    def cleanup_child_processes(self):
        """Clean up leftover RAY-UI and Xvfb processes.

        Only RAY-UI/Xvfb processes are targeted; the multiprocessing
        resource_tracker and the executor's worker processes are left alone.
        """
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        announced_cleanup = False

        # Terminate only leftover RAY-UI / Xvfb child processes
        for child in children:
            if not self._is_rayui_or_xvfb_process(child):
                continue
            try:
                if not announced_cleanup:
                    print("Terminating leftover RAY-UI processes...")
                    announced_cleanup = True
                child.terminate()
                child.wait(timeout=3)
            except psutil.NoSuchProcess:
                continue
            except psutil.TimeoutExpired:
                # On macOS SIGKILL on a GUI app triggers the crash reporter dialog;
                # leave it to be reaped rather than force-killing.
                if sys.platform != "darwin":
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass

        # Now target specific Xvfb processes with display numbers higher than 3000
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            if "Xvfb" in proc.info["name"]:
                cmdline = proc.info["cmdline"]
                if len(cmdline) > 1:
                    display_part = cmdline[1]  # The part of the cmdline where ':XXXX' is expected
                    if display_part.startswith(":") and display_part[1:].isdigit():
                        display_number = int(display_part[1:])
                        if display_number > 3000:
                            # print(f"Killing Xvfb process on display {display_number}
                            # with PID {proc.pid}")
                            os.kill(proc.pid, signal.SIGTERM)  # Terminate the Xvfb process
                            try:
                                proc.wait(timeout=3)  # Wait for the process to terminate
                            except psutil.TimeoutExpired:
                                proc.kill()  # Force kill if not terminated after timeout

    def _remove_round_folders(self):
        for round_n in range(self._repeat):
            round_folder_path = os.path.join(self.sim_path, "round_" + str(round_n))
            if os.path.exists(round_folder_path):
                shutil.rmtree(round_folder_path)

    def _create_results_dataframe(self):
        looper_path = os.path.join(self.sim_path, "looper.csv")
        looper = pd.read_csv(looper_path)
        missing_files = []
        for export, in_out in self._iter_unique_export_pairs():
            oe_path = os.path.join(self.sim_path, f"{export}_{in_out}.csv")
            if not os.path.exists(oe_path):
                missing_files.append(oe_path)
                continue

            # Reading the data into a DataFrame, specify no comment
            # handling and read headers normally
            res = pd.read_csv(oe_path, comment=None, header=0, index_col=False)
            # Manually remove the '#' from the first column name
            res.columns = [col.replace("#", "").strip() for col in res.columns]
            res_combined = pd.concat([looper, res], axis=1)
            res_combined = res_combined.loc[:, ~res_combined.columns.str.contains("^Unnamed")]
            res_combined.to_csv(os.path.join(self.sim_path, f"{export}_{in_out}.csv"))
            # Issue E: cache columns so _write_analysis_metadata_file avoids a re-read
            if not hasattr(self, "_last_result_columns"):
                self._last_result_columns = list(res_combined.columns)

        if missing_files:
            formatted = "\n".join(f"- {path}" for path in missing_files)
            raise FileNotFoundError(
                "Missing expected analysis output file(s) for configured sim.exports:\n"
                f"{formatted}"
            )

    def _read_rayui_analysis_row(self, file_path):
        """Read one tab-separated RAY-UI analysis export into a single-row DataFrame."""
        res = pd.read_csv(file_path, sep="\t", skiprows=1)
        res.columns = [col.replace("#", "").strip() for col in res.columns]
        return res.loc[:, ~res.columns.str.contains("^Unnamed")]

    def _aggregate_rayui_rows(self, rows):
        """Average numeric columns across rounds and keep first non-null text values."""
        concatenated = pd.concat(rows, ignore_index=True)
        aggregated = {}

        for column in concatenated.columns:
            series = concatenated[column]
            numeric = pd.to_numeric(series, errors="coerce")
            non_null = series.dropna()

            if not non_null.empty and numeric.notna().sum() == len(non_null):
                aggregated[column] = numeric.mean()
            else:
                aggregated[column] = non_null.iloc[0] if not non_null.empty else np.nan

        return pd.DataFrame([aggregated])

    def _create_rayui_results_dataframe(self):
        looper_path = os.path.join(self.sim_path, "looper.csv")
        looper = pd.read_csv(looper_path)
        missing_files = []

        for export, export_type in self._iter_unique_export_pairs():
            combined_rows = []

            for sim_number in looper["Simulation Number"]:
                round_rows = []
                for round_n in range(self.repeat):
                    rayui_path = os.path.join(
                        self.sim_path,
                        f"round_{round_n}",
                        f"{sim_number}_{export}-{export_type}.csv",
                    )
                    if not os.path.exists(rayui_path):
                        missing_files.append(rayui_path)
                        round_rows = []
                        break

                    round_rows.append(self._read_rayui_analysis_row(rayui_path))

                if not round_rows:
                    continue

                looper_row = looper.loc[looper["Simulation Number"] == sim_number].reset_index(
                    drop=True
                )
                analysis_row = self._aggregate_rayui_rows(round_rows)
                combined_rows.append(pd.concat([looper_row, analysis_row], axis=1))

            if combined_rows:
                combined = pd.concat(combined_rows, ignore_index=True)
                combined = combined.loc[:, ~combined.columns.str.contains("^Unnamed")]
                combined.to_csv(
                    os.path.join(self.sim_path, f"{export}_{export_type}.csv"), index=False
                )

        if missing_files:
            formatted = "\n".join(f"- {path}" for path in missing_files)
            raise FileNotFoundError(
                "Missing expected RAY-UI analysis output file(s) for configured sim.exports:\n"
                f"{formatted}"
            )

    def _unit_for_output_column(self, column_name):
        analysis_units = {
            "Simulation Number": "index",
            "SourcePhotonFlux": "photons/s",
            "SourceBandwidth": "eV",
            "NumberRaysSurvived": "count",
            "PercentageRaysSurvived": "%",
            "PhotonEnergy": "eV",
            "Bandwidth": "eV",
            "HorizontalFocusFWHM": "mm",
            "VerticalFocusFWHM": "mm",
            "HorizontalDivergenceFWHM": "deg",
            "VerticalDivergenceFWHM": "deg",
            "HorizontalCenter": "mm",
            "VerticalCenter": "mm",
            "PhotonFlux": "photons/s",
            "EnergyPerMilPerBw": None,
            "FluxPerMilPerBwPerc": None,
            "FluxPerMilPerBwAbs": None,
            "AXUVCurrentAmp": "A",
            "GaAsPCurrentAmp": "A",
        }
        parameter_units = {
            "photonEnergy": "eV",
            "numberRays": "count",
            "totalHeight": "mm",
            "cFactor": None,
        }

        if column_name.startswith("Unnamed:"):
            return None
        if column_name in analysis_units:
            return analysis_units[column_name]
        if "." in column_name:
            param_id = column_name.split(".")[-1]
            return parameter_units.get(param_id)
        return None

    def _write_analysis_metadata_file(self):
        sample_columns = None
        # Issue E: use columns already captured in _create_results_dataframe when available
        if hasattr(self, "_last_result_columns"):
            sample_columns = self._last_result_columns
        else:
            for export, in_out in self._iter_unique_export_pairs():
                output_path = os.path.join(self.sim_path, f"{export}_{in_out}.csv")
                if os.path.exists(output_path):
                    sample_columns = list(pd.read_csv(output_path, nrows=0).columns)
                    break

        if sample_columns is None:
            return

        first_analysis_column = "SourcePhotonFlux"
        if first_analysis_column in sample_columns:
            sample_columns = sample_columns[sample_columns.index(first_analysis_column) :]

        metadata = {
            "applies_to": "all raypyng analysis output files in this folder",
            "columns": [
                {"name": column_name, "unit": self._unit_for_output_column(column_name)}
                for column_name in sample_columns
            ],
        }

        metadata_path = os.path.join(self.sim_path, "raypyng_analysis_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=2)

    def _remove_recap_files(
        self,
    ):

        # Filter files ending with ".csv" or ".data"
        files_to_remove = ["looper.csv", "looper.txt"]

        # Remove filtered files
        for file in files_to_remove:
            to_be_removed = os.path.join(self.sim_path, file)
            if os.path.exists(to_be_removed):
                os.remove(to_be_removed)

    def _prepare_simulation_environment(self, overwrite_rml):
        """
        Prepares the simulation environment based on a given recipe and file management options.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup. Defaults to None.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
        """
        self.overwrite_rml = overwrite_rml
        self._initialize_simulation_directory()
        self._save_parameters_to_file(self.sim_path)
        self._remove_recap_files()
        self._initial_eta_seed = self._build_initial_eta_seed()
        self._print_simulations_info()

    def _find_source_with_number_rays(self):
        for oe in self._rml.beamline.children():
            if hasattr(oe, "numberRays"):
                return oe
        return None

    def _estimate_seconds_from_number_rays(self, number_rays):
        x = [point[0] for point in _ETA_NRAYS_CALIBRATION_POINTS]
        y = [point[1] for point in _ETA_NRAYS_CALIBRATION_POINTS]
        number_rays = float(number_rays)

        if number_rays <= x[0]:
            slope = (y[1] - y[0]) / (x[1] - x[0])
            estimate = y[0] + (number_rays - x[0]) * slope
        elif number_rays >= x[-1]:
            slope = (y[-1] - y[-2]) / (x[-1] - x[-2])
            estimate = y[-1] + (number_rays - x[-1]) * slope
        else:
            estimate = np.interp(number_rays, x, y)

        estimate *= _ETA_SAFETY_FACTOR
        return max(_ETA_MIN_SECONDS, float(estimate))

    def _round_zero_number_rays(self):
        if self._engine != "ray-ui" or self.sp is None:
            return None

        source = self._find_source_with_number_rays()
        if source is None:
            return None

        try:
            default_number_rays = float(source.numberRays.cdata)
        except (TypeError, ValueError, AttributeError):
            return None

        source_path = source.numberRays.get_full_path()
        values = []
        scanned = False

        for params in self.sp.simulation_parameters_generator():
            ray_count = default_number_rays
            for param, value in params.items():
                if isinstance(param, ParamElement) and param.get_full_path() == source_path:
                    ray_count = float(value)
                    scanned = True
                    break
            values.append(ray_count)

        return {"basis": "scanned" if scanned else "fixed", "values": values}

    def _build_initial_eta_seed(self):
        round_zero_number_rays = self._round_zero_number_rays()
        if not round_zero_number_rays or not round_zero_number_rays["values"]:
            return None

        first_round_seconds = sum(
            self._estimate_seconds_from_number_rays(number_rays)
            for number_rays in round_zero_number_rays["values"]
        )
        total_seconds = first_round_seconds * self.repeat / max(1, self._workers)

        return {
            "basis": round_zero_number_rays["basis"],
            "first_round_seconds": first_round_seconds,
            "total_seconds": total_seconds,
        }

    def _seed_progress_bar_eta(self, pbar):
        if not getattr(self, "_initial_eta_seed", None):
            return

        eta_str = self._format_eta(self._initial_eta_seed["total_seconds"])
        pbar.set_postfix_str(f"ETA~: {eta_str}", refresh=True)

    def _validate_run_configuration(self):
        if self.sp is None or len(self.sp.params) == 0:
            raise ValueError(
                "Simulation parameters are not configured. Assign 'sim.params = [...]' "
                "before calling run(). In-place mutations such as "
                "'sim.params.append(...)' are not supported."
            )

    def _execute_simulations(
        self,
        num_workers,
        force,
        total_simulations,
        pbar,
        update_reacap_files=True,
        update_pbar_for_present=True,
    ):
        """
        Executes the simulations in batches with multiprocessing support.

        Args:
            num_workers (int): Number of processes for parallel execution.
            force (bool): Force re-execution of simulations.
            total_simulations (int): Total number of simulations to be executed.
            pbar (tqdm): Progress bar object for tracking simulation progress.
            update_reacap_files (bool): Whether to update recap CSV/TXT files.
            update_pbar_for_present (bool): Whether to tick pbar for already-complete sims.
                Set False during retry so the retry bar only counts retried simulations.
        """
        simulations_durations = []  # Track durations of all simulations for average calculation
        self._simulations_duration_total = 0.0  # Issue F: running sum, avoids O(N) sum() per tick
        executor = None
        rerun_missing = False
        rerun_pbar = None

        try:
            # On macOS the default start method is "spawn", which leaves worker
            # processes that fail to reap on shutdown(wait=False) and busy-spin at
            # 100% CPU; the interpreter then hangs forever in the multiprocessing
            # atexit join(). Force "fork" on Darwin so workers reap cleanly.
            mp_context = multiprocessing.get_context("fork") if sys.platform == "darwin" else None
            executor = ProcessPoolExecutor(max_workers=num_workers, mp_context=mp_context)
            simulation_params_batch = []
            batch_length = 0
            remaining_simulations = total_simulations
            for round_number in range(self.repeat):
                self.logger.info(f"Start round {round_number}")
                missing_in_round = set(self._missing_simulations_for_round(round_number))
                for sim_number, params in enumerate(self.sp.simulation_parameters_generator()):
                    if round_number == 0 and update_reacap_files is True:
                        self._update_simulation_recap_files(params, sim_number)
                    if sim_number in missing_in_round or force:
                        self._prepare_and_submit_simulation(
                            params,
                            sim_number,
                            round_number,
                            simulation_params_batch,
                            executor,
                            force,
                        )
                    elif update_pbar_for_present:
                        pbar.update(1)
                    batch_length += 1
                    remaining_simulations -= 1
                    if batch_length == self.batch_size or remaining_simulations == 0:
                        self._wait_for_simulation_batch(
                            simulations_durations,
                            simulation_params_batch,
                            executor,
                            pbar,
                        )
                        self.logger.info(f"Waiting For batch, {self.batch_size} simulations to go")
                        batch_length = 0
                    if remaining_simulations == 0:
                        self.logger.info(
                            f"Remaining simulations {remaining_simulations}, "
                            "stopping the simulations loop"
                        )
                        rerun_missing, rerun_pbar = self._final_check_on_simulations_and_shutdown(
                            pbar
                        )
                        break
        except Exception as e:
            traceback.print_exc()
            self.logger.info(f"Error in _execute simulations: {e}")
            raise
        finally:
            if executor is not None:
                shutdown_wait = not rerun_missing and not self._executor_has_unfinished_futures
                force_cancel = rerun_missing or self._executor_has_unfinished_futures
                if force_cancel:
                    # cancel_futures only drops *queued* tasks; a worker already
                    # running a task keeps going and can busy-loop at 100% CPU.
                    # That worker keeps the executor's non-daemon manager thread
                    # alive, so the interpreter hangs at exit in threading._shutdown().
                    # Forcibly terminate this executor's own worker processes so the
                    # pool tears down and the process can exit. Safe here: any
                    # genuinely-missing simulations are re-run below.
                    for proc in list(getattr(executor, "_processes", {}).values()):
                        try:
                            if proc.is_alive():
                                proc.terminate()
                        except Exception:  # noqa: BLE001 - best-effort teardown
                            pass
                executor.shutdown(wait=shutdown_wait, cancel_futures=force_cancel)
                self.logger.info(
                    "Executor shutdown completed%s.",
                    " without waiting" if not shutdown_wait else "",
                )
                if force_cancel:
                    self.cleanup_child_processes()
        if rerun_missing:
            self._execute_simulations(
                self._workers,
                False,
                total_simulations,
                rerun_pbar,
                update_reacap_files=False,
                update_pbar_for_present=False,
            )

    def _final_check_on_simulations_and_shutdown(self, old_pbar):
        self.logger.info(
            "Checking that all simulations are completed before stopping the ProcessPoolExecutor"
        )
        missing_sim = []
        for round_number in range(self.repeat):
            round_missing = self._missing_simulations_for_round(round_number)
            self.logger.info(
                f"Round {round_number}: final check found {len(round_missing)} missing simulations"
            )
            for sim_number in round_missing:
                self.logger.info(f"Missing simulation: round {round_number}, number {sim_number}")
                missing_sim.append({"round": round_number, "sim_number": sim_number})

        missing_count = len(missing_sim)

        if missing_count >= 1 and self.simulations_checked is False:
            print(
                f"\nFinal check: {missing_count} missing simulation(s). Retrying now...",
                flush=True,
            )
            self.logger.info(f"Retrying {missing_count} missing simulation(s)")
            old_pbar.close()
            pbar = self._initialize_progress_bar(
                missing_count, description="Retrying Missing Simulations"
            )
            self.simulations_checked = True
            return True, pbar

        if missing_count >= 1:
            print(
                f"\nWarning: {missing_count} simulation(s) still missing after retry.",
                flush=True,
            )
            self.logger.warning(f"{missing_count} simulation(s) still missing after retry")
        elif self.simulations_checked:
            print("\nRetry complete. All simulations finished successfully.", flush=True)

        return False, old_pbar

    def _prepare_and_submit_simulation(
        self, params, sim_number, round_number, simulation_params_batch, executor, force
    ):
        """
        Prepares and submits a single simulation for execution.

        Args:
            params (dict): Parameters for the current simulation.
            sim_number (int): Simulation number within the current batch.
            round_number (int): Current round of simulations.
            simulation_params_batch (list): Batch of simulation parameters for submission.
            executor (ProcessPoolExecutor): Executor for multiprocessing.
            force (bool): Force re-execution of simulations.
        """
        rml_file_path = self._generate_rml_file(sim_number, round_number, params)
        exp_list = self._make_exports_list(sim_number, round_number)
        simulation_params = (
            (
                rml_file_path,
                self._hide,
                self.analyze,
                self.raypyng_analysis,
                self.ray_path,
                self.remove_rawrays,
                self.undulator_table,
                self.efficiency,
                self.graxpy_efficiency,
                self.graxpy_fourier_orders,
                self.graxpy_x_resolution_nm,
                self.graxpy_z_resolution_nm,
            ),
            exp_list,
        )
        simulation_params_batch.append(simulation_params)
        self.logger.info(f"Prepared sim number: {sim_number}: {rml_file_path}")

    def _wait_for_simulation_batch(
        self, simulations_durations, simulation_params_batch, executor, pbar
    ):
        """
        Waits for a batch of simulations to complete and updates the progress bar.

        Args:
            simulations_durations (list): List to track durations of completed simulations.
            simulation_params_batch (list): Batch of simulation parameters that were submitted.
            executor (ProcessPoolExecutor): Executor for multiprocessing.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        func = run_rml_func_rayx if self._engine == "rayx" else run_rml_func
        futures = {
            executor.submit(func, sim_params): sim_params for sim_params in simulation_params_batch
        }
        completed_sim = 0
        remaining_simulations = len(futures)
        self.logger.info(
            f"Waiting for batch number: {self._batch_number}, "
            f"initial max-idle: {self._simulation_timeout}s"
        )
        self._batch_number += 1

        # Adaptive idle-based timeout: poll every 5 s and recompute the allowed idle
        # window from real timing data after each future completes.
        batch_clock_start = time.time()  # wall-clock anchor for freshness checks
        pending = set(futures)
        last_completion = time.monotonic()
        max_idle_secs = self._simulation_timeout  # 300 s seed; replaced once first sim reports in
        timed_out_futures = []

        while pending:
            done, pending = wait(pending, timeout=5.0, return_when=FIRST_COMPLETED)
            for future in done:
                try:
                    sim_duration, rml_filename = future.result()
                    simulations_durations.append(sim_duration)
                    self._simulations_duration_total += sim_duration
                    avg = self._simulations_duration_total / len(simulations_durations)
                    max_idle_secs = max(60.0, avg * 3.0)
                    self._simulation_timeout = max_idle_secs
                    self._update_progress_bar(simulations_durations, pbar)
                    completed_sim += 1
                    remaining_simulations -= 1
                    last_completion = time.monotonic()
                    self.logger.info(
                        f"Completed: {completed_sim}, remaining: {remaining_simulations}, "
                        f"{rml_filename}"
                    )
                except Exception as e:
                    self.logger.warning(f"Future raised exception: {e}")
                    remaining_simulations -= 1
                    last_completion = time.monotonic()
                    self._update_progress_bar(simulations_durations, pbar)

            if pending and (time.monotonic() - last_completion) >= max_idle_secs:
                idle = time.monotonic() - last_completion
                self.logger.warning(
                    f"No batch completion reported for {idle:.0f}s; "
                    f"{len(pending)} future(s) still pending (threshold {max_idle_secs:.0f}s)"
                )
                timed_out_futures = list(pending)
                pending = set()
                break

        if timed_out_futures:
            self._executor_has_unfinished_futures = True
            self.logger.info(
                f"Marking executor as having {len(timed_out_futures)} unfinished futures"
            )
            for future in timed_out_futures:
                future.cancel()
            missing_sims = []
            try:
                for sim in simulation_params_batch:
                    _, exp_list = sim
                    exp = exp_list[0]
                    round_n = int(re.findall(r"(?<=round_)\d+", exp[-2])[0])
                    sim_n = int(re.findall(r"\d+", exp[-1])[0])
                    sim_file = sim[0][0]
                    if self._is_simulation_missing(sim_n, round_n):
                        missing_sims.append((sim_n, round_n, sim_file))
            except Exception as e:
                self.logger.info(f"Exception building missing-sim list: {e}")

            n_missing = len(missing_sims)
            if missing_sims:
                idle_threshold = max(10.0, max_idle_secs / 4)
                print(
                    f"\nStill waiting for {n_missing} sim(s) to finish. "
                    "This can be normal for longer runs; checking the output files...",
                    flush=True,
                )
                last_progress = time.monotonic()
                while missing_sims:
                    time.sleep(2)
                    still_missing = []
                    for sim_n, round_n, sim_file in missing_sims:
                        if self._sim_output_is_fresh(sim_n, round_n, batch_clock_start):
                            last_progress = time.monotonic()
                            elapsed = time.time() - batch_clock_start
                            max_idle_secs = max(60.0, elapsed * 3.0)
                            self._simulation_timeout = max_idle_secs
                            self.logger.info(
                                f"Sim {sim_n} appeared after {elapsed:.1f}s; "
                                f"updating max_idle to {max_idle_secs:.0f}s"
                            )
                        else:
                            still_missing.append((sim_n, round_n, sim_file))
                    missing_sims = still_missing
                    if missing_sims and (time.monotonic() - last_progress) >= idle_threshold:
                        self.logger.warning(
                            f"Giving up: {len(missing_sims)} sims idle for "
                            f"{time.monotonic() - last_progress:.0f}s"
                        )
                        break
                found = n_missing - len(missing_sims)
                self.logger.info(f"Post-timeout: {found}/{n_missing} sims appeared")

            if len(simulations_durations) == 0:
                simulations_durations.append(max_idle_secs)
            self.logger.info("Updating progress bar")
            for _i in range(remaining_simulations):
                try:
                    self._update_progress_bar(simulations_durations, pbar)
                except Exception as e:
                    self.logger.info(f"Exception updating progress bar: {e}")

        simulation_params_batch.clear()  # Reset batch for next set of simulations
        self.logger.info("Batch Completed")

    def _update_progress_bar(self, simulations_durations, pbar):
        """
        Updates the progress bar based on completed simulations.

        Args:
            simulations_durations (list): List of durations for completed simulations.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        avg_duration = getattr(self, "_simulations_duration_total", 0.0) / max(
            1, len(simulations_durations)
        )
        last_duration = simulations_durations[-1]
        remaining_simulations = pbar.total - pbar.n
        eta_seconds = avg_duration * remaining_simulations / self._workers
        eta_str = self._format_eta(eta_seconds)
        pbar.set_postfix_str(
            f"ETA: {eta_str}, Last: {last_duration:.2f}s, Avg: {avg_duration:.2f}s/it",
            refresh=True,
        )
        pbar.update(1)

    def _setup_simulation_environment(self, recipe):
        """
        Sets up the simulation environment based on the provided recipe.

        Args:
            recipe (SimulationRecipe or None): Recipe to apply for the simulation setup.

        Raises:
            TypeError: If the recipe is not a SimulationRecipe instance or None.
        """
        if recipe:
            if not isinstance(recipe, SimulationRecipe):
                raise TypeError("Unsupported type of the recipe!")
            print("recipe")
            self.params = recipe.params(self)
            self.exports = recipe.exports(self)
            self.simulation_name = recipe.simulation_name(self)

    def reflectivity(self, value):
        """
        Switch the reflectivity of all the optical elements in the beamline on or off.

        Args:
            value (bool, optional): If :code:`True` the reflectivity is switched on,
                                           if :code:`False` the reflectivity is switched off.
        """
        if value:
            on_off = "1"
        else:
            on_off = "0"

        for oe in self.rml.beamline.children():
            if hasattr(oe, "reflectivityType"):
                oe.reflectivityType.cdata = on_off

    def slope_errors(self, slope_errors):
        """
        Switch the slope errors of all the optical elements in the beamline on or off.

        Args:
            value (bool, optional): If `True` the slope errors are switched on,
                                           if `False` the slope errors are switched off.
        """
        if slope_errors:
            on_off = "0"
        else:
            on_off = "1"

        for oe in self.rml.beamline.children():
            if hasattr(oe, "slopeError"):
                oe.slopeError.cdata = on_off
                # oe.slopeError.attributes()['enabled'] = enabled

    def alignment_errors(self, value):
        """
        Switch the alignment errors of all the optical elements in the beamline on or off.

        Args:
            value (bool, optional): If `True`, the alignment errors are switched on.
                If `False`, the alignment errors are switched off.

        Returns:
            None
        """

        if value:
            on_off = "0"
        else:
            on_off = "1"

        for oe in self.rml.beamline.children():
            if hasattr(oe, "alignmentError"):
                oe.alignmentError.cdata = on_off


def run_rml_func_rayx(parameters):
    """Executes a simulation using the RAYX engine for a given RML file."""
    st = time.time()
    (
        rml_filename,
        _hide,
        _analyze,
        raypyng_analysis,
        _ray_path,
        remove_rawrays,
        undulator_table,
        efficiency,
        graxpy_efficiency,
        graxpy_fourier_orders,
        graxpy_x_resolution_nm,
        graxpy_z_resolution_nm,
    ), exports = parameters
    from .rayx_runner import RayXAPI, _rayui_update_rml

    _rayui_update_rml(rml_filename, ray_path=_ray_path, hide=_hide)
    graxpy_eff_df = None
    downstream_elements: set[str] = set()
    if graxpy_efficiency:
        from .graxpy_efficiency import (
            compute_grating_efficiency,
            elements_after_first_grating,
            read_grating_params,
            write_efficiency_csv,
            write_grating_snippet,
        )

        try:
            grating_params_list = read_grating_params(rml_filename)
            write_grating_snippet(
                rml_filename,
                grating_params_list,
                fourier_orders=graxpy_fourier_orders,
                x_resolution_nm=graxpy_x_resolution_nm,
                z_resolution_nm=graxpy_z_resolution_nm,
            )
            efficiencies = compute_grating_efficiency(
                rml_filename,
                fourier_orders=graxpy_fourier_orders,
                x_resolution_nm=graxpy_x_resolution_nm,
                z_resolution_nm=graxpy_z_resolution_nm,
            )
            write_efficiency_csv(rml_filename, efficiencies)
            if efficiencies:
                combined = 1.0
                energy_ev = next(iter(efficiencies.values()))["energy_ev"]
                for r in efficiencies.values():
                    combined *= r["efficiency_p"]
                graxpy_eff_df = pd.DataFrame({"Energy[eV]": [energy_ev], "Efficiency": [combined]})
                downstream_elements = elements_after_first_grating(rml_filename)
        except Exception as e:
            print(f"WARNING! graxpy efficiency failed for {rml_filename}: {e}")
    api = RayXAPI()
    pp = PostProcess()
    try:
        api.load(rml_filename)
        api.trace()
        for export_params in exports:
            api.export(*export_params)
        if raypyng_analysis:
            for export_params in exports:
                element_name = export_params[0]
                eff = (
                    graxpy_eff_df
                    if graxpy_eff_df is not None and element_name in downstream_elements
                    else efficiency
                )
                pp.postprocess_RawRays(
                    *export_params,
                    rml_filename,
                    suffix=export_params[1],
                    remove_rawrays=remove_rawrays,
                    undulator_table=undulator_table,
                    efficiency=eff,
                )
    except Exception as e:
        print(f"ERROR! Got exception while processing {rml_filename}: {e}", flush=True)
        raise
    return time.time() - st, rml_filename


def run_rml_func(parameters):
    """
    Executes a simulation for a given RML file and handles exporting of results.

    Args:
        parameters (tuple): A tuple containing the necessary parameters for the simulation run,
                            which includes the RML filename, hide flag, analyze flag,
                            raypyng analysis flag, and the path to the RAY-UI installation.
    """
    st = time.time()
    (
        rml_filename,
        hide,
        analyze,
        raypyng_analysis,
        ray_path,
        remove_rawrays,
        undulator_table,
        efficiency,
        graxpy_efficiency,
        graxpy_fourier_orders,
        graxpy_x_resolution_nm,
        graxpy_z_resolution_nm,
    ), exports = parameters
    runner = RayUIRunner(ray_path=ray_path, hide=hide)
    api = RayUIAPI(runner)
    pp = PostProcess()
    try:
        runner.run()
        api.load(rml_filename)
        api.trace(analyze=analyze)
        api.save(rml_filename)
        graxpy_eff_df = None
        downstream_elements: set[str] = set()
        if graxpy_efficiency:
            from .graxpy_efficiency import (
                compute_grating_efficiency,
                elements_after_first_grating,
                read_grating_params,
                write_efficiency_csv,
                write_grating_snippet,
            )

            try:
                grating_params_list = read_grating_params(rml_filename)
                write_grating_snippet(
                    rml_filename,
                    grating_params_list,
                    fourier_orders=graxpy_fourier_orders,
                    x_resolution_nm=graxpy_x_resolution_nm,
                    z_resolution_nm=graxpy_z_resolution_nm,
                )
                efficiencies = compute_grating_efficiency(
                    rml_filename,
                    fourier_orders=graxpy_fourier_orders,
                    x_resolution_nm=graxpy_x_resolution_nm,
                    z_resolution_nm=graxpy_z_resolution_nm,
                )
                write_efficiency_csv(rml_filename, efficiencies)
                if efficiencies:
                    combined = 1.0
                    energy_ev = next(iter(efficiencies.values()))["energy_ev"]
                    for r in efficiencies.values():
                        combined *= r["efficiency_p"]
                    graxpy_eff_df = pd.DataFrame(
                        {"Energy[eV]": [energy_ev], "Efficiency": [combined]}
                    )
                    downstream_elements = elements_after_first_grating(rml_filename)
            except Exception as e:
                print(f"WARNING! graxpy efficiency failed for {rml_filename}: {e}")
        rawrays_cache = {}
        for export_params in exports:
            element_name, export_type = export_params[0], export_params[1]
            if export_type in _RAWRAYS_ITEM_IDS:
                raw_array = api.rawdata(element_name, export_type)
                rawrays_cache[(element_name, export_type)] = raw_array
                if not remove_rawrays:
                    csv_path = os.path.join(
                        export_params[2],
                        export_params[3] + element_name + "-" + export_type + ".csv",
                    )
                    _write_rawrays_csv(raw_array, element_name, csv_path)
            else:
                api.export(*export_params)
        if raypyng_analysis:
            for export_params in exports:
                element_name = export_params[0]
                export_type = export_params[1]
                eff = (
                    graxpy_eff_df
                    if graxpy_eff_df is not None and element_name in downstream_elements
                    else efficiency
                )
                pp.postprocess_RawRays(
                    *export_params,
                    rml_filename,
                    suffix=export_type,
                    remove_rawrays=False,
                    raw_array=rawrays_cache.get((element_name, export_type)),
                    undulator_table=undulator_table,
                    efficiency=eff,
                )
    except Exception as e:
        print(f"ERROR! Got exception while processing {rml_filename}: {e}", flush=True)
        raise
    finally:
        # Ensure resources are cleaned up properly
        try:
            api.quit()
        except Exception:
            pass
        runner.kill()
    et = time.time()
    simulation_duration = et - st
    return simulation_duration, rml_filename
