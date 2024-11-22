import itertools
import os 
import sys
import re
import numpy as np
from tqdm import tqdm
import time
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import pandas as pd 

from .rml import RMLFile
from .rml import ObjectElement,ParamElement, BeamlineElement
from .runner import RayUIAPI,RayUIRunner
from .recipes import SimulationRecipe
from .postprocessing import PostProcess

################################################################
class SimulationParams():
    """Handles the setup and management of simulation parameters for RAY-UI simulations.

    This class is responsible for organizing simulation parameters, both independent and dependent,
    and generating the necessary parameter sets for conducting simulations.

    Attributes:
        rml (RMLFile or str): The RML file or the path to the RML file used as the template for simulations.
        params (list of dict): A list of dictionaries where each dictionary represents a set of parameters
                               to simulate. Each key in the dictionary is a ParamElement, and its value
                               is the parameter value(s) to simulate.
    """
    
    def __init__(self, rml=None, param_list=None,**kwargs) -> None:
        """Initializes the SimulationParams class with a RML file and a list of parameter dictionaries.

        Args:
            rml (RMLFile or str, optional): The RML file or the path to the RML file used as the template for simulations.
            param_list (list of dict, optional): A list of dictionaries where each dictionary represents a set of parameters
                                                  to simulate. Defaults to None.
        """        
        self._rml = self._initialize_rml(rml, **kwargs)  # Initializes the RML file or RMLFile object
        self.params = param_list or []  # List of dictionaries for parameters to simulate
        self.param_to_simulate = []  # List of parameters to be simulated
        self.simulations_param_list = []  # List of simulations based on the parameters
        self.ind_param_values = []  # Independent parameter values for simulations
        self.ind_par = []  # Independent parameters
        self.dep_param_dependency = {}  # Dependencies between parameters
        self.dep_value_dependency = []  # Values dependent on other parameters
        self.dep_par = []  # Dependent parameters
        self.loop = []  # Product of independent parameter values for generating simulations
        self.par = None  # Compiled result of parameters for simulation

    def _initialize_rml(self, rml, **kwargs):
        """Initializes the RML file or RMLFile object based on the provided RML path or object.

        Args:
            rml (RMLFile or str): The RML file or the path to the RML file used as the template for simulations.

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
            raise ValueError(f"The rml should be either a string point to n rml file or an instance of the RMLFile class. You passed a {type(rml)}")

    @property
    def rml(self):
        return self._rml

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        self._validate_params(value)
        self._params = value
        self._extract_param()

    def _validate_params(self, value):
        """Validates the input parameter list to ensure it is in the correct format.

        Args:
            value (list): The parameter list to be validated.

        Raises:
            TypeError: If the input value is not a list or if the elements of the list are not dictionaries.
        """
        if not isinstance(value, list):
            raise TypeError('params must be a list')
        for item in value:
            if not isinstance(item, dict):
                raise TypeError('Each element in params must be a dictionary')
            self._validate_param_keys_values(item)

    def _validate_param_keys_values(self, param):
        """Validates the keys and values of a parameter dictionary.

        Args:
            param (dict): The parameter dictionary to be validated.

        Raises:
            TypeError: If the keys are not instances of ParamElement or if the values are not valid types.
        """
        for key, value in param.items():
            if not isinstance(key, ParamElement):
                raise TypeError(f'Keys must be ParamElement instances, found {type(key)}')
            self._validate_value_type(param, value, key)

    def _validate_value_type(self, param, value, key):
        if not isinstance(value, (list, float, int, str)) and not hasattr(value, '__iter__'):
            raise TypeError(f'Invalid type for parameter {key}: {type(value)}')
        if not isinstance(value, list):
            param[key] = [value] if isinstance(value, (float, int, str)) else list(value)
        
    def _extract_param(self, verbose:bool=False):
        """Extracts and organizes parameters from the input parameter list.

        Args:
            verbose (bool, optional): If set to True, prints the results of the parameter extraction. Defaults to False.

        Returns:
            tuple: A tuple containing the organized parameters and their values.
        """
        self._reset_extraction_variables()
        for parameters_dict in self.params:
            self._process_parameter_dict(parameters_dict)
        if verbose:
            self._print_extraction_results()
        #return self._compilation_results()

    def _reset_extraction_variables(self):
        """Reset or initialize variables for a new extraction."""
        self.ind_param_values, self.ind_par = [], []
        self.dep_param_dependency, self.dep_value_dependency, self.dep_par = {}, {}, []

    def _process_parameter_dict(self, parameters_dict):
        """Process each dictionary of parameters."""
        keys = list(parameters_dict.keys())
        items = list(parameters_dict.items())
        # add independent params
        self.ind_par.append(keys[0])
        self.ind_param_values.append(items[0])
        
        if len(keys) > 1:
            for k in keys[1:]:
                self.dep_param_dependency[k] = keys[0]
                self.dep_par.append(k)
                for ind, ind_par_value in enumerate(items[0][1]):
                    if ind_par_value in list(self.dep_value_dependency.keys()):
                        self.dep_value_dependency[ind_par_value].append(parameters_dict[k][ind])
                    else:
                        self.dep_value_dependency[ind_par_value] = [parameters_dict[k][ind]]
               

    def _validate_dependency_length(self, parameters_dict, independent_key, dependent_key):
        """Ensure dependent parameters match the length of their independent counterparts."""
        if len(parameters_dict[dependent_key]) != len(parameters_dict[independent_key]):
            raise ValueError(f"Dependent parameter lengths do not match for {dependent_key}.")

    def _print_extraction_results(self):
        """Print the results of the parameter extraction."""
        print('Independent parameters:', len(self.ind_par))
        print('Dependent parameters:', len(self.dep_par))

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
        return param.enabled=='T'
    
    def _enable_param(self, param):
        """Set :code:`enabled='T'` and :code:`auto='F'` in a beamline object

        Args:
            param (RML object): beamline object
        """        
        if not self._check_if_enabled(param):
            param.enabled = 'T'
        try:
            param.auto = 'F'
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
        if not isinstance(value,str):
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

    def simulation_parameters_generator(self):
        """Generates a dictionary of parameters for each simulation based on the input parameter list.

        Yields:
            dict: A dictionary of parameters for a single simulation.
        """
        # Extract the keys (first elements of tuples) and the lists of possible values (second elements)
        keys, value_lists = zip(*self.ind_param_values)
        # Generate all combinations of values using itertools.product
        for values_combination in itertools.product(*value_lists):
            # Create a dictionary for the current combination, pairing keys with their respective values
            simulation_params = dict(zip(keys, values_combination))
            # add dependen parameters
            if len(self.dep_param_dependency.keys()) > 0:
                for ind, dep_par in enumerate(self.dep_param_dependency.keys()):
                    depending_param = self.dep_param_dependency[dep_par]
                    value_depending_param = simulation_params[depending_param]
                    dep_par_value = self.dep_value_dependency[value_depending_param][ind]
                    simulation_params[dep_par] = dep_par_value
            yield simulation_params











################################################################
class Simulate():
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
    def __init__(self, rml=None, hide=False,ray_path=None,**kwargs) -> None:
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

        Raises:
            Exception: If the rml file is not defined an exception is raised
        """
        if rml is not None:
            if isinstance(rml,RMLFile):
                self._rml = rml
            else: # assume that parameter is the file name as required for RMLFile
                self._rml = RMLFile(None,template=rml)
        else:
            raise Exception("rml file must be defined")
        

        
        self._rml = rml if isinstance(rml, RMLFile) else RMLFile(None, template=rml) if rml else None
        self.path = None  # Path for simulation execution
        self.prefix = 'RAYPy_Simulation'  # Simulation prefix
        self._hide = hide  # Hide GUI leftovers
        self.analyze = True  # Enable RAY-UI analysis
        self._repeat = 1  # Number of simulation repeats
        self.raypyng_analysis = False  # Enable RAYPyNG analysis
        self.ray_path = ray_path  # RAY-UI installation path
        self.overwrite_rml = True  # Overwrite RML files
        self._sim_folder = None  # Simulation folder name
        self.batch_size = 50#1e6
        self._simulation_timeout = 60
        self._batch_number = None
        
        self._simulation_name = None  # Custom simulation name
        self._exports = []  # Files to export after simulation
        self._exports_list = []  # Processed list of exports
        self._exported_obj_names_list = [] # List containing the names of the objects to export
        self.sp = None  # SimulationParams instance
        self.sim_list_path = []  # Paths to RML files
        self.sim_path = None  # Simulation directory path
        self.durations = []  # Durations of simulations
        self.total_duration = None  # Total duration of all simulations
        self.completed_simulations = None  # Count of completed simulations
        self._possible_exports = ['AnglePhiDistribution', # possible exports when RAY-UI analysis is active
                                'AnglePsiDistribution',
                                'BeamPropertiesPlotSnapshot',
                                'EnergyDistribution',
                                'FootprintAbsorbedRays',
                                'FootprintAllRays',
                                'FootprintOutgoingRays',
                                'FootprintPlotSnapshot',
                                'FootprintWastedRays',
                                'IntensityPlotSnapshot',
                                'IntensityX',
                                'IntensityYZ',
                                'PathlengthDistribution',
                                'RawRaysBeam',
                                'RawRaysIncoming',
                                'RawRaysOutgoing',
                                'ScalarBeamProperties',
                                'ScalarElementProperties'
                             ]
        self._possible_exports_without_analysis = ['RawRaysIncoming', # possible exports when RAY-UI analysis is not active
                                'RawRaysOutgoing'
                             ]

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
        """RMLFile object instantiated in init
        """        
        return self._rml

    @property 
    def simulation_name(self):
        """A string to append to the folder where the simulations will be executed.
        """        
        return self._simulation_name
    
    @simulation_name.setter
    def simulation_name(self,value):
        self._simulation_name = value
        self._sim_folder = self.prefix+'_'+self._simulation_name

    @property 
    def analyze(self):
        """Turn on or off the RAY-UI analysis of the results. 
        The analysis of the results takes time, so turn it on only if needed

        Returns:
            bool: True: analysis on, False: analysis off
        """        
        return self._analyze
    
    @analyze.setter
    def analyze(self,value):
        if not isinstance(value, bool):
            raise ValueError ('Only bool are allowed')
        self._analyze = value

    @property 
    def raypyng_analysis(self):
        """Turn on or off the RAYPyNG analysis of the results. 

        Returns:
            bool: True: analysis on, False: analysis off
        """        
        return self._raypyng_analysis
    
    @raypyng_analysis.setter
    def raypyng_analysis(self,value):
        if not isinstance(value, bool):
            raise ValueError ('Only bool are allowed')
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
    def repeat(self,value):
        if not isinstance(value, int):
            raise ValueError ('Only int are allowed')
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
    def path(self,value):
        if value == None:
            value=os.getcwd()
        if not isinstance(value, str):
            raise ValueError ('Only str are allowed')
        if not os.path.exists(value):
            raise ValueError('The path does not exist')
        self._path = value

    @property 
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self,value):
        if not isinstance(value, str):
            raise ValueError ('Only str are allowed')
        self._prefix = value

    @property 
    def exports(self):
        """Get the list of files to export after the simulation is complete."""
        return self._exports

    @exports.setter
    def exports(self, value):
        """
        Validates and sets the exports list for simulation results.

        Args:
            value (list): A list of dictionaries specifying the exports configuration.
        
        Raises:
            TypeError: If the input is not a list or the contents of the list are not as expected.
        """
        self._validate_export_list(value)
        self._exports = value
        self._exports_list = self._generate_exports_list(value)
        self._exported_obj_names_list = self._generate_exported_obj_names_list(value)

    def _validate_export_list(self, export_list):
        """
        Validates that the provided export list is properly formatted.

        Args:
            export_list (list): The exports list to validate.
        
        Raises:
            TypeError: If the export list is not a list or contains non-dictionary items.
        """
        if not isinstance(export_list, list):
            raise TypeError('The exports must be a list.')
        for export_dict in export_list:
            self._validate_export_dict(export_dict)

    def _validate_export_dict(self, export_dict):
        """
        Validates that each dictionary in the export list is correctly structured.

        Args:
            export_dict (dict): A dictionary representing an export configuration.
        
        Raises:
            TypeError: If the export configuration is not a dictionary or has incorrect key/value types.
        """
        if not isinstance(export_dict, dict):
            raise TypeError('Each export configuration must be a dictionary.')
        for object_element, export_files in export_dict.items():
            self._validate_export_entry(object_element, export_files)

    def _validate_export_entry(self, object_element, export_files):
        """
        Validates each export entry within the export configuration dictionary.

        Args:
            object_element (ObjectElement): The object element associated with the export.
            export_files (str or list): The file or files to be exported for the object element.
        
        Raises:
            TypeError: If the keys are not instances of ObjectElement or if export_files are not correctly specified.
        """
        if not isinstance(object_element, ObjectElement):
            raise TypeError('Keys of the export dictionary must be instances of ObjectElement.')
        if not isinstance(export_files, list):
            raise ValueError('The exported files should be written as a list')
        if not all(isinstance(file, str) for file in export_files):
            raise TypeError('Export files must be specified as a list of strings.')
        self._validate_export_files_existence(export_files)

    def _validate_export_files_existence(self, export_files):
        """
        Validates that the specified export files are eligible for export based on current settings.

        Args:
            export_files (list): A list of filenames to be exported.
        
        Raises:
            ValueError: If any of the specified files cannot be exported based on the current configuration.
        """
        possible_exports = self.possible_exports if self.analyze else self.possible_exports_without_analysis
        for file in export_files:
            if file not in possible_exports:
                raise ValueError(f'Cannot export {file}. Check spelling or analysis settings.')

    def _generate_exports_list(self, export_list):
        """
        Generates a comprehensive list of exports based on the provided export configurations.

        Args:
            export_list (list): The validated list of export configurations.

        Returns:
            list: A list of tuples, each containing the name of an object element and a filename to export.
        """
        exports_list = []
        for export_dict in export_list:
            for object_element, export_files in export_dict.items():
                if isinstance(export_files, str):
                    export_files = [export_files]  # Ensure it's a list
                for file in export_files:
                    exports_list.append((object_element.attributes().original()['name'], file))
        return exports_list

    def _generate_exported_obj_names_list(self, export_list):
        """
        Generates a list with the names of the objects that will be exported.

        Args:
            export_list (list): The validated list of export configurations.

        Returns:
            list: A list of str representing the names of the objects to export.
        """
        self._exported_obj_names_list = []
        for export_dict in export_list:
            for object_element, export_files in export_dict.items():
                if isinstance(export_files, str):
                    export_files = [export_files]  # Ensure it's a list
                for file in export_files:
                    self._exported_obj_names_list.append(object_element.attributes().original()['name'])
        return self._exported_obj_names_list

    @property
    def params(self):
        """The parameters to scan, as a list of dictionaries.

        For each dictionary the keys are the parameters elements of the beamline, and the values are the 
        values to be assigned.
        """               
        return self.param

    @params.setter
    def params(self,value):
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
            filename = str(p.get_full_path().lstrip("lab.beamline."))
            filename = "input_param_"+filename.replace(".", "_")
            filename += ".dat"
            filepath = os.path.join(dir, filename)
            with open(filepath, 'w') as f:
                values = self.sp.ind_param_values[i]
                for item in values[1]:
                        f.write(f"{item}\n")

        for i, p in enumerate(self.sp.dep_par):
            filename = str(p.get_full_path().lstrip("lab.beamline."))
            filename = "input_param_"+filename.replace(".", "_")
            filename += ".dat"
            filepath = os.path.join(dir, filename)
            with open(filepath, 'w') as f:
                values = list(self.sp.dep_value_dependency.items())
                for item in values:
                        f.write(f"{item[1][i]}\n")

    def rml_list(self, recipe=None, overwrite_rml=True):
        """
        Creates the folder structure and RML files needed for simulation. This method organizes simulation parameters into RML files and prepares the directory structure for simulations, which is useful for pre-simulation checks and manual adjustments.

        Args:
            recipe (SimulationRecipe, optional): Recipe to use for setting up the simulation. Defaults to None.
            overwrite_rml (bool, optional): If True, existing RML files will be overwritten. Defaults to True.

        """
        self.overwrite_rml = overwrite_rml
        self._setup_simulation_environment(recipe)
        self._initialize_simulation_directory()

        if overwrite_rml:
            recap_csv_path = os.path.join(self.sim_path, 'looper.csv')
            if os.path.exists(recap_csv_path):
                os.remove(recap_csv_path)
            recap_txt_path = os.path.join(self.sim_path, 'looper.txt')
            if os.path.exists(recap_txt_path):
                os.remove(recap_txt_path)
        
        for round_number in range(self.repeat):
            sim_number = 0
            for params in self.sp.simulation_parameters_generator():
                _ = self._generate_rml_file(sim_number, round_number, params)
                if round_number==0:
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
            round_folder_path = os.path.join(self.sim_path, 'round_'+str(round_n))
            if not os.path.exists(round_folder_path):
                os.makedirs(round_folder_path)

    def _generate_rml_file(self, sim_number,round_n, param_set):
        """
        Generates an RML file for a given simulation setup.

        Args:
            sim_folder (str): The folder where the RML file should be saved.
            sim_number (int): The simulation number within the current round.
            param_set (dict): The parameter set for the current simulation.

        Returns:
            str: The path to the generated RML file.
        """
        round_folder = 'round_'+str(round_n)
        rml_path = os.path.join(self._sim_folder, round_folder,f"{sim_number}_{self.simulation_name}.rml")
        
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
        recap_csv_path = os.path.join(self.sim_path, 'looper.csv')
        recap_txt_path = os.path.join(self.sim_path, 'looper.txt')

        # Check if the files exist to determine if headers need to be written
        csv_file_exists = os.path.exists(recap_csv_path)
        txt_file_exists = os.path.exists(recap_txt_path)
        
        # Prepare data for CSV and TXT files
        header = ['Simulation Number'] + [f"{param._parent['name']}.{param['id']}" for param in params]
        row = [str(simulation_number)] + [param for param in params.values()]

        # Update CSV file
        with open(recap_csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not csv_file_exists:
                writer.writerow(header)
            writer.writerow(row)
        
        # Prepare and update TXT file with nice formatting
        with open(recap_txt_path, 'a') as txtfile:
            if not txt_file_exists:
                # Write header with nice formatting
                txtfile.write(' '.join(header) + '\n')
            
            # Determine the maximum width for each column
            column_widths = [max(len(str(simulation_number)), max(len(h), max(len(str(r)) for r in row))) for h, r in zip(header, row)]
            
            # Format row with aligned columns
            formatted_row = ' '.join(str(r).ljust(w) for r, w in zip(row, column_widths))
            
            # Write the formatted row to the TXT file
            txtfile.write(formatted_row + '\n')


    def _is_simulation_missing(self, sim_index, repeat):
        """
        Checks if a simulation is missing based on the existence of its export files.

        Args:
            simulation_index (int): The index of the simulation in the simulation list.

        Returns:
            bool: True if the simulation is missing any export files, False otherwise.
        """
        round_folder = 'round_'+str(repeat)
        folder = os.path.join(self._sim_folder, round_folder)
        for export_config in self._exports_list:  
            export_file = os.path.join(folder, f"{sim_index}_{export_config[0]}-{export_config[1]}.csv")
            if not os.path.exists(export_file):
                return True  # Missing at least one export file
        return False

    def _make_exports_list(self, sim_number, round_n):
        exports_list = []
        path = os.path.join(self.sim_path, 'round_'+str(round_n))
        for d in self.exports:
            for exp_oe in d.keys():
                for exp in d[exp_oe]:
                    temp_exp_list = []
                    temp_exp_list.append(exp_oe["name"])
                    temp_exp_list.append(exp)
                    temp_exp_list.append(path)
                    temp_exp_list.append(str(sim_number)+'_')
                    exports_list.append(temp_exp_list)
        return exports_list

    
    def _format_eta(self, seconds):
        """Format seconds into days, hours, and minutes."""
        days, seconds = divmod(int(seconds), 86400)
        hours, seconds = divmod(int(seconds), 3600)
        minutes, seconds = divmod(int(seconds), 60)
        if days > 0:
            return f"{days} day(s), {int(hours):02d}h:{int(minutes):02d}min"
        else:
            return f"{int(hours):02d}h:{int(minutes):02d}min"

    
    def _initialize_progress_bar(self, total_simulations, description="Simulations Completed"):
        bar_format = '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {postfix}]'
        progress_bar = tqdm(total=total_simulations, bar_format=bar_format, desc=description)
        return progress_bar
    
    def _print_simulations_info(self):
        total_simulations = self.sp._calc_number_sim() * self.repeat
        
        # Prepare data for printing
        data = [
            ["RML File ", os.path.basename(self._rml._template)],
            ["Simulation Name",self._sim_folder],
            ["Independent Parameters", len(self.sp.ind_par)],
            ["Dependent Parameters", len(self.sp.dep_par)],
            ["Rounds of Simulations", self._repeat],
            ["Total Number of Simulations", total_simulations]
        ]
        
        # Determine column widths by the longest item in each column
        col_widths = [max(len(str(item)) for item in col) for col in zip(*data)]
        
        print()
        print('Simulation Info')

        # Print the data rows
        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        for row in data[0:]:
            print(f"{row[0]:<{col_widths[0]}} | {row[1]:>{col_widths[1]}}")

        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        print()

    def _init_logging(self):
        """Initializes logging for the simulation."""
        log_filename = os.path.join(self.sim_path,'simulation.log')
        logging.basicConfig(filename=log_filename, filemode='a', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.info(f'Simulation started, using {self._workers} workers')
        
    def run(self, recipe=None, multiprocessing=1, force=False, overwrite_rml=True, force_exit=True):
        """
        Execute simulations with optional recipe, multiprocessing, and file management options.

        This method orchestrates the setup and execution of simulations, managing multiprocessing,
        file generation, and progress tracking.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup. Defaults to None.
            multiprocessing (int, optional): Number of processes for parallel execution. Defaults to 1.
            force (bool, optional): Force re-execution of simulations. Defaults to False.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
            force_exit (bool, optional): calls os.exit when the simulations are complete. Nothing else will run after it. Defaults to True.
        """
        if not isinstance(multiprocessing, int) or multiprocessing < 1:
            raise ValueError("The 'multiprocessing' argument must be an integer greater than 0.")
        
        # test that we car run RAY-UI
        runner = RayUIRunner(ray_path=self.ray_path, hide=True)
        runner.kill()

        self._batch_number = 0
        self._workers = multiprocessing
        self.batch_size = int(self._workers)*5  
        self._prepare_simulation_environment(recipe, overwrite_rml)
        self._init_logging()
        total_simulations = self.sp._calc_number_sim() * self.repeat
        self.simulations_checked = False

        pbar = self._initialize_progress_bar(total_simulations, description='Simulations Completed')
        try:
            self._execute_simulations(multiprocessing, force, total_simulations, pbar)
            pbar.close()
            self.logger.info('Simulation completed successfully.')
        except Exception as e:
            self.logger.error('Simulation failed.', exc_info=True) 
        if self.raypyng_analysis:
            self.logger.info('Starting cleanup')
            pp = PostProcess()
            pp.cleanup(self.sim_path, self.repeat, self._exported_obj_names_list)
            self.logger.info('Done with the cleanup')
            if self.analyze == False and self.raypyng_analysis == True:
                self.logger.info('Create Pandas Recap Files')
                self._create_results_dataframe()
        self.logger.info('End of the Simulations')
        if force_exit:
            os._exit(0)
        
    def _create_results_dataframe(self):
        looper_path = os.path.join(self.sim_path, 'looper.csv')
        looper = pd.read_csv(looper_path)
        for export in self._exported_obj_names_list:
            for in_out in ['RawRaysIncoming', 'RawRaysOutgoing']:
                oe_path = os.path.join(self.sim_path,f'{export}_{in_out}.dat')
                # Reading the data into a DataFrame, specify no comment handling and read headers normally
                res = pd.read_csv(oe_path, sep="\t", comment=None, header=0)
                # Manually remove the '#' from the first column name
                res.columns = [col.replace('#', '').strip() for col in res.columns]
                res_combined = pd.concat([looper, res], axis=1)
                res_combined.to_csv(os.path.join(self.sim_path,f'{export}_{in_out}.csv'))

    def _remove_recap_files(self,):

        # Filter files ending with ".csv" or ".data"
        files_to_remove = ['looper.csv', 'looper.txt']

        # Remove filtered files
        for file in files_to_remove:
            to_be_removed = os.path.join(self.sim_path, file)
            if os.path.exists(to_be_removed):
                os.remove(to_be_removed)

    def _prepare_simulation_environment(self, recipe, overwrite_rml):
        """
        Prepares the simulation environment based on a given recipe and file management options.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup. Defaults to None.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
        """
        self.overwrite_rml = overwrite_rml
        self._setup_simulation_environment(recipe)
        self._initialize_simulation_directory()
        self._save_parameters_to_file(self.sim_path)
        self._remove_recap_files()
        self._print_simulations_info()

    def _execute_simulations(self, multiprocessing, force, total_simulations, pbar, update_reacap_files=True):
        """
        Executes the simulations in batches with multiprocessing support.

        Args:
            multiprocessing (int): Number of processes for parallel execution.
            force (bool): Force re-execution of simulations.
            total_simulations (int): Total number of simulations to be executed.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        simulations_durations = []  # Track durations of all simulations for average calculation

        try:
            with ProcessPoolExecutor(max_workers=multiprocessing) as executor:
                simulation_params_batch = []
                batch_length = 0
                remaining_simulations = total_simulations
                for round_number in range(self.repeat):
                    self.logger.info(f'Start round {round_number}')
                    for sim_number, params in enumerate(self.sp.simulation_parameters_generator()):
                        if round_number==0 and update_reacap_files==True:
                            self._update_simulation_recap_files(params, sim_number)
                        if self._is_simulation_missing(sim_number, round_number) or force:
                            self._prepare_and_submit_simulation(params, sim_number, round_number, simulation_params_batch, executor, force)       
                        else:
                            pbar.update(1)  # If not missing or forced, update progress bar directly
                        batch_length += 1
                        remaining_simulations -= 1
                        if batch_length == self.batch_size or remaining_simulations == 0:
                            self._wait_for_simulation_batch(simulations_durations, simulation_params_batch, executor, pbar)
                            self.logger.info(f'Waiting For batch, {self.batch_size} simulations to go')
                            batch_length = 0
                        if remaining_simulations == 0:
                            self.logger.info(f'Remaning Simulations {remaining_simulations}, stop the simulations loop')
                            self._final_check_on_simulations_and_shutdown(executor, pbar)
                            executor.shutdown(wait=False, cancel_futures=True)
                            break 
        except Exception as e:
            self.logger.info(f'Error in _execute simulations: {e}')
            executor.shutdown(wait=False)
            self.logger.info('Executor shutdown completed.')
        
        

    def _final_check_on_simulations_and_shutdown(self, executor, old_pbar):

        #check that all simulatins are completed:
        self.logger.info(f'Checking that all simulations are completed before stopping the ProcessPoolExecutor')
        missing_sim = []
        for round_number in range(self.repeat):
            for sim_number, params in enumerate(self.sp.simulation_parameters_generator()):
                if self._is_simulation_missing(sim_number, round_number):
                    self.logger.info(f'This simulation is missing: round {round_number}, number {sim_number}')
                    missing_sim.append({'round': round_number, 'sim_number':sim_number})

        executor.shutdown(wait=False)
        self.logger.info('Executor shutdown completed.')

        if len(missing_sim) >=1 and self.simulations_checked==False:
            self.logger.info('Finish missing simulations')
            total_simulations = self.sp._calc_number_sim() * self.repeat
            old_pbar.close()
            pbar = self._initialize_progress_bar(total_simulations,description='Checking Simulations')
            self.simulations_checked = True
            self._execute_simulations(self._workers, False, total_simulations, pbar, update_reacap_files=False)

    def _prepare_and_submit_simulation(self, params, sim_number, round_number, simulation_params_batch, executor, force):
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
        simulation_params = ((rml_file_path, self._hide, self.analyze, self.raypyng_analysis, self.ray_path), exp_list)
        simulation_params_batch.append(simulation_params)
        self.logger.info(f'Prepared sim number: {sim_number}: {rml_file_path}')


    def _wait_for_simulation_batch(self, simulations_durations, simulation_params_batch, executor, pbar):
        """
        Waits for a batch of simulations to complete and updates the progress bar.

        Args:
            simulations_durations (list): List to track durations of completed simulations.
            simulation_params_batch (list): Batch of simulation parameters that were submitted.
            executor (ProcessPoolExecutor): Executor for multiprocessing.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        futures = {executor.submit(run_rml_func, sim_params): sim_params for sim_params in simulation_params_batch}
        completed_sim = 0
        remaining_simulations = self.batch_size
        self.logger.info(f'Waiting for batch number: {self._batch_number}, timeout: {self._simulation_timeout}s')
        self._batch_number += 1
        try:
            for future in as_completed(futures, timeout=self._simulation_timeout):
                sim_duration, rml_filename = future.result()
                simulations_durations.append(sim_duration)
                self._simulation_timeout = (np.mean(simulations_durations)*self.batch_size/self._workers*1.2)
                self._update_progress_bar(simulations_durations, pbar)
                completed_sim += 1
                remaining_simulations -= 1
                self.logger.info(f'Completed: {completed_sim}, remaining: {remaining_simulations}, {rml_filename}')
                # if remaining_simulations == 1:
                #     break
        except Exception as e:
            self.logger.info(f'Exception during simulation: {e}')
            try:
                wait_time = self._simulation_timeout/4
                for sim in simulation_params_batch:
                    _,exp_list = sim
                    exp = exp_list[0]
                    round_n = int(re.findall(r'(?<=round_)\d+', exp[-2])[0])
                    sim_n = int(re.findall(r'\d+', exp[-1])[0])
                    sim_file = sim[0][0]
                    while self._is_simulation_missing(sim_n, round_n) and wait_time>0:
                        time.sleep(5)
                        wait_time -= 5
                        self.logger.info(f'Waiting for file {sim_file}, wait_time {wait_time}')
            except Exception as e:
                self.logger.info(f'Exception checking simulations: {e}')
            if wait_time>=0:
                self.logger.info(f'Found all simulations of the batch, futures missed {remaining_simulations} simulations')
            else:
                self.logger.info(f'Found most simulations of the batch, futures missed at least {remaining_simulations} simulations')
            for i in range(remaining_simulations):
                self._update_progress_bar(simulations_durations, pbar)
            self.logger.info('Updated progress bar')
            
        simulation_params_batch.clear()  # Reset batch for next set of simulations
        self.logger.info(f'Batch Completed')

    def _update_progress_bar(self, simulations_durations, pbar):
        """
        Updates the progress bar based on completed simulations.

        Args:
            simulations_durations (list): List of durations for completed simulations.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        avg_duration = sum(simulations_durations) / len(simulations_durations)
        last_duration = simulations_durations[-1]
        remaining_simulations = pbar.total - pbar.n
        eta_seconds = avg_duration * remaining_simulations / self._workers
        eta_str = self._format_eta(eta_seconds)
        pbar.set_postfix_str(f"ETA: {eta_str}, Last: {last_duration:.2f}s, Avg: {avg_duration:.2f}s/it", refresh=True)
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
            print('recipe')
            self.params = recipe.params(self)
            self.exports = recipe.exports(self)
            self.simulation_name = recipe.simulation_name(self)
    
    def reflectivity(self, reflectivity=True):
        """Switch the reflectivity of all the optical elements in the beamline on or off.

        Args:
            reflectivity (bool, optional): If :code:`True` the reflectivity is switched on,
                                           if :code:`False` the reflectivity is switched off.
                                           Defaults to True.
        """        
        if reflectivity: 
            on_off = '1'
        else:
            on_off = '0'

        for oe in self.rml.beamline.children():
                if hasattr(oe,"reflectivityType"):
                    oe.reflectivityType.cdata = on_off
         
def run_rml_func(parameters):
    """
    Executes a simulation for a given RML file and handles exporting of results.

    Args:
        parameters (tuple): A tuple containing the necessary parameters for the simulation run,
                            which includes the RML filename, hide flag, analyze flag, raypyng analysis flag,
                            and the path to the RAY-UI installation.
    """
    st = time.time()
    (rml_filename, hide, analyze, raypyng_analysis, ray_path), exports = parameters
    runner = RayUIRunner(ray_path=ray_path, hide=hide)
    api = RayUIAPI(runner)
    pp = PostProcess()
    try:
        runner.run()
        api.load(rml_filename)
        api.trace(analyze=analyze)
        api.save(rml_filename)
        for export_params in exports:
            api.export(*export_params)
            if raypyng_analysis:
                pp.postprocess_RawRays(*export_params, rml_filename, suffix=export_params[1])
    except Exception as e:
        print(f"WARNING! Got exception while processing {rml_filename}, the error was: {e}")
    finally:
        # Ensure resources are cleaned up properly
        try:
            api.quit()
        except Exception as e:
            print(f"WARNING! Got exception while quitting API for {rml_filename}, the error was: {e}")
        runner.kill()
    et = time.time()
    simulation_duration = et-st
    return simulation_duration, rml_filename

