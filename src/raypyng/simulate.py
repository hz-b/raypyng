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
        """The files to export once the simulation is complete.

        For a list of possible files check self.possible_exports
        and self.possible_exports_without_analysis.
        It is expected a list of dictionaries, and for each dictionary 
        the key is the element to be exported and the values are 
        the files to be exported
        """        
        return self._exports

    @exports.setter
    def exports(self,value):
        if not isinstance(value, list):
            raise AssertionError ('The exports must be a list, while it is a '+str(type(value)), value)
        for d in value:
            if not isinstance(d,dict):
                raise AssertionError('The element of the list must be dictionaries, while I found a '+str(type(d)), d)
            for k in d.keys():
                if not isinstance(k,ObjectElement):
                    raise AssertionError('The keys of the dictionaries must be instance of ObjectElement, while ', k, 'is a ', str(type(k)))
                if isinstance(d[k], str):
                    if self.analyze:
                        possible_exports = self.possible_exports
                    else: 
                        possible_exports = self.possible_exports_without_analysis
                    if d[k] not in possible_exports:
                        raise AssertionError('It is not possible to export {}, check the spelling. The possible files to exports are {}'.format(d[k],possible_exports))
                elif isinstance(d[k], list):
                    for dd in d[k]:
                        if dd not in self.possible_exports and self._analyze==True:
                            raise AssertionError('It is not possible to export this file. The possible files to exports are ', self.possible_exports)
                        elif dd not in self.possible_exports_without_analysis and self._analyze==False:
                            raise AssertionError('It is not possible to export this file. The possible files to exports are ', self.possible_exports)

        self._exports = value
        self._exports_list = self.compose_exports_list(value, verbose=False)
        
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
        """This function creates the folder structure and the rml files to simulate.
        
        It requires the param to be set. Useful if one wants to create the simulation files 
        for a manual check before starting the simulations.
        """
        result = []
        self.sim_list_path = []
        self.sim_path = os.path.join(self.path, self.prefix+'_'+self.simulation_name)
        # check if simulation folder exists, otherwise create it
        if not os.path.exists(self.sim_path):
            os.makedirs(self.sim_path)
        self.save_parameters_to_file(self.sim_path)
        for r in range(0,self.repeat):
            sim_folder = os.path.join(self.sim_path,'round_'+str(r))
            if not os.path.exists(sim_folder):
                os.makedirs(sim_folder)
            for sim_n,param_set in enumerate(self.sp.params_list()):
                rml_path = os.path.join(sim_folder,str(sim_n)+'_'+self.simulation_name+'.rml')
                for param,value in param_set.items():
                    self.sp._write_value_to_param(param,value)
                if self.overwrite_rml or os.path.exists(rml_path)==False:
                    self.rml.write(rml_path)
                self.sim_list_path.append(rml_path)
                # is this gonna create problems if I have millions of simulations?
                result.append(RMLFile(rml_path))

            # create csv file with simulations recap
            with open(os.path.join(sim_folder,'looper.csv'), 'w') as f:
                header = 'n '
                for par in self.sp.param_to_simulate:
                    #header = header + '\t'+str(par.id)#get_full_path().lstrip("lab.beamline."))
                    header = header + '\t'+str(par.get_full_path().lstrip("lab.beamline."))
                header += '\n'
                f.write(header)
                for ind,par in enumerate(self.sp.simulations_param_list):
                    line = ''
                    line += str(ind)+'\t'
                    for value in par:
                        line += str(value)+'\t'
                    f.write(line+'\n')  
        return result

    def compose_exports_list(self, exports_dict_list,/,verbose:bool=True):
        self.exports_list=[]
        for i, d in enumerate(self.exports):
                for obj in d.keys():
                    if isinstance(d[obj], str):
                        self.exports_list.append((obj.attributes().original()['name'], d[obj]))
                    elif isinstance(d[obj], list):
                        for l in d[obj]:
                            self.exports_list.append((obj.attributes().original()['name'], l))
                    else: 
                        raise ValueError('The exported param can be only str or list of str.')
        if verbose:
            print('The following will be exported:')
            for d in self.exports_list:
                print(d[0], d[1])

    def check_simulations(self,/,verbose:bool=True, force:bool=False):
        if force: return {k:v for k,v in enumerate(self.rml_list())}
        missing_simulations={}
        for ind,simulation in enumerate(self.rml_list()):
            folder = os.path.dirname(self.sim_list_path[ind])
            filename = os.path.basename(self.sim_list_path[ind])
            sim_number = filename.split("_")[0]
            for d in self.exports_list:
                export = sim_number+'_'+d[0]+'-'+d[1]+'.csv'
                csv = os.path.join(folder,export)
                if not os.path.exists(csv):
                    missing_simulations[ind]=simulation
                    break
        if verbose:
            print('I still have ', len(missing_simulations), 'simulations to do!')
            #print('missing_simulations',missing_simulations)
        return missing_simulations

    def run(self,recipe=None,/,multiprocessing=True, force=False, overwrite_rml=True):
        """This method starts the simulations. params and exports need to be defined.

        Args:
            recipe (SimulationRecipe, optional): If using a recipee pass it as a parameter. Defaults to None.
            multiprocessing (boolint, optional): If True all the cpus are used. If an integer n is provided, n cpus are used. Defaults to True.
            force (bool, optional): If True all the simlations are performed, even if the export files already exist. If False only the simlations for which are missing some exports are performed. Defaults to False.
            overwrite_rml (bool): if exists, overwrite the rml files, otherwise don't.   Defaults to True

        """  
        self.overwrite_rml = overwrite_rml           
        if recipe is not None:
            if isinstance(recipe,SimulationRecipe):
                self.params = recipe.params(self)
                self.exports = recipe.exports(self)
                self.simulation_name = recipe.simulation_name(self)
            else:
                raise TypeError("Unsupported type of the recipe!")

        filenames_hide_analyze = []
        exports = []
        missing_simulations= self.check_simulations(force=force).items()
        for ind,rml in missing_simulations:
            filename = os.path.basename(rml.filename)
            filenames_hide_analyze.append([rml.filename, self._hide, self._analyze, self.raypyng_analysis, self.ray_path])
            sim_index = int(filename[:filename.index("_")])
            exports.append(self.generate_export_params(sim_index,self.sim_list_path[ind]))
            rml.write()
        with RunPool(multiprocessing) as pool:
            pool.map(run_rml_func,zip(filenames_hide_analyze,exports))
        if len(missing_simulations) != 0 and self.analyze==False and self.raypyng_analysis==True:
            pp = PostProcess()
            pp.cleanup(self.sim_path, self.repeat, self.exports_list)
        return True

    def generate_export_params(self,simulation_index,rml):
        folder = os.path.dirname(rml)
        return [ (d[0], d[1], folder, str(simulation_index)+'_') for d in self.exports_list]
    
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
         
def run_rml_func(_tuple):
    filenames_hide_analyze,exports = _tuple
    rml_filename     = filenames_hide_analyze[0]
    hide             = filenames_hide_analyze[1]
    analyze          = filenames_hide_analyze[2]
    raypyng_analysis = filenames_hide_analyze[3]
    ray_path         = filenames_hide_analyze[4]
    runner = RayUIRunner(ray_path=ray_path,hide=hide)
    api    = RayUIAPI(runner)
    pp     = PostProcess()
    runner.run()
    api.load(rml_filename)
    api.trace(analyze=analyze)
    api.save(rml_filename)
    #print("DEBUG:: exports", exports)
    for e in exports:
        api.export(*e)
        if analyze==False and raypyng_analysis == True:
            pp.postprocess_RawRays(e[0], e[1], e[2], e[3], rml_filename)
    #time.sleep(0.1) # testing file creation issue
    try: 
        api.quit()
    except Exception as e:
        print("WARNING! Got exception while quitting ray, the error was:",e)
        pass
    #time.sleep(1) # testing file creation issue
    runner.kill()
    return None
