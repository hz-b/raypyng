
from RayPyNG.rml import RMLFile
import itertools
import os 
import numpy as np

class Simulate():
    """class to simulate 
    """
    def __init__(self, rml=None) -> None:
        if rml is not None:
            self.rml = rml
        else:
            raise Exception("rml file must be defined")

    def set_param(self, param:list=None):
        if param is not None:
            self.param = param
        else:
            raise Exception("Params must be set")
        self._check_param()
    
    def _check_param(self):
        # self.param must be a list
        if not isinstance(self.param, list) == True:
            raise AssertionError('params must be a list')
        # every element in the list must be a dictionary
        for d in self.param:
            if not isinstance(d, dict):
                raise AssertionError('The elements of params must be dictionaries')
        # the items permitted types are:
        # int,float,str,np.array
        # a list of the types above
        # the output of range, that I still did not understand what it is
        # in any case at the end we want to have either
        # a list or a numpy array
        for d in self.param:
            for k in d.keys():
                if isinstance(d[k], (list)):
                    pass
                elif isinstance(d[k], (float, int, str)):
                    d[k] = [d[k]]
                else: # this works with range output, but I would like to capture the type..
                    try:
                        d[k] = list(d[k])
                    except TypeError:
                        raise Exception('The only permitted type are: int, float, str, list, range, np.array, check',d[k]) 
    
    def _extract_param(self, verbose:bool=False):
        self.ind_param_values = []
        self.ind_par = []
        self.dep_param_dependency = {}
        self.dep_value_dependency = []
        self.dep_par = []
        # loop over the list of dictionaries
        for par in self.param:
            keys_par = list(par.keys())
            # if there is more than one key, we have an indipendent parameter
            # and one or more dependent parameters
            # the dependent param are keys, value and dependency are stored
            if len(keys_par) > 1:
                index_param  = 0
                for dep_param in keys_par:
                    if dep_param != keys_par[0]:
                        index_values = 0
                        self.dep_param_dependency[dep_param] = keys_par[0]
                        for dep_value in par[dep_param]:
                            if index_values == 0:
                                self.dep_value_dependency.append({par[keys_par[0]][index_values]:dep_value})
                            else:
                                self.dep_value_dependency[index_param][par[keys_par[0]][index_values]]=dep_value
                            index_values += 1
                        index_param += 1
            # here we deal with the indipendent parameters
            self.ind_param_values.append(par[keys_par[0]])
            self.ind_par.append(keys_par[0])
            self.dep_par = list(self.dep_param_dependency.keys())
        if verbose:
            print('###########################################')
            print('self.ind_param_values', self.ind_param_values)
            print('self.ind_par', self.ind_par)
            print('###########################################')
            print('self.dep_param_dependency', self.dep_param_dependency)
            print('self.dep_value_dependency',self.dep_value_dependency)
    
    def _calc_loop(self):
        self.param_to_simulate = self.ind_par + self.dep_par
        self.simulations_param_list = []
        # here we arrange the indipendent parameters in a grid
        self.loop = list(itertools.product(*self.ind_param_values))
        
        # work out where are the parameters on which the dependent parameters depends
        # make a copy of the dependency dictionary and replace the items with the index in the second step
        self.dep_param_dependency_index = []
        for ind,par in enumerate(self.dep_param_dependency.values()):
            index_par = self.ind_par.index(par)
            self.dep_param_dependency_index.append(index_par)

        # here we add the dependent parameters
        for count, loop in enumerate(self.loop):
            for ind,par in enumerate(self.dep_param_dependency.keys()):
                #print(par.id, loop[self.dep_param_dependency_index[ind]], self.dep_value_dependency[ind][loop[self.dep_param_dependency_index[ind]]] )
                to_add = (self.dep_value_dependency[ind][loop[self.dep_param_dependency_index[ind]]],)
                loop = loop + to_add
            self.simulations_param_list.append(loop)
        self.par = self.ind_par + self.dep_par
    
    def _check_if_enabled(self, param):
        return param.enabled=='T'
    
    def _enable_param(self, param):
        if not self._check_if_enabled(param):
            param.enabled = 'T'
        try:
            param.auto = 'T'
        except AttributeError:
            pass

    def _write_value_to_param(self, param, value):
        self._enable_param(param)
        if not isinstance(value,str):
            value = str(value)
            param.cdata = value

    def create_simulation_files(self, name:str,/, path:str=None, repeat:bool=1, prefix:str='RAYPy_Simulation'):
        if path is None:
            path = os.getcwd()
            for n in range (0,repeat):
                #print ('N', n)
                count = 0
                sim_folder = os.path.join(path, prefix+'_'+str(n))
                if not os.path.exists(sim_folder):
                    os.makedirs(sim_folder)              
                # write the rml files
                for sim_n,single_simulation in enumerate(self.simulations_param_list):
                    for ind, value in enumerate(single_simulation):
                        self._write_value_to_param(self.param_to_simulate[ind], value)
                    rml.write(os.path.join(sim_folder,str(sim_n)+'_'+name))
        # create csv file with simulations recap
        with open(os.path.join(sim_folder,'looper.csv'), 'w') as f:
            header = 'n '
            for par in self.param_to_simulate:
                header = header + '\t'+str(par.id)
            header += '\n'
            f.write(header)
            for ind,par in enumerate(self.simulations_param_list):
                line = ''
                line += str(ind)+'\t'
                for value in par:
                    line += str(value)+'\t'
                f.write(line+'\n')
            





rml = RMLFile('RayPyNG/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')
sim = Simulate(rml=rml)

params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml.beamline.M1.grazingIncAngle:np.array([1,2]), rml.beamline.M1.longRadius:[0,180], rml.beamline.Dipole.photonEnergy:[1000,2000]}, 
            # set a range of  values - in independed way
            {rml.beamline.M1.exitArmLengthMer:range(19400,19501, 100)},
            # set a value - in independed way
            {rml.beamline.M1.exitArmLengthSag:np.array([100])}
        ]


sim.set_param(params)
sim._extract_param(verbose=False)
sim._calc_loop()
sim.create_simulation_files('simulation_test')
        
        

        
