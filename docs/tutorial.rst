Tutorial
********

.. note::

   Every code block in this tutorial is written so that it can be copied and
   pasted directly into a Python script or interpreter. Program output, when
   shown, is given in a separate block and is not meant to be pasted back in.

Manipulate an RML file
========================
Using the :code:`RMLFile` class it is possible to manipulate a beamline file produced by RAY-UI.

.. code-block:: python

    from raypyng.rml import RMLFile

    rml = RMLFile('rml/dipole_beamline.rml')
    print(rml)

Output:

.. code-block:: text

    RMLFile('rml/dipole_beamline.rml', template='rml/dipole_beamline.rml')

The filename can be accessed with the :code:`filename` attribute:

.. code-block:: python

    print(rml.filename)

Output:

.. code-block:: text

    rml/dipole_beamline.rml

and the beamline is available under:

.. code-block:: python

    beamline = rml.beamline
    print(beamline)

Output:

.. code-block:: text

    XmlElement(name = beamline, attributes = {}, cdata = )

It is possible to list all the elements present in the beamline using
the :code:`children()` method:

.. code-block:: python

    for i, oe in enumerate(beamline.children()):
        print('OE ', i, ':', oe.resolvable_name())

Output:

.. code-block:: text

    OE  0 : Dipole
    OE  1 : M1
    OE  2 : PremirrorM2
    OE  3 : PG
    OE  4 : M3
    OE  5 : ExitSlit
    OE  6 : KB1
    OE  7 : KB2
    OE  8 : DetectorAtFocus

In a similar way one can print all the available parameters of a certain element.
For instance, to print all the parameters of the Dipole:

.. code-block:: python

    # print all the parameters of the Dipole
    for param in beamline.Dipole.children():
        print('Dipole param: ', param.id)

Output:

.. code-block:: text

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

Any parameter can be read and modified through its :code:`cdata` attribute:

.. code-block:: python

    # read the current value
    print(beamline.Dipole.photonEnergy.cdata)

    # modify the value
    beamline.Dipole.photonEnergy.cdata = str(2000)

    # read it back
    print(beamline.Dipole.photonEnergy.cdata)

Output:

.. code-block:: text

    1000
    2000

Once you are done with the modifications, you can save the rml file using the :code:`write()` method:

.. code-block:: python

    rml.write('rml/new_dipole_beamline.rml')


RAY-UI API
===============
Using the :code:`RayUIRunner` and the :code:`RayUIAPI` classes it is possible
to interact with RAY-UI directly from python.

.. code-block:: python

    from raypyng.runner import RayUIRunner, RayUIAPI

    r = RayUIRunner(ray_path=None, hide=True)
    a = RayUIAPI(r)

    # start the RAY-UI process
    r.run()

Once an instance of RAY-UI is running, we can confirm that it is running
and we can ask for its :code:`pid`:

.. code-block:: python

    print(r.isrunning)
    print(r.pid)

Output:

.. code-block:: text

    True
    20742

It is possible to load an rml file and trace it:

.. code-block:: python

    a.load('rml/dipole_beamline.rml')
    a.trace(analyze=True)

Export the files for the elements of interest:

.. code-block:: python

    a.export(
        "Dipole,DetectorAtFocus",
        "RawRaysOutgoing",
        '/home/simone/Documents/RAYPYNG/raypyng/examples',
        'test_export',
    )

Save the rml file used for the simulation (this is useful because when RAY-UI
traces the beamline it updates the RML file with the latest parameters: for
instance if you change the photon energy, it will update the source flux):

.. code-block:: python

    a.save('rml/new_dipole_beamline')

And finally we can quit the RAY-UI instance that we opened:

.. code-block:: python

    a.quit()

Simulations 
===============

Perform Simulations
--------------------
raypyng is not able to create a beamline from scratch. To do so, use RAY-UI, 
create a beamline, and save it. What you save is :code:`.rml` file, which you have to 
pass as an argument to the :code:`Simulate` class. In the following example, we
use a dipole beamline, saved in :code:`rml/dipole_beamline.rml`.
On Linux, the :code:`hide` parameter can be set to :code:`True` only if `xvfb`
is installed. On macOS xvfb is not needed and :code:`hide` is simply ignored, so
it is safe to leave it set to :code:`True`.

.. code-block:: python

    from raypyng import Simulate
    rml_file = 'rml/dipole_beamline.rml'

    sim = Simulate(rml_file, hide=True)
    beamline = sim.rml.beamline

The elements of the beamline are now available as python objects, as well as 
their properties. If working in ipython, tab autocompletion is available. 
For instance to access the source, a dipole in this case: 

.. code-block:: python

    # this is the dipole object
    beamline.Dipole 
    # to acess its parameter, for instance, the photonFlux
    beamline.Dipole.photonFlux
    # to access the value 
    beamline.Dipole.photonFlux.cdata
    # to modify the value
    beamline.Dipole.photonFlux.cdata = 10


Independent and dependent parameters
-------------------------------------

To perform a simulation, any number of parameters can be varied. The values to
scan are passed to :code:`sim.params` as a **list of dictionaries**. Each
dictionary describes one *block* of parameters, and the way parameters combine
depends on whether they are **independent** or **dependent**.

The rules, in the abstract:

- **Each dictionary in the list contributes exactly one independent
  parameter: its first key.** Independent parameters are scanned against each
  other as a full grid (the Cartesian product of their value lists).
- **Any additional key in the same dictionary is a dependent parameter.** A
  dependent parameter is *coupled* to the independent parameter of its
  dictionary: it does not add a new dimension to the grid, it simply advances
  together with its independent partner. Its value list must therefore have the
  **same length** as the independent one.
- **The total number of simulations is the product of the lengths of the
  independent parameters only.** Dependent parameters never increase this count.

Independent parameters (a grid)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the simplest case every dictionary has a single key, so every parameter is
independent. For instance, to scan the photon energy of the source against the
aperture of the exit slit:

.. code-block:: python

    import numpy as np

    # define the values of the parameters to scan
    energy   = np.array([200, 400])
    SlitSize = np.array([0.1, 0.5, 0.9])

    # one key per dictionary -> both parameters are independent
    params = [
        {beamline.Dipole.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: SlitSize},
    ]

    # plug them into the Simulate class
    sim.params = params

This produces ``2 x 3 = 6`` simulations, one for every combination of the two
parameters. The **last** parameter in the list varies fastest:

.. list-table:: 6 simulations: full grid of two independent parameters
   :header-rows: 1
   :widths: 12 30 30

   * - sim #
     - ``photonEnergy`` (independent)
     - ``totalHeight`` (independent)
   * - 0
     - 200
     - 0.1
   * - 1
     - 200
     - 0.5
   * - 2
     - 200
     - 0.9
   * - 3
     - 400
     - 0.1
   * - 4
     - 400
     - 0.5
   * - 5
     - 400
     - 0.9

Dependent (coupled) parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to define coupled parameters. For instance, one may want to
increase the number of rays together with the photon energy, so that every
energy point is simulated with its own ray count. To couple two parameters,
place them in the **same dictionary**: the first key is the independent
parameter, the following keys are dependent on it and must have value lists of
the same length.

.. code-block:: python

    import numpy as np

    # energy and nrays must have the same length: they are coupled
    energy   = np.array([200, 400, 600])
    nrays    = np.array([20, 40, 60])
    SlitSize = np.array([0.1])

    # photonEnergy is independent; numberRays is dependent on it
    params = [
        {beamline.Dipole.photonEnergy: energy, beamline.Dipole.numberRays: nrays},
        {beamline.ExitSlit.totalHeight: SlitSize},
    ]

    sim.params = params

Here ``numberRays`` does not multiply the number of simulations: there are
``3 x 1 = 3`` simulations, and at each one ``numberRays`` takes the value paired
with the current ``photonEnergy``:

.. list-table:: 3 simulations: ``numberRays`` coupled to ``photonEnergy``
   :header-rows: 1
   :widths: 10 26 26 26

   * - sim #
     - ``photonEnergy`` (independent)
     - ``numberRays`` (dependent)
     - ``totalHeight`` (independent)
   * - 0
     - 200
     - 20
     - 0.1
   * - 1
     - 400
     - 40
     - 0.1
   * - 2
     - 600
     - 60
     - 0.1

More than one parameter can be coupled to the same independent parameter by
adding further keys to the dictionary (all with value lists of the same
length). For example ``{photonEnergy: energy, numberRays: nrays, energySpread:
spread}`` keeps ``numberRays`` and ``energySpread`` both locked to
``photonEnergy``.

.. note::

   A dependent parameter advances together with the **fastest-varying** scan
   dimension, which is the **last** independent parameter in the list. When you
   mix a coupled block with other independent parameters that have more than one
   value, put the coupled block **last** so the coupling stays aligned with its
   partner. In the example above this is automatic, because the only other
   independent parameter (``totalHeight``) has a single value.

The simulations files and the results will be saved in a folder called `RAYPy_simulation_`
and a name of your choice, that can be set. This folder will be saved, by default, 
in the folder where the program is executed, but it can eventually be modified

.. code-block:: python

    sim.simulation_folder = '/home/raypy/Documents/simulations'
    sim.simulation_name = 'test'

This will create a simulation folder with the following path and name:

.. code-block:: text

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

Output:

.. code-block:: text

    ['AnglePhiDistribution',
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
     'ScalarElementProperties']

To let raypyng analyze the results set:

.. code-block:: python

    sim.analyze = False # don't let RAY-UI analyze the results
    sim.raypyng_analysis=True # let raypyng analyze the results

In this case, only these exports are possible:

.. code-block:: python

    print(sim.possible_exports_without_analysis)

Output:

.. code-block:: text

    ['RawRaysIncoming', 'RawRaysOutgoing']

The exports are available for each optical element in the beamline, ImagePlanes included, and can be set like this:

.. code-block:: python

    ## This must be a list of dictionaries
    sim.exports  =  [{beamline.Dipole:['ScalarElementProperties']},
                    {beamline.DetectorAtFocus:['ScalarBeamProperties']}
                    ]

Finally, the simulations can be run using

.. code-block:: python

    sim.run(multiprocessing="auto", force=True)

.. important::

   **Always guard the call to** :code:`sim.run()` **with**
   :code:`if __name__ == '__main__':`. raypyng runs the simulations in parallel
   through Python's :code:`multiprocessing`. On macOS (and Windows) the worker
   processes are created with the :code:`spawn` start method, which **re-imports
   your script** in every worker. Without the guard, each worker would execute
   :code:`sim.run()` again on import, leading to runaway process creation and a
   :code:`RuntimeError`. On Linux the default start method is :code:`fork`, which
   does not re-import the script, so the guard is not strictly required there —
   but adding it is harmless and makes the same script work on every platform.

   A complete script therefore looks like this:

   .. code-block:: python

       import numpy as np
       from raypyng import Simulate

       if __name__ == '__main__':
           rml_file = 'rml/dipole_beamline.rml'
           sim = Simulate(rml_file, hide=True)
           beamline = sim.rml.beamline

           sim.params = [
               {beamline.Dipole.photonEnergy: np.array([200, 400, 600])},
               {beamline.ExitSlit.totalHeight: np.array([0.1])},
           ]
           sim.simulation_name = 'test'
           sim.exports = [{beamline.DetectorAtFocus: ['RawRaysOutgoing']}]

           sim.run(multiprocessing="auto", force=True)

where the `multiprocessing` parameter can be:

- an integer greater or equal to 1, corresponding to the number of parallel instances of RAY-UI to be used
- `"auto"`, which uses the minimum between the available CPU count and the available RAM in GB minus 2
- `"max"`, which uses the minimum between the available CPU count and the available RAM in GB

Generally speaking, the number of instances of RAY-UI must be lower or equal than the number of available cores. If the simulation uses many rays, monitor the RAM usage of your computer. If the computation uses all the possible RAM of the computer the program may get blocked or not execute correctly.

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

    RAYPy_Simulation_mySimulation
    ├── looper.csv
    ├── looper.txt
    ├── Dipole_RawRaysOutgoing.csv                    (if raypyng analyzes the results)
    ├── DetectorAtFocus_RawRaysOutgoing.csv           (if raypyng analyzes the results)
    ├── raypyng_analysis_metadata.json                (if raypyng analyzes the results)
    ├── round_0
    │   ├── 0_mySimulation.rml
    │   ├── 0_Dipole-RawRaysOutgoing.csv
    │   ├── 0_Dipole_analyzed_rays_RawRaysOutgoing.dat        (if raypyng analyzes the results)
    │   ├── 0_DetectorAtFocus-RawRaysOutgoing.csv
    │   ├── 0_DetectorAtFocus_analyzed_rays_RawRaysOutgoing.dat (if raypyng analyzes the results)
    │   └── ...
    ├── round_1
    │   └── ...
    └── round_n
        └── ...



Analysis performed by RAY-UI 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**This is discouraged, as this approach is very slow.**

If you decided to let RAY-UI do the analysis, you should expect the following files to be 
saved in your simulation folder:

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

- `looper.csv` and `looper.txt`, containing the simulation number and the scanned input parameters
- one folder called `round_n` for each repetition of the simulations. 
  For instance, if you set :code:`sim.repeat=2` you will have two folders `round_0` and `round_1`
- inside each `round_n` folder you will find the beamline files modified with the parameters 
  you set in `sim.params`, these are the `.rml` files, that can be opened by RAY-UI.
- inside each `round_n` folder you will find your exported files, one for each simulation. 
  If for instance, you exported the `RawRaysOutgoing` of the Dipole, you will 
  have a list of files `0_Dipole-RawRaysOutgoing.csv`
- for each `RawRaysOutgoing` file, raypyng calculates some properties, 
  and saves a corresponding file, for instance `0_Dipole_analyzed_rays_RawRaysOutgoing.dat`
- in the simulation folder, the analyzed results for each exported element are brought together
  (and averaged in case of more rounds of simulations) in one single file.
  For the dipole, the file is called `Dipole_RawRaysOutgoing.csv`
- one shared metadata sidecar, `raypyng_analysis_metadata.json`, describing the units of the
  analyzed output columns. This metadata file is written only if :code:`sim.raypyng_analysis=True`

The combined recap files contain the scanned input parameters from `looper.csv`,
followed by the analyzed output columns. The analyzed columns currently include:

- `SourcePhotonFlux` (`photons/s`)
- `SourceBandwidth` (`eV`)
- `NumberRaysSurvived` (`count`)
- `PercentageRaysSurvived` (`%`)
- `PhotonEnergy` (`eV`)
- `Bandwidth` (`eV`)
- `HorizontalFocusFWHM` (`mm`)
- `VerticalFocusFWHM` (`mm`)
- `HorizontalDivergenceFWHM` (`deg`)
- `VerticalDivergenceFWHM` (`deg`)
- `HorizontalCenter` (`mm`)
- `VerticalCenter` (`mm`)
- `PhotonFlux` (`photons/s`)
- `EnergyPerMilPerBw` (dimensionless)
- `FluxPerMilPerBwPerc` (dimensionless)
- `FluxPerMilPerBwAbs` (dimensionless)
- `AXUVCurrentAmp` (`A`)
- `GaAsPCurrentAmp` (`A`)

Shared metadata sidecar
^^^^^^^^^^^^^^^^^^^^^^^^
When raypyng performs the analysis, it also writes one metadata file in the simulation folder:

- `raypyng_analysis_metadata.json`

This file:

- applies to all raypyng-analyzed output CSV files in the same simulation folder
- lists only the analyzed-output columns, starting at `SourcePhotonFlux`
- stores a column-to-unit mapping without modifying the CSV headers

This keeps existing scripts based on exact CSV column names compatible, while still making the
units available in a machine-readable format.

Providing your own flux and efficiency tables
---------------------------------------------

RAY-UI traces the *geometry* of the beamline very well, but the **absolute
photon flux** it assigns to a source, and the efficiency of optical elements it
cannot model (for instance a grating coated with a multilayer), are often better
known from external calculations or measurements. raypyng lets you feed in two
kinds of tabulated data at simulation runtime, which are then used by the
analysis to produce more realistic numbers:

- an **undulator flux table** (:code:`sim.undulator_table`), and
- a **general efficiency table** (:code:`sim.efficiency`).

Both are passed as pandas DataFrames before calling :code:`sim.run()`, and both
only affect the *flux-related* analyzed columns. The geometric quantities
(focus FWHM, divergence, bandwidth, beam centre) are unchanged.

Undulator flux table
^^^^^^^^^^^^^^^^^^^^^

When the source is an undulator, the flux emitted per harmonic as a function of
photon energy is usually computed with a dedicated code (e.g. WAVE or SPECTRA).
You can supply that spectrum as a table; raypyng then **ignores the source flux
estimated by RAY-UI and uses your tabulated flux instead**.

The table must be a DataFrame with an **even number of columns, grouped in
energy/flux pairs, one pair per odd harmonic**, named exactly
``Energy1[eV]``, ``Photons1``, ``Energy3[eV]``, ``Photons3``,
``Energy5[eV]``, ``Photons5``, … (the bundled example
``examples/undulator/undulator_harmonics_energy_photons.csv`` follows this
format). The source in the ``.rml`` must be a real undulator: it **cannot** be a
``Dipole`` or an ``Undulator File`` source.

.. code-block:: python

    import pandas as pd

    undulator = pd.read_csv('undulator/undulator_harmonics_energy_photons.csv')
    sim.undulator_table = undulator

    sim.run(multiprocessing="auto", force=True)

**Impact on the results.** This is the important part. Without a table, raypyng
writes a single set of flux columns and computes the flux at the detector as

.. code-block:: text

    PhotonFlux = SourcePhotonFlux (from RAY-UI) / 100 * PercentageRaysSurvived

With an undulator table, the source flux no longer comes from RAY-UI. For each
simulated photon energy and **each harmonic** :code:`h`, raypyng linearly
interpolates your tabulated flux ``Photons{h}`` and scales it by the fraction of
rays that survived the beamline:

.. code-block:: text

    PhotonFlux{h} = interp(energy, Energy{h}[eV], Photons{h}) * PercentageRaysSurvived / 100

Consequently the analyzed output gains **one set of flux columns per harmonic**
instead of a single one. For a table with harmonics 1, 3 and 5 you get, for
example, ``PhotonFlux1``, ``PhotonFlux3``, ``PhotonFlux5``, and likewise
``FluxPerMilPerBwAbs1/3/5``, ``AXUVCurrentAmp1/3/5`` and
``GaAsPCurrentAmp1/3/5``. In short: the absolute flux and the diode currents are
driven entirely by your table (per harmonic), while the ray tracing only
contributes the transmission and the geometry.

General efficiency table
^^^^^^^^^^^^^^^^^^^^^^^^^

The efficiency table covers the second case: an optical element whose
energy-dependent efficiency RAY-UI does not compute — the typical example being
a **grating coated with a multilayer**, but it applies to any element for which
you have your own tabulated efficiency (reflectivity, diffraction efficiency,
filter transmission, …).

The table must be a DataFrame with two columns, ``Efficiency`` and
``Energy[eV]``:

.. code-block:: python

    import pandas as pd

    eff = pd.DataFrame({
        "Efficiency": [0.9, 0.8, 0.7],
        "Energy[eV]": [100, 200, 300],
    })
    sim.efficiency = eff

    sim.run(multiprocessing="auto", force=True)

**Impact on the results.** The efficiency is linearly interpolated at each
simulated photon energy and multiplies the transmission:

.. code-block:: text

    PercentageRaysSurvived = (rays_survived / rays_source) * 100 * efficiency(energy)

Because every flux-related quantity (``PhotonFlux``, ``FluxPerMilPerBwPerc``,
``FluxPerMilPerBwAbs``, the diode currents) is derived from
``PercentageRaysSurvived``, all of them are scaled down by the same efficiency
factor. The number of columns does not change; only their values are reduced to
account for the element you modelled externally.

.. note::

   The two tables are independent and can be used together. The efficiency
   table scales the transmission; the undulator table sets the absolute source
   flux per harmonic. Neither affects the focus size, divergence, bandwidth or
   beam-centre columns, which depend only on the traced geometry.

Working with the results
------------------------

.. note::

   This section is intentionally minimal for now and will be expanded.

When raypyng performs the analysis, the most convenient output is the combined
recap file written in the simulation folder, one per exported element, for
example ``DetectorAtFocus_RawRaysOutgoing.csv``. Each row is one simulation; the
first columns are the scanned input parameters (taken from ``looper.csv``) and
the remaining columns are the analyzed quantities listed above.

It is a plain CSV, so it can be loaded directly with pandas:

.. code-block:: python

    import pandas as pd

    df = pd.read_csv('RAYPy_Simulation_test/DetectorAtFocus_RawRaysOutgoing.csv')

    # the scanned input parameters are columns named "<element>.<parameter>"
    energy = df['Dipole.photonEnergy']

    # the analyzed outputs are columns such as these
    flux = df['PhotonFlux']
    transmission = df['PercentageRaysSurvived']
    h_fwhm = df['HorizontalFocusFWHM']

    print(df.columns.tolist())

You can then filter, plot, or further process the DataFrame as usual. A complete
plotting example is available in `eval_permil.py
<https://github.com/hz-b/raypyng/blob/main/examples/eval_permil.py>`_.

Recipes
========
raypyng provides some recipes to make simulations,
that simplify the syntax in the script.
Two recipes are provided, one to make `Resolving Power
<https://github.com/hz-b/raypyng/blob/main/examples/simulation_recipee_ResolvinPower.py>`_ simulations,
one to make `Flux
<https://github.com/hz-b/raypyng/blob/main/examples/simulation_recipee_Flux.py>`_
simulations.


List of available examples
===========================
All examples live in the `examples folder
<https://github.com/hz-b/raypyng/blob/main/examples>`_ of the repository. A short
description of each one follows.

Simulation examples
-------------------
These scripts run a beamline scan end to end.

- `simulation_raypyng.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_raypyng.py>`_ —
  basic simulation: scan the photon energy and exit-slit aperture of a dipole
  beamline and let **raypyng** analyze the exported rays.
- `simulation_analysis_by_RAY-UI.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_analysis_by_RAY-UI.py>`_ —
  the same kind of scan, but letting **RAY-UI** perform the analysis
  (:code:`ScalarBeamProperties` / :code:`ScalarElementProperties`).
- `simulation_permil.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_permil.py>`_ —
  flux and bandwidth per 0.1% bandwidth, scanning energy for two grating line
  densities.
- `simulation_external_undulator_flux_table.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_external_undulator_flux_table.py>`_ —
  undulator source whose flux is taken from an external flux table
  (:code:`sim.undulator_table`).
- `simulation_multilayer_monochromator_efficiency.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_multilayer_monochromator_efficiency.py>`_ —
  fold an externally computed monochromator efficiency into the results
  (:code:`sim.efficiency`).
- `simulation_waveFiles.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_waveFiles.py>`_ —
  drive an Undulator from external WAVE ray files via the :code:`undulatorFile`
  parameter.
- `simulation_slope_errors.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_slope_errors.py>`_ —
  scan the meridional/sagittal slope errors of the mirrors one at a time.
- `simulation_save_space.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_save_space.py>`_ —
  same scan as the basic example but deleting raw-ray files and round folders to
  save disk space (:code:`remove_rawrays`, :code:`remove_round_folders`).
- `simulation_recipee_Flux.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_recipee_Flux.py>`_ —
  run a flux scan with the ready-made :code:`Flux` recipe.
- `simulation_recipee_ResolvinPower.py
  <https://github.com/hz-b/raypyng/blob/main/examples/simulation_recipee_ResolvinPower.py>`_ —
  run a resolving-power scan with the ready-made :code:`ResolvingPower` recipe.

Building-block and post-processing examples
-------------------------------------------
These scripts show individual pieces of raypyng without running a full scan.

- `example_rml.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_rml.py>`_ —
  open an RML file, list its elements and parameters, and modify a value.
- `example_runner.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_runner.py>`_ —
  drive RAY-UI directly through :code:`RayUIRunner` / :code:`RayUIAPI`
  (load, trace, export, quit).
- `example_waveHelper.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_waveHelper.py>`_ —
  use :code:`WaveHelper` to inspect a WAVE folder and list the available
  undulator energies/files.
- `example_beamwaist.py
  <https://github.com/hz-b/raypyng/blob/main/examples/example_beamwaist.py>`_ —
  trace and plot the beam waist along the beamline with :code:`PlotBeamwaist`.
- `dipole.py
  <https://github.com/hz-b/raypyng/blob/main/examples/dipole.py>`_ —
  compute and plot a dipole source spectrum from its magnetic field with the
  standalone :code:`Dipole` class (no RAY-UI needed).
- `diodes.py
  <https://github.com/hz-b/raypyng/blob/main/examples/diodes.py>`_ —
  convert a photon flux into a diode current for AXUV and GaAsP diodes.
- `eval_permil.py
  <https://github.com/hz-b/raypyng/blob/main/examples/eval_permil.py>`_ —
  post-process and plot the results produced by ``simulation_permil.py``.

  
  
