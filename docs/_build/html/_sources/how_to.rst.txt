How To Guides
**************

To simplify the scripting, especially when repetitive, 
there is the possibility to write recipe for raypyng, to 
perform simulations, and automatize some tasks.

Write your own Recipe
======================

Recipe Template
------------------

This the template to use to write a recipe. 
At the beginning of the file import 
:code:`SimulationRecipe` from :code:`raypyng` 
and define a the Simulation class as an empty dummy.
This will ensure that you have access to all the methods of the 
:code:`Simulation` class.

A recipe should containe at least the :code:`__init__()` 
method and three more methods: :code:`params()`, 
and :code:`simulation_name()`, 
and they must have as an argument the simulate class.  

Compose the simulation parameters in the :code:`params` method:
The simulation parameter must return a list of dictionaries, 
where the keys of the dictionaries are parameters of on abject 
present in the beamline, instances of :code:`ParamElement` class. 
The items of the dictionary must be the values that the parameter should 
assume for the simulations. 

Compose the simulation parameters in the :code:`params()` method:
The :code:`params()` method must return a list of dictionaries.
The keys of the dictionaries are parameters of on abject 
present in the beamline, instances of :code:`ParamElement` class. 
The items of the dictionary must be the values that the parameter should 
assume for the simulations. 

Compose the export parameters in the :code:`exports()` method:
The The :code:`exports()` method must return a list of dictionaries, 
method must return a list of dictionaries.
The keys of the dictionaries are parameters of on abject 
present in the beamline, instances of :code:`ParamElement` class. 
The items of the dictionary is the name of the file that you want to export 
(print the output of :code:`Simulation.possible_exports` and 
:code:`possible_exports_without_analysis`.

Define the name to give to the simulation folder 
in :code:`simulation_name()`

.. code-block:: python

    from raypyng.recipes import SimulationRecipe

    class Simulate: pass

    class MyRecipe(SimulationRecipe):
        def __init__(self):
            pass
        
        def params(self,sim:Simulate):

            params = []

            return params

        def exports(self,sim:Simulate):
            
            exports = []

            return exports

        def simulation_name(self,sim:Simulate):

            self.sim_folder = ...

            return self.sim_folder

How To Write a Recipe
---------------------

An example of how to write a recipe that exports 
file for each element present in the beamline automatically.  
 
 .. code-block:: python

    class ExportEachElement(SimulationRecipe):
    """At one defined energy export a file for each 
    optical elements
    """
    def __init__(self, energy:float,/,nrays:int=None,sim_folder:str=None):
        """
        Args:
            energy_range (np.array, list): the energies to simulate in eV
            nrays (int): number of rays for the source
            sim_folder (str, optional): the name of the simulation folder. If None, the rml filename will be used. Defaults to None.
        
        """        
    
        if not isinstance(energy, (int,float)):
           raise TypeError('The energy must be an a int or float, while it is a', type(energy))

        self.energy = energy
        self.nrays  = nrays
        self.sim_folder = sim_folder
    
    def params(self,sim:Simulate):
        params = []

        # find source and add to param with defined user energy range
        found_source = False
        for oe in sim.rml.beamline.children():
            if hasattr(oe,"photonEnergy"):
            self.source = oe
                found_source = True
                break        
        if found_source!=True:
            raise AttributeError('I did not find the source')        
        params.append({self.source.photonEnergy:self.energy})
        
        # set reflectivity to 100%
        for oe in sim.rml.beamline.children():
                for par in oe:
                    try:
                        params.append({par.reflectivityType:0})
                    except:
                        pass

        # all done, return resulting params
        return params

    def exports(self,sim:Simulate):
        # find all the elements in the beamline
        oe_list=[]
        for oe in sim.rml.beamline.children():
            oe_list.append(oe)
        # compose the export list of dictionaries
        exports = []
        for oe in oe_list:
            exports.append({oe:'RawRaysOutgoing'})
        return exports

    def simulation_name(self,sim:Simulate):
        if self.sim_folder is None:
            return 'ExportEachElement'
        else: 
            return self.sim_folder
    if __name__ == "__main__":
        from raypyng import Simulate
        import numpy as np
        import os

        rml_file = ('rml_file.rml')
        sim      = Simulate(rml_file, hide=True)


        sim.analyze = False

        myRecipe = ExportEachElement(energy=1000,nrays=10000,sim_folder='MyRecipeTest')

        # test resolving power simulations
        sim.run(myRecipe, multiprocessing=5, force=True)


