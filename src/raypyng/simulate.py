import raypyng
from .rml import RMLFile
from .rml import ObjectElement,ParamElement, BeamlineElement
import itertools
import os 
import numpy as np

from .runner import RayUIAPI,RayUIRunner
from .recipes import SimulationRecipe
from .multiprocessing import RunPool
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
        self._rml = self._initialize_rml(rml, **kwargs)
        self.params = param_list or []
        self.param_to_simulate = []  # Initialize the attribute here
        self.simulations_param_list = []  # Initialize the attribute here

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
        print('###########################################')
        print('Independent parameter values:', self.ind_param_values)
        print('Independent parameters:', self.ind_par)
        print('###########################################')
        print('Dependency dictionary:', self.dep_param_dependency)
        print('Dependent value dependency:', self.dep_value_dependency)

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

        if verbose:
            self._print_simulation_details()

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

    def _print_simulation_details(self):
        """Print details about the simulations setup."""
        print('You have defined:')
        print(f"{len(self.ind_par)} independent parameters")
        print(f"{len(self.dep_par)} dependent parameters or set parameters")
        print(f"{len(self.simulations_param_list)} simulations")

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
        
        self.path             = None
        self.prefix           = 'RAYPy_Simulation'
        self._hide            = hide
        self.analyze          = True
        self._repeat          = 1
        self.raypyng_analysis = True
        self.ray_path         = ray_path
        self.overwrite_rml    = True


    @property
    def possible_exports(self):
        """A list of the files that can be exported by RAY-UI

        Returns:
            list: list of the names of the possible exports for RAY-UI
        """        
        self._possible_exports = ['AnglePhiDistribution',
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
        return self._possible_exports
    
    @property
    def possible_exports_without_analysis(self):
        """A list of the files that can be exported by RAY-UI when the 
        analysis option is turned off

        Returns:
            list: list of the names of the possible exports for RAY-UI when analysis is off
        """        
        self._possible_exports_without_analysis = ['RawRaysIncoming',
                                'RawRaysOutgoing'
                             ]
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
            #raise AssertionError('Params must be an instance of SimulationParams, while it is', type(params))
            sp = SimulationParams(self.rml)
            sp.params = value
            self.sp = sp
        else:
            self.sp = value
        _ = self.sp._extract_param(verbose=False)
        _ =self.sp._calc_loop()

    def save_parameters_to_file(self, dir):
        """Save user input parameters to file. 
        
        It takes the values from the SimulationParams class

        Args:
            dir (str): the folder where to save the parameters
        """        
        # do it first for indipendent parameters
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
    
    def rml_list(self):
        """
        Creates the folder structure and RML files needed for simulation.

        This function organizes simulation parameters into RML files and
        prepares the directory structure for simulations. It's useful for
        pre-simulation checks and manual adjustments.

        Returns:
            list: A list of RMLFile objects representing the simulations to run.
        """
        self._initialize_simulation_directory()
        self.save_parameters_to_file(self.sim_path)
        result = self._generate_rml_files_for_each_round()
        self._create_simulation_recap_files()
        return result

    def _initialize_simulation_directory(self):
        """Initializes the directory structure for simulations."""
        self.sim_list_path = []
        self.sim_path = os.path.join(self.path, f"{self.prefix}_{self.simulation_name}")
        if not os.path.exists(self.sim_path):
            os.makedirs(self.sim_path)

    def _generate_rml_files_for_each_round(self):
        """Generates RML files for each simulation round."""
        result = []
        for round_number in range(self.repeat):
            sim_folder = self._create_simulation_round_folder(round_number)
            for sim_number, param_set in enumerate(self.sp.params_list()):
                rml_path = self._generate_rml_file(sim_folder, sim_number, param_set)
                result.append(RMLFile(rml_path))
        return result

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

    def _generate_rml_file(self, sim_folder, sim_number, param_set):
        """
        Generates an RML file for a given simulation setup.

        Args:
            sim_folder (str): The folder where the RML file should be saved.
            sim_number (int): The simulation number within the current round.
            param_set (dict): The parameter set for the current simulation.

        Returns:
            str: The path to the generated RML file.
        """
        rml_path = os.path.join(sim_folder, f"{sim_number}_{self.simulation_name}.rml")
        for param, value in param_set.items():
            self.sp._write_value_to_param(param, value)
        if self.overwrite_rml or not os.path.exists(rml_path):
            self.rml.write(rml_path)
        self.sim_list_path.append(rml_path)
        return rml_path

    def _create_simulation_recap_files(self):
        """Creates recap CSV files summarizing the simulations for each round."""
        for sim_folder in set(os.path.dirname(path) for path in self.sim_list_path):
            with open(os.path.join(sim_folder, 'looper.csv'), 'w') as f:
                header = 'n\t' + '\t'.join(par.get_full_path().lstrip("lab.beamline.") for par in self.sp.param_to_simulate) + '\n'
                f.write(header)
                for ind, par in enumerate(self.sp.simulations_param_list):
                    line = f'{ind}\t' + '\t'.join(str(value) for value in par) + '\n'
                    f.write(line)


    def compose_exports_list(self, exports_dict_list, verbose:bool=True):
        """
        Generates a list of exports based on configurations and prints them if verbose.

        This function iterates over the export configurations provided to the class and
        compiles a list of tuples specifying the object elements and the associated files
        to export. It supports exporting single files or lists of files for each object element.

        Args:
            exports_dict_list (list): A list of dictionaries specifying the exports configuration.
            verbose (bool, optional): If True, prints the list of exports. Defaults to True.
        
        Raises:
            ValueError: If an export configuration is neither a string nor a list of strings.
        """
        self.exports_list = []
        for export_config in self.exports:
            for obj_element, file_names in export_config.items():
                self._append_exports(obj_element, file_names)

        if verbose:
            self._print_exports()

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


    def check_simulations(self, verbose:bool=True, force:bool=False):
        """
        Checks for simulations that have not been completed or are missing exports.

        This function iterates through the list of simulations, checking if the expected
        export files exist. If files are missing for a simulation, it's considered missing.

        Args:
            verbose (bool, optional): If True, prints the number of simulations still to do.
            force (bool, optional): If True, considers all simulations as missing regardless of existing files.

        Returns:
            dict: A dictionary mapping from simulation index to the simulation object for all missing simulations.
        """
        if force:
            return {k: v for k, v in enumerate(self.rml_list())}

        missing_simulations = self._identify_missing_simulations()

        if verbose:
            self._print_missing_simulations_count(missing_simulations)

        return missing_simulations

    def _identify_missing_simulations(self):
        """
        Identifies simulations that are missing based on their export files.

        Iterates through each simulation, checking if all specified export files exist.

        Returns:
            dict: A dictionary of missing simulations indexed by their enumeration index.
        """
        missing_simulations = {}
        for ind, simulation in enumerate(self.rml_list()):
            if self._is_simulation_missing(ind):
                missing_simulations[ind] = simulation
        return missing_simulations

    def _is_simulation_missing(self, simulation_index):
        """
        Checks if a simulation is missing based on the existence of its export files.

        Args:
            simulation_index (int): The index of the simulation in the simulation list.

        Returns:
            bool: True if the simulation is missing any export files, False otherwise.
        """
        folder = os.path.dirname(self.sim_list_path[simulation_index])
        sim_number = os.path.basename(self.sim_list_path[simulation_index]).split("_")[0]

        for export_config in self._exports_list:  # Corrected from exports_list to _exports_list
            if not os.path.exists(os.path.join(folder, f"{sim_number}_{export_config[0]}-{export_config[1]}.csv")):
                return True  # Missing at least one export file
        return False

    def _print_missing_simulations_count(self, missing_simulations):
        """
        Prints the count of missing simulations.

        Args:
            missing_simulations (dict): Dictionary of missing simulations.
        """
        print(f"I still have {len(missing_simulations)} simulations to do!")

    def run(self, recipe=None, multiprocessing=True, force=False, overwrite_rml=True):
        """
        Initiates the simulation process based on defined parameters and exports.

        Args:
            recipe (SimulationRecipe, optional): Recipe to use for setting up the simulation.
            multiprocessing (bool or int, optional): Specifies if simulations should run in parallel
                                                    and the number of processes to use.
            force (bool, optional): Forces re-execution of simulations even if they already have been completed.
            overwrite_rml (bool, optional): Overwrites existing RML files if set to True.

        Returns:
            bool: True if simulations are successfully started, False otherwise.

        Raises:
            TypeError: If an unsupported recipe type is provided.
        """
        self.overwrite_rml = overwrite_rml
        self._setup_simulation_environment(recipe)
        missing_simulations = self.check_simulations(force=force)
        
        self._execute_missing_simulations(missing_simulations, multiprocessing)
        
        self._postprocess_simulations(missing_simulations)

        return True

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

    def _execute_missing_simulations(self, missing_simulations, multiprocessing):
        """
        Executes simulations that are identified as missing or incomplete.

        Args:
            missing_simulations (dict): A dictionary of missing simulations.
            multiprocessing (bool or int): Specifies if and how multiprocessing should be used.
        """
        if not missing_simulations:
            return

        filenames_hide_analyze, exports = self._prepare_simulation_execution(missing_simulations)

        with RunPool(multiprocessing) as pool:
            pool.map(run_rml_func, zip(filenames_hide_analyze, exports))

    def _prepare_simulation_execution(self, missing_simulations):
        """
        Prepares necessary data for executing missing simulations.

        Args:
            missing_simulations (dict): A dictionary of missing simulations.

        Returns:
            tuple: Two lists containing data for running simulations and their respective exports.
        """
        filenames_hide_analyze = []
        exports = []

        for ind, rml in missing_simulations.items():
            simulation_data = self._gather_simulation_data(ind, rml)
            filenames_hide_analyze.append(simulation_data)
            exports.append(self.generate_export_params(ind, self.sim_list_path[ind]))

        return filenames_hide_analyze, exports

    def _gather_simulation_data(self, ind, rml):
        """
        Gathers necessary data for a single simulation execution.

        Args:
            ind (int): Index of the simulation.
            rml (RMLFile): RML file associated with the simulation.

        Returns:
            list: Data needed for executing the simulation.
        """
        filename = os.path.basename(rml.filename)
        sim_index = int(filename.split("_")[0])
        return [rml.filename, self._hide, self._analyze, self.raypyng_analysis, self.ray_path]

    def _postprocess_simulations(self, missing_simulations):
        """
        Performs cleanup and postprocessing after simulations are executed.

        Args:
            missing_simulations (dict): A dictionary of missing simulations that were executed.
        """
        if missing_simulations and not self.analyze and self.raypyng_analysis:
            pp = PostProcess()
            pp.cleanup(self.sim_path, self.repeat, self.exports_list)


    def generate_export_params(self,simulation_index,rml):
        folder = os.path.dirname(rml)
        return [ (d[0], d[1], folder, str(simulation_index)+'_') for d in self._exports_list]
    
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


