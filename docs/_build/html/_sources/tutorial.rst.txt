Tutorial
********

Manipulate an RML file 
========================
Using the :code:`RMLFile` class it is possible to manupulate an beamline file produced by RAY-UI.

.. code:: python

  In [8]: from raypyng.rml import RMLFile
   ...: rml = RMLFile('rml/elisa.rml')
   ...: rml
  Out[8]: RMLFile('rml/elisa.rml',template='rml/elisa.rml')

The filename can be accesed with the filename :code:`attribute`

.. code:: python

  In [9]: rml.filename
  Out[9]: 'rml/elisa.rml'

and the beamline is available under:

.. code:: python
  
  In [10]: elisa = rml.beamline
  In [11]: elisa
  Out[11]: XmlElement(name = beamline, attributes = {}, cdata = )

It is possible to list all the element present in the beamlne using 
the :code:`children()` method

.. code:: python

  In [14]: for i, oe in enumerate(elisa.children()):
    ...:     print('OE ',i, ':', oe.resolvable_name())
    ...: 
  OE  0 : Dipole
  OE  1 : M1
  OE  2 : PremirrorM2
  OE  3 : PG
  OE  4 : M3
  OE  5 : ExitSlit
  OE  6 : KB1
  OE  7 : KB2
  OE  8 : DetectorAtFocus

In a similar way one can print all the available paramters of a certain element.
For instance, to print all the parameters of the Dipole:

.. code:: python

  In [15]: # print all the parameters of the Dipole
    ...: for param in elisa.Dipole.children():
    ...:     print('Dipole param: ', param.id)
    ...: 
  Dipole param:  numberRays
  Dipole param:  sourceWidth
  Dipole param:  sourceHeight
  Dipole param:  verEbeamDiv
  Dipole param:  horDiv
  Dipole param:  electronEnergy
  Dipole param:  electronEnergyOrientation
  Dipole param:  bendingRadius
  Dipole param:  alignmentError
  Dipole param:  translationXerror
  Dipole param:  translationYerror
  Dipole param:  rotationXerror
  Dipole param:  rotationYerror
  Dipole param:  energyDistributionType
  Dipole param:  photonEnergyDistributionFile
  Dipole param:  photonEnergy
  Dipole param:  energySpreadType
  Dipole param:  energySpreadUnit
  Dipole param:  energySpread
  Dipole param:  sourcePulseType
  Dipole param:  sourcePulseLength
  Dipole param:  photonFlux
  Dipole param:  worldPosition
  Dipole param:  worldXdirection
  Dipole param:  worldYdirection
  Dipole param:  worldZdirection

Any parameter can be modified in this way:

.. code:: python

  In [17]: elisa.Dipole.photonEnergy.cdata
  Out[17]: '1000'

  In [18]: elisa.Dipole.photonEnergy.cdata = str(2000)

  In [19]: elisa.Dipole.photonEnergy.cdata
  Out[19]: 2000

Once you are done with the modifications, you can save the rml file using the :code:`write()` method

.. code:: python

  rml.write('rml/new_elisa.rml')


RAY-UI API 
===============
Using the :code:`RayUIRunner` and the :code:`RayUIAPI` classes it is possible 
to interact with RAY-UI directly from python.

.. code:: python

  In [1]: import os
   ...: import time
   ...: from raypyng.runner import RayUIRunner, RayUIAPI
   ...: 
   ...: r = RayUIRunner(ray_path=None, hide=True)
   ...: a = RayUIAPI(r)

  In [2]: r.run()
  Out[2]: <raypyng.runner.RayUIRunner at 0x7effd8f53b50>

Once an instance of RAY-UI is running, we can confirm that it is running
and we can ask the :code:`pid`

.. code:: python

  In [3]: r.isrunning
  Out[3]: True

  In [4]: r.pid
  Out[4]: 20742

It is possible to load an rml file and trace it

.. code:: python

  In [5]: a.load('rml/elisa.rml')
   ...: 
  Out[5]: True

  In [6]: a.trace(analyze=True)
    ...: 
  Out[6]: True
 
Export the files for the elements of interest:

.. code:: python

  In [7]: a.export("Dipole,DetectorAtFocus", "RawRaysOutgoing", '/home/simone/Documents/RAYPYNG/raypyng/examples', 'test_export')
   ...: 
  Out[7]: True

Save the rml file used for the simulation (this is useful because RAY-UI 
when it traces the beamline it updates the RML files with the latest parameters: for
instance if you change the photon energy, it will update the source flux)

.. code:: python 

  In [8]: a.save('rml/new_elisa')
  Out[8]: True

And finally we can quit the RAY-UI instance that we opened:

.. code:: python

  In [9]: a.quit()

Simulations 
===============

Perform Simulations
--------------------
raypyng is not able to create a beamline from scratch. To do so, use RAY-UI, 
create a beamline, and save it. What you save is :code:`.rml` file, which you have to 
pass as an argument to the :code:`Simulate` class. In the following example, we 
use the file for a beamline called `elisa`, and the file is saved in :code:`rml/elisa.rml`. 
The :code:`hide` parameter can be set to true only if `xvfb` is installed.

.. code-block:: python

    from raypyng import Simulate
    rml_file = 'rml/elisa.rml'

    sim = Simulate(rml_file, hide=True)
    elisa = sim.rml.beamline

The elements of the beamline are now available as python objects, as well as 
their properties. If working in ipython, tab autocompletion is available. 
For instance to access the source, a dipole in this case: 

.. code-block:: python

    # this is the dipole object
    elisa.Dipole 
    # to acess its parameter, for instance, the photonFlux
    elisa.Dipole.photonFlux
    # to access the value 
    elisa.Dipole.photonFlux.cdata
    # to modify the value
    elisa.Dipole.photonFlux.cdata = 10


To perform a simulation, any number of parameters can be varied. 
For instance, one can vary the photon energy of the source, and set a 
a certain aperture of the exit slits:

.. code-block:: python
    
    # define the values of the parameters to scan 
    energy    = np.arange(200, 7201,250)
    SlitSize  = np.array([0.1])

    # define a list of dictionaries with the parameters to scan
    params = [  
                {elisa.Dipole.photonEnergy:energy}, 
                {elisa.ExitSlit.totalHeight:SlitSize}
            ]

    #and then plug them into the Simulation class
    sim.params=params

It is also possible to define coupled parameters. If for instance, one wants 
to increase the number of rays with the photon energy

.. code-block:: python
    
    # define the values of the parameters to scan 
    energy    = np.arange(200, 7201,250)
    nrays     = energy*100
    SlitSize  = np.array([0.1])

    # define a list of dictionaries with the parameters to scan
    params = [  
                {elisa.Dipole.photonEnergy:energy, elisa.Dipole.numberRays:nrays}, 
                {elisa.ExitSlit.totalHeight:SlitSize}
            ]

    #and then plug them into the Simulation class
    sim.params=params

The simulations files and the results will be saved in a folder called `RAYPy_simulation_` 
and a name of your choice, that can be set. This folder will be saved, by default, 
in the folder where the program is executed, but it can eventually be modified

.. code-block:: python

    sim.simulation_folder = '/home/raypy/Documents/simulations'
    sim.simulation_name = 'test'

This will create a simulation folder with the following path and name

.. code-block:: python

    /home/raypy/Documents/simulations/RAYPy_simulation_test

Sometimes, instead of using millions of rays, it is more convenient to repeat the simulations and average the results
We can set which parameters of which optical elements can be exported. The number of rounds of simulations can be set like this:

.. code-block:: python

    # repeat the simulations as many times as needed
    sim.repeat = 1

One can decide whether want RAY-UI or raypyng to do a preliminary analysis of the results. 
To let RAY-UI analyze the results, one has to set:

.. code-block:: python

    sim.analyze = True # let RAY-UI analyze the results

In this case, the following files are available to export:

.. code-block:: python

    print(sim.possible_exports)
    > ['AnglePhiDistribution',
    > 'AnglePsiDistribution',
    > 'BeamPropertiesPlotSnapshot',
    > 'EnergyDistribution',
    > 'FootprintAbsorbedRays',
    > 'FootprintAllRays',
    > 'FootprintOutgoingRays',
    > 'FootprintPlotSnapshot',
    > 'FootprintWastedRays',
    > 'IntensityPlotSnapshot',
    > 'IntensityX',
    > 'IntensityYZ',
    > 'PathlengthDistribution',
    > 'RawRaysBeam',
    > 'RawRaysIncoming',
    > 'RawRaysOutgoing',
    > 'ScalarBeamProperties',
    > 'ScalarElementProperties']

To let raypyng analyze the results set:

.. code-block:: python

    sim.analyze = False # don't let RAY-UI analyze the results
    sim.raypyng_analysis=True # let raypyng analyze the results

In this case, only these exports are possible

.. code-block:: python

    print(sim.possible_exports_without_analysis)
    > ['RawRaysIncoming', 'RawRaysOutgoing']

The exports are available for each optical element in the beamline, ImagePlanes included, and can be set like this:

.. code-block:: python

    ## This must be a list of dictionaries
    sim.exports  =  [{elisa.Dipole:['ScalarElementProperties']},
                    {elisa.DetectorAtFocus:['ScalarBeamProperties']}
                    ]

Finally, the simulations can be run using

.. code-block:: python

    sim.run(multiprocessing=5, force=True)

where the `multiprocessing` parameter can be an integer greater or equal to 1, corresponding to the number of parallel instances of RAY-UI to be used. Generally speaking, the number of instances of RAY-UI must be lower or equal than the number of available cores. If the simulation uses many rays, monitor the RAM usage of your computer. If the computation uses all the possible RAM of the computer the program may get blocked or not execute correctly.

Note on multiprocessing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The speed increase due to opening many RAY-UI instances is effective only when RAY-UI is not performing the analysis of the results.

.. code-block:: python

    sim.analyze = False # don't let RAY-UI analyze the results


There is little/no difference having RayPyNG analyzing the results
.. code-block:: python

    sim.raypyng_analysis=True # let raypyng analyze the results


Simulation Output
------------------
Expect this folders and subfolders to be created:

::

    RAYPy_simulation_mySimulation
    ├── round_0          
    │   ├── 0_*.rml
    │   └── 0_*.csv
    │   └── 0_*.dat (only if raypyng analyzes the results)
    │   └── ...
    │   └── looper.py
    ...
    ├── round_n          
    │   ├── 0_*.rml
    │   └── 0_*.csv
    │   └── 0_*.dat (only if raypyng analyzes the results)
    │   └── ...
    │   └── looper.py
    ├── input_param_1.dat
    ...
    ├── input_param_k.dat
    ├── output_simulation.dat (only if raypyng analyzes the results)



Analysis performed by RAY-UI 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**This is discouraged, as this approach is very slow.**

If you decided to let RAY-UI do the analysis, you should expect the following files to be 
saved in your simulation folder:

- one file for each parameter you set with the values that you passed to the program. 
  If for instance, you input the Dipole numberRays, you will find a file called 
  `input_param_Dipole_numberRays.dat`
- one folder called `round_n` for each repetition of the simulations. 
  For instance, if you set :code:`sim.repeat=2` you will have two folders `round_0` and `round_1`
- inside each `round_n` folder you will find the beamline files modified 
  with the parameters you set in `sim.params`, these are the `.rml` files, 
  that can be opened by RAY-UI.
- inside each `round_n` folder you will find your exported files, one for 
  each simulation. If for instance, you exported the `ScalarElementProperties` of the Dipole, 
  you will have a list of files `0_Dipole-ScalarElementProperties.csv`
- `looper.csv` each simulation and its parameters.

Analysis performed by raypyng
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you decided to let raypyng do the analysis, you should expect the following files to 
be saved in your simulation folder:

- one file for each parameter you set with the values that you passed to the program. 
  If for instance, you input the Dipole numberRays, you will find a file called 
  `input_param_Dipole_numberRays.dat`
- one folder called `round_n` for each repetition of the simulations. 
  For instance, if you set :code:`sim.repeat=2` you will have two folders `round_0` and `round_1`
- inside each `round_n` folder you will find the beamline files modified with the parameters 
  you set in `sim.params`, these are the `.rml` files, that can be opened by RAY-UI.
- inside each `round_n` folder you will find your exported files, one for each simulation. 
  If for instance, you exported the `RawRaysOutgoing` of the Dipole, you will 
  have a list of files `0_Dipole-RawRaysOutgoing.csv`
- for each `RawRaysOutgoing` file, raypyng calculates some properties, 
  and saves a corresponding file, for instance `0_Dipole_analyzed_rays.dat`. 
- In the simulation folder, all the for each exported element 
  is brought together (and averaged in case of more rounds of simulations ) 
  in one single file. For the dipole, the file is called `Dipole_RawRaysOutgoing.csv`. 
  It contains the following columns, beside the input parameters:

    - Simulation Number  
    - SourcePhotonFlux  
    - NumberRaysSurvived  
    - PercentageRaysSurvived  
    - PhotonEnergy  
    - Bandwidth  
    - HorizontalFocusFWHM  
    - VerticalFocusFWHM  
    - PhotonFlux  
    - EnergyPerMilPerBw  
    - FluxPerMilPerBwPerc  
    - FluxPerMilPerBwAbs  
    - AXUVCurrentAmp  
    - GaAsPCurrentAmp  

Recipes
========
raypyng provides some recipes to make simulations, 
that simplify the syntax in the script. 
Two recipes are provided, one to make `Resolving Power
<https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_RP.py>`_ simulations, 
one to make `Flux
<https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_Flux.py>`_
simulations. 


List of available examples 
===========================
Examples are available at the following link: Examples are available at the following link: `raypyng examples <https://github.com/hz-b/raypyng/blob/main/examples>`_.


  
  