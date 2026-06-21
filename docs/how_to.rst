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

An example of how to write a recipe that automatically exports a
file for each element present in the beamline:

.. code-block:: python

    from raypyng.recipes import SimulationRecipe


    class ExportEachElement(SimulationRecipe):
        """At one defined energy, export a file for each optical element."""

        def __init__(self, energy: float, /, nrays: int = None, sim_folder: str = None):
            """
            Args:
                energy (float): the energy to simulate, in eV
                nrays (int): number of rays for the source
                sim_folder (str, optional): the name of the simulation folder.
                    If None, the rml filename will be used. Defaults to None.
            """
            if not isinstance(energy, (int, float)):
                raise TypeError(
                    'The energy must be an int or float, while it is a', type(energy)
                )

            self.energy = energy
            self.nrays = nrays
            self.sim_folder = sim_folder

        def params(self, sim):
            params = []

            # find the source and scan it over the user-defined energy range
            found_source = False
            for oe in sim.rml.beamline.children():
                if hasattr(oe, "photonEnergy"):
                    self.source = oe
                    found_source = True
                    break
            if not found_source:
                raise AttributeError('I did not find the source')
            params.append({self.source.photonEnergy: self.energy})

            # set reflectivity to 100% on every element that supports it
            for oe in sim.rml.beamline.children():
                for par in oe:
                    try:
                        params.append({par.reflectivityType: 0})
                    except Exception:
                        pass

            # all done, return the resulting params
            return params

        def exports(self, sim):
            # export RawRaysOutgoing for every element in the beamline
            exports = []
            for oe in sim.rml.beamline.children():
                exports.append({oe: 'RawRaysOutgoing'})
            return exports

        def simulation_name(self, sim):
            if self.sim_folder is None:
                return 'ExportEachElement'
            return self.sim_folder


    if __name__ == "__main__":
        from raypyng import Simulate

        rml_file = 'rml_file.rml'
        sim = Simulate(rml_file, hide=True)

        sim.analyze = False

        myRecipe = ExportEachElement(energy=1000, nrays=10000, sim_folder='MyRecipeTest')

        sim.run(myRecipe, multiprocessing="auto", force=True)

How to work with Undulator File
================================

The `WaveHelper` class helps to inspect a WAVE simulation folder and 
provides a simple way to extract the absolute path of the simulation files
to feed to the `Undulator File`. In this example we use the `WAVE` folder provided in the example
folder at this `link <https://github.com/hz-b/raypyng/tree/main/examples>`_. Inside the folder there are 
WAVE simulation files for the first, third and fifth harmonic, and the Undulator is called `U49`

.. code:: python

    import numpy as np

    from raypyng.wave_helper import WaveHelper

    WH = WaveHelper(wave_folder_path='WAVE', harmonic=3, undulator='U49')

    WH.report_available_energies(verbose=True)

This produces the following output:

.. code-block:: text

    I found the following harmonics: dict_keys([1, 3, 5])
    the energy points for each harmonic are equally spaced
    Harmonic number 1, available energies:
    start 80
    stop 570
    step 10
    Harmonic number 3, available energies:
    start 240
    stop 1710
    step 30
    Harmonic number 5, available energies:
    start 400
    stop 2850
    step 50


We can now extract the file location for all the energies or a subset of the 
energies available for the first harmonic of the undulator:

.. code:: python

    energies = np.arange(80,570,10)
    energy_files = WH.convert_energies_to_file_list(1,energies)

`energy_files` contains the absolute path to the WAVE simulation file for each energy. 
This can be used to change the energy of an Undulator by calling the parameter `undulatorFile`.
