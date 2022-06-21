
from RayPyNG.rml import RMLFile
import itertools
import os

class Simulate():
    """class to simulate 
    """
    def __init__(self, rml=None) -> None:
        if rml is not None:
            self.rml = rml
        else:
            raise Exception("rml file must be defined")

    def set_param(self, param= None):
        if param is not None:
            self.param = param
        else:
            raise Exception("params must be set")
    
    def _extract_param(self, verbose=False):
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
            # If there is only one key we have an indipendent parameter
            elif len(keys_par) == 1:
                # check if we have a float, int, str, 
                # and convert it to list if necessary
                if isinstance(par[keys_par[0]], (float, int, str)):
                    par[keys_par[0]]=[par[keys_par[0]]]
                # if we have a list or output of range this will work
                # otherwise we raise an exception                
                else:
                    try:
                        par[keys_par[0]] = list(par[keys_par[0]])
                    except TypeError:
                        raise('The only permitted type are: int, float, str, list, range')
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
                        self.param_to_simulate[ind].cdata = str(value)
                    rml.write(os.path.join(sim_folder,str(sim_n)+'_'+name))
        # create csv file with simulations recap
        with open(os.path.join(sim_folder,'looper.csv'), 'w') as f:
            header = 'n '
            for par in self.param_to_simulate:
                header = header + '\t'+str(par.id)
            header += '\n'
            f.write(header)
            print(header)
            for ind,par in enumerate(self.simulations_param_list):
                print(ind, par)
                f.write(str(ind)+'\t'+str(par)+'\n')
            






rml = RMLFile('RayPyNG/rml2.xml',template='examples/rml/high_energy_branch_flux_1200.rml')
sim = Simulate(rml=rml)

params = [  
            # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml.beamline.M1.grazingIncAngle:[1,2], rml.beamline.M1.azimuthalAngle:[0,180], rml.beamline.Dipole.photonEnergy:[1000,2000]}, 
            # set a range of  values - in independed way
            {rml.beamline.M1.exitArmLengthMer:range(19400,19501, 100)},
            # set a value - in independed way
            {rml.beamline.M1.exitArmLengthSag:100}
        ]



sim.set_param(params)
sim._extract_param(verbose=False)
sim._calc_loop()
sim.create_simulation_files('simulation_test')
        
        

        
