Tutorial
********

Minimal example
===============
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

where the `multiprocessing` parameter can be set either to False or to an int, corresponding to the number of parallel instances of RAY-UI to be used. Generally speaking, the number of instances of RAY-UI must be lower than the number of cores available. If the simulation uses many rays, monitor the RAM usage of your computer. If the computation uses all the possible RAM of the computer the program may get blocked or not execute correctly.

Simulation Output
=================
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
------------------------------ 
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
-------------------------------
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
  and saves a corresponding file, for instance `0_Dipole_analyzed_rays.dat`. Each of these files contains the following information:

  - SourcePhotonFlux
  - NumberRaysSurvived     
  - PercentageRaysSurvived   
  - PhotonFlux        
  - Bandwidth        
  - HorizontalFocusFWHM     
  - VerticalFocusFWHM

- In the simulation folder, all the for each exported element 
  is united (and in case of more rounds of simulations averaged) 
  in one single file. For the dipole, the file is called `Dipole.dat`
- `looper.csv` each simulation and its parameters.

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
In the example folder, the following examples are available:

- `example_simulation_analyze.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_analyze.py>`_ simulate a beamline, 
  let Ray-UI do the analysis
- `example_simulation_noanalyze.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_noanalyze.py>`_ 
  simulate a beamline, 
  let raypyng do the analysis
- `example_eval_noanalyze_and_analyze.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_eval_noanalyze_and_analyze.py>`_
  plots the results 
  of the two previous simulations
- `example_simulation_Flux.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_Flux.py>`_
  simulations using the flux recipe,
  useful if you intend to simulate the flux of your beamline
- `example_simulation_RP.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_simulation_RP.py>`_
  simulations using the resolving power 
  (RP) recipe, useful if you intend to simulate the RP of your beamline. 
  The reflectivity of every optical element is switched to 100% and not 
  calculated using the substrate and coating(s) material(s). The 
  information about the Flux of the beamline is therefore not reliable.
- `example_beamwaist.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_beamwaist.py>`_
  raypyng can plot the beam waist of 
  the x-rays across your beamline. It performs simulations using the beam waist recipe, 
  and it exports the RawRaysOutgoing file from each optical element. It then uses a 
  simple geometrical x-ray tracer to propagate each ray until the next optical 
  element and plots the results (both top view and side view). This is still 
  experimental and it may fail.   

  