import itertools
import os 
import numpy as np
from tqdm import tqdm
import time
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed

from .rml import RMLFile
from .rml import ObjectElement,ParamElement, BeamlineElement
from .runner import RayUIAPI,RayUIRunner
from .recipes import SimulationRecipe
from .postprocessing import PostProcess

################################################################
class SimulationParams():
    """The entry point of the simulation parameters.
    
    A class that takes care of the simulations parameters, 
    makes sure that they are written correctly,
    and returns the the list of simulations that is requested by the user.

    Args:
        rml (RMLFile/string, optional): string pointing to an rml 
                                        file with the beamline template, 
                                        or an RMLFile class object. 
                                        Defaults to None.
        param_list (list, optional): list of dictionaries containing the 
                                     parameters and values to simulate. 
                                     Defaults to None.            
    """    
    def __init__(self, rml=None, param_list=None,**kwargs) -> None:
        """ 
        Args:
            rml (RMLFile/string, optional): string pointing to an rml file with the beamline template, or an RMLFile class object. Defaults to None.
            param_list (list, optional): list of dictionaries containing the parameters and values to simulate. Defaults to None.
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

    def _validate_params(self, value):
        if not isinstance(value, list):
            raise TypeError('params must be a list')
        for item in value:
            if not isinstance(item, dict):
                raise TypeError('Each element in params must be a dictionary')
            self._validate_param_keys_values(item)

    def _validate_param_keys_values(self, param):
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
        """Refactored method to parse and extract parameters."""
        self._reset_extraction_variables()
        for parameters_dict in self.params:
            self._process_parameter_dict(parameters_dict)
        if verbose:
            self._print_extraction_results()
        return self._compilation_results()

    def _reset_extraction_variables(self):
        """Reset or initialize variables for a new extraction."""
        self.ind_param_values, self.ind_par = [], []
        self.dep_param_dependency, self.dep_value_dependency, self.dep_par = {}, [], []

    def _process_parameter_dict(self, parameters_dict):
        """Process each dictionary of parameters."""
        keys = list(parameters_dict.keys())
        if len(keys) > 1:
            self._handle_dependent_parameters(parameters_dict, keys)
        else:
            self._handle_independent_parameter(parameters_dict, keys[0])

    def _handle_dependent_parameters(self, parameters_dict, keys):
        """Handle parameters with dependencies."""
        for index, dependent_key in enumerate(keys[1:], start=1):  # Skip the first key, which is independent
            self._validate_dependency_length(parameters_dict, keys[0], dependent_key)
            self._store_dependency_info(parameters_dict, keys[0], dependent_key, index)

    def _validate_dependency_length(self, parameters_dict, independent_key, dependent_key):
        """Ensure dependent parameters match the length of their independent counterparts."""
        if len(parameters_dict[dependent_key]) != len(parameters_dict[independent_key]):
            raise ValueError(f"Dependent parameter lengths do not match for {dependent_key}.")

    def _store_dependency_info(self, parameters_dict, independent_key, dependent_key, index):
        """Store information about dependencies."""
        for idx, value in enumerate(parameters_dict[dependent_key]):
            if idx == 0:
                self.dep_value_dependency.append({parameters_dict[independent_key][idx]: value})
            else:
                self.dep_value_dependency[index-1][parameters_dict[independent_key][idx]] = value
        self.dep_param_dependency[dependent_key] = independent_key

    def _handle_independent_parameter(self, parameters_dict, key):
        """Handle independent parameters."""
        self.ind_param_values.append(parameters_dict[key])
        self.ind_par.append(key)

    def _print_extraction_results(self):
        """Print the results of the parameter extraction."""
        print('Independent parameters:', len(self.ind_par))
        print('Dependent parameters:', len(self.dep_par))

    def _compilation_results(self):
        """Compile and return the results of the extraction."""
        self.dep_par = list(self.dep_param_dependency.keys())
        return self.ind_param_values, self.ind_par, self.dep_param_dependency, self.dep_value_dependency, self.dep_par
    
    def _make_dictionary(self, keys, items):
        d = {}
        for v,k in enumerate(keys):
            # it follows a dirty little trick to ensure that all the dictionry keys
            # are different
            k.cdata=v+3987.3423421534563632
            d.update({k:items[v]})
        return d

    def params_list(self, obj=None):
        result = []
        for i in self.simulations_param_list:
            result.append(self._make_dictionary(self.param_to_simulate, i))
        return result

    def _calc_loop(self, verbose:bool=True):
        """Refactor to calculate the simulations loop with better structure."""
        self._prepare_simulation_parameters()
        self._generate_simulation_combinations()
        self._append_dependent_parameters_to_combinations()

    def _prepare_simulation_parameters(self):
        """Prepare the list of parameters to simulate."""
        self.param_to_simulate = self.ind_par + self.dep_par

    def _generate_simulation_combinations(self):
        """Generate all possible combinations of independent parameters."""
        self.loop = list(itertools.product(*self.ind_param_values))

    def _append_dependent_parameters_to_combinations(self):
        """Append dependent parameters to each combination based on dependencies."""
        self.simulations_param_list = []
        dependency_indices = self._get_dependency_indices()

        for combination in self.loop:
            extended_combination = list(combination)  # Copy to modify
            for dep_index, dep_par in enumerate(self.dep_param_dependency.keys()):
                dependent_value = self.dep_value_dependency[dep_index][combination[dependency_indices[dep_index]]]
                extended_combination.append(dependent_value)
            self.simulations_param_list.append(tuple(extended_combination))

    def _get_dependency_indices(self):
        """Get indices of independent parameters that dependent parameters rely on."""
        return [self.ind_par.index(dep) for dep in self.dep_param_dependency.values()]

    def _compilation_results(self):
        """Compile and return the results of the calculation."""
        self.par = self.ind_par + self.dep_par  # Might be redundant if not used elsewhere
        return self.param_to_simulate, self.simulations_param_list    
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
        from functools import reduce
        from operator import mul
        sim_per_round = reduce(mul, (len(values) for values in self.ind_param_values), 1)    
        return sim_per_round
  
    def simulation_parameters_generator(self):
        """Yield parameters for each simulation as a dictionary."""
        # Generate all possible combinations of independent parameters
        for combination in itertools.product(*self.ind_param_values):
            simulation_params = {}
            # Combine independent parameters with their values
            for param, value in zip(self.ind_par, combination):
                simulation_params[param] = value
            # Append dependent parameters based on the current combination
            for dep_param in self.dep_par:
                ind_param = self.dep_param_dependency[dep_param]
                ind_param_index = self.ind_par.index(ind_param)
                ind_param_value = combination[ind_param_index]
                dependent_value = self.dep_value_dependency[self.dep_par.index(dep_param)][ind_param_value]
                simulation_params[dep_param] = dependent_value
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
        self.raypyng_analysis = True  # Enable RAYPyNG analysis
        self.ray_path = ray_path  # RAY-UI installation path
        self.overwrite_rml = True  # Overwrite RML files
        self._sim_folder = None  # Simulation folder name
        
        self._simulation_name = None  # Custom simulation name
        self._exports = []  # Files to export after simulation
        self._exports_list = []  # Processed list of exports
        self.sp = None  # SimulationParams instance
        self.sim_list_path = []  # Paths to RML files
        self.sim_path = None  # Simulation directory path
        self.durations = []  # Durations of simulations
        # New variables, initialized to None where not previously specified.
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
        if isinstance(export_files, str):
            export_files = [export_files]  # Normalize single string to list
        if not all(isinstance(file, str) for file in export_files):
            raise TypeError('Export files must be specified as a string or list of strings.')
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
        _ = self.sp._extract_param(verbose=False)

    def _save_parameters_to_file(self, dir):
        """Save user input parameters to file. 
        
        It takes the values from the SimulationParams class

        Args:
            dir (str): the folder where to save the parameters
        """        
        for i,p in enumerate(self.sp.ind_par):
            filename = str(p.get_full_path().lstrip("lab.beamline."))
            filename = "input_param_"+filename.replace(".", "_")
            filename += ".dat"
            np.savetxt(os.path.join(dir,filename),self.sp.ind_param_values[i])
        for i,p in enumerate(self.sp.dep_par):
            filename = str(p.get_full_path().lstrip("lab.beamline."))
            filename = "input_param_"+filename.replace(".", "_")
            filename += ".dat"
            np.savetxt(os.path.join(dir,filename),list(self.sp.dep_value_dependency[i].values()))
    
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

    def _create_simulation_round_folder(self, round_number):
        """
        Creates a folder for each round of simulations.

        Args:
            round_number (int): The current round number of the simulation.

        Returns:
            str: The path to the created simulation round folder.
        """
        sim_folder = os.path.join(self.sim_path, f"round_{round_number}")
        if not os.path.exists(sim_folder):
            os.makedirs(sim_folder)
        return sim_folder

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
        row = [str(simulation_number)] + [param.cdata for param in params]
        
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

    def _append_exports(self, obj_element, file_names):
        """
        Appends export configurations to the exports list.

        Args:
            obj_element (ObjectElement): The simulation object element associated with the export.
            file_names (str or list): A single file name or a list of file names to export.
        """
        if isinstance(file_names, str):
            file_names = [file_names]  # Normalize to list for uniform processing
        elif not isinstance(file_names, list):
            raise ValueError('The exported param can be only str or list of str.')

        for file_name in file_names:
            self.exports_list.append((obj_element.attributes().original()['name'], file_name))

    def _print_exports(self):
        """
        Prints the compiled list of exports.
        """
        print('The following will be exported:')
        for export_name, file_name in self.exports_list:
            print(export_name, file_name)


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
        for export_config in self._exports_list:  # Corrected from exports_list to _exports_list
            export_file = os.path.join(folder, f"{sim_index}_{export_config[0]}-{export_config[1]}.csv")
            if not os.path.exists(export_file):
                return True  # Missing at least one export file
        return False

    def _make_exports_list(self, sim_number, round_n):
        exports_list = []
        path = os.path.join(self.sim_path, 'round_'+str(round_n))
        for d in self.exports:
            for exp_oe in d.keys():
                temp_exp_list = []
                temp_exp_list.append(exp_oe["name"])
                temp_exp_list.append(d[exp_oe][0])
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

    
    def _initialize_progress_bar(self, total_simulations):
        bar_format = '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {postfix}]'
        progress_bar = tqdm(total=total_simulations, bar_format=bar_format, desc="Simulations Completed")
        return progress_bar
    
    def _print_simulations_info(self):
        total_simulations = self.sp._calc_number_sim() * self.repeat
        
        # Prepare data for printing
        data = [
            ["Simulation Info", ""],
            ["Independent parameters", len(self.sp.ind_par)],
            ["Dependent parameters", len(self.sp.dep_par)],
            ["Rounds of Simulations", self._repeat],
            ["Total Number of Simulations", total_simulations]
        ]
        
        # Determine column widths by the longest item in each column
        col_widths = [max(len(str(item)) for item in col) for col in zip(*data)]
        
        # Print the header
        header = data[0]
        print(f"{header[0]:<{col_widths[0]}} | {header[1]:>{col_widths[1]}}")
        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        
        # Print the data rows
        for row in data[1:]:
            print(f"{row[0]:<{col_widths[0]}} | {row[1]:>{col_widths[1]}}")

        print("-" * (sum(col_widths) + 3))  # for the separator and spaces
        print()


    def run(self, recipe=None, multiprocessing=1, force=False, overwrite_rml=True):
        """
        Execute simulations with optional recipe, multiprocessing, and file management options.

        This method orchestrates the setup and execution of simulations, managing multiprocessing,
        file generation, and progress tracking.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup. Defaults to None.
            multiprocessing (int, optional): Number of processes for parallel execution. Defaults to 1.
            force (bool, optional): Force re-execution of simulations. Defaults to False.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
        """
        if not isinstance(multiprocessing, int) or multiprocessing < 1:
            raise ValueError("The 'multiprocessing' argument must be an integer greater than 0.")
        
        self._prepare_simulation_environment(recipe, overwrite_rml)
        total_simulations = self.sp._calc_number_sim() * self.repeat
        self._handle_simulation_recap_files(force, total_simulations)

        pbar = self._initialize_progress_bar(total_simulations)
        self._execute_simulations(multiprocessing, force, total_simulations, pbar)
        pbar.close()

    def _prepare_simulation_environment(self, recipe, overwrite_rml):
        """
        Prepares the simulation environment based on a given recipe and file management options.

        Args:
            recipe (SimulationRecipe, optional): Recipe for simulation setup. Defaults to None.
            overwrite_rml (bool, optional): Overwrite existing RML files. Defaults to True.
        """
        self._print_simulations_info()
        self.overwrite_rml = overwrite_rml
        self._setup_simulation_environment(recipe)
        self._initialize_simulation_directory()
        self._save_parameters_to_file(self.sim_path)

    def _handle_simulation_recap_files(self, force, total_simulations):
        """
        Manages recap files based on simulation settings.

        Args:
            force (bool): Force re-execution of simulations and potential recap file updates.
            total_simulations (int): Total number of simulations to be executed.
        """
        n_sim_max_for_looper = 1e7
        if total_simulations <= n_sim_max_for_looper:
            for params in self.sp.simulation_parameters_generator():
                # Corrected the call to match the expected method signature
                self._update_simulation_recap_files(params, 0)


    def _execute_simulations(self, multiprocessing, force, total_simulations, pbar):
        """
        Executes the simulations in batches with multiprocessing support.

        Args:
            multiprocessing (int): Number of processes for parallel execution.
            force (bool): Force re-execution of simulations.
            total_simulations (int): Total number of simulations to be executed.
            pbar (tqdm): Progress bar object for tracking simulation progress.
        """
        batch_size = 100  # Adjust batch size as needed
        simulations_durations = []  # Track durations of all simulations for average calculation

        with ProcessPoolExecutor(max_workers=multiprocessing) as executor:
            simulation_params_batch = []
            for round_number in range(self.repeat):
                for sim_number, params in enumerate(self.sp.simulation_parameters_generator()):
                    if self._is_simulation_missing(sim_number, round_number) or force:
                        self._prepare_and_submit_simulation(params, sim_number, round_number, simulation_params_batch, executor, force)
                    else:
                        pbar.update(1)  # If not missing or forced, update progress bar directly
                    if len(simulation_params_batch) == batch_size or sim_number == total_simulations - 1:
                        self._wait_for_simulation_batch(simulations_durations, simulation_params_batch, executor, pbar)

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
        for future in as_completed(futures):
            try:
                sim_duration = future.result()
                simulations_durations.append(sim_duration)
                self._update_progress_bar(simulations_durations, pbar)
            except Exception as e:
                print(f"Exception during simulation: {e}")
        simulation_params_batch.clear()  # Reset batch for next set of simulations

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
        eta_seconds = avg_duration * remaining_simulations
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
            if not analyze and raypyng_analysis:
                pp.postprocess_RawRays(*export_params, rml_filename)
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
    return simulation_duration

