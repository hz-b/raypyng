Simulations
***********

Perform Simulations
===================

raypyng is not able to create a beamline from scratch. To do so, use RAY-UI,
create a beamline, and save it as an :code:`.rml` file. In the following
example, we use a dipole beamline saved in :code:`rml/dipole_beamline.rml`.

.. code-block:: python

    from raypyng import Simulate

    rml_file = 'rml/dipole_beamline.rml'
    sim = Simulate(rml_file, hide=True)
    beamline = sim.rml.beamline

The elements of the beamline are now available as Python objects, as well as
their properties. For instance:

.. code-block:: python

    beamline.Dipole
    beamline.Dipole.photonFlux
    beamline.Dipole.photonFlux.cdata
    beamline.Dipole.photonFlux.cdata = 10

Independent and dependent parameters
====================================

To perform a simulation, any number of parameters can be varied. The values to
scan are passed to :code:`sim.params` as a **list of dictionaries**.

- Each dictionary contributes one independent parameter: its first key.
- Additional keys in the same dictionary are dependent parameters.
- The total number of simulations is the product of the independent parameter
  lengths only.

Independent parameters (a grid)
--------------------------------

.. code-block:: python

    import numpy as np

    energy = np.array([200, 400])
    slit_size = np.array([0.1, 0.5, 0.9])

    sim.params = [
        {beamline.Dipole.photonEnergy: energy},
        {beamline.ExitSlit.totalHeight: slit_size},
    ]

Dependent (coupled) parameters
------------------------------

.. code-block:: python

    import numpy as np

    energy = np.array([200, 400, 600])
    nrays = np.array([20, 40, 60])

    sim.params = [
        {beamline.Dipole.photonEnergy: energy, beamline.Dipole.numberRays: nrays},
        {beamline.ExitSlit.totalHeight: np.array([0.1])},
    ]

Beamline and element toggles
============================

raypyng lets you manipulate reflectivity, slope errors, and alignment errors
either per element or for the whole beamline.

Per-element toggles
-------------------

Direct per-element toggles work on elements that actually define the
corresponding RML parameter:

.. code-block:: python

    beamline.M1.reflectivity_enabled = True
    beamline.M1.slope_error_enabled = False
    beamline.M1.alignment_error_enabled = True

    print(beamline.M1.reflectivity_enabled)
    print(beamline.M1.slope_error_enabled)
    print(beamline.M1.alignment_error_enabled)

If an element does not support one of these parameters, raypyng raises
:code:`AttributeError`.

Beamline-wide toggles
---------------------

The :code:`Simulate` API exposes the matching beamline-wide helpers:

.. code-block:: python

    sim.reflectivity(False)
    sim.slope_errors(True)
    sim.alignment_errors(False)

These helpers update every element in the beamline that supports the matching
parameter and leave unsupported elements untouched.

Simulation folder, exports, and analysis
=========================================

The simulation files and results are saved in a folder called
:code:`RAYPy_Simulation_` plus a name of your choice:

.. code-block:: python

    sim.simulation_folder = '/home/raypy/Documents/simulations'
    sim.simulation_name = 'test'

Repeat count, exports, and analysis mode can be configured like this:

.. code-block:: python

    sim.repeat = 1
    sim.analyze = False
    sim.raypyng_analysis = True
    sim.exports = [{beamline.DetectorAtFocus: ['RawRaysOutgoing']}]

Finally, the simulations can be run using:

.. code-block:: python

    sim.run(multiprocessing="auto", force=True)

.. important::

   Always guard the call to :code:`sim.run()` with
   :code:`if __name__ == '__main__':` so the script works correctly on macOS
   and Windows multiprocessing as well as on Linux.

Providing your own flux and efficiency tables
=============================================

raypyng can incorporate external tabulated data at simulation runtime:

- an undulator flux table through :code:`sim.undulator_table`
- a general efficiency table through :code:`sim.efficiency`

Both affect the flux-related analyzed columns, while geometric quantities such
as focus size, divergence, bandwidth, and beam center remain determined by the
traced beamline geometry.

Working with the results
========================

When raypyng performs the analysis, the most convenient output is the combined
recap CSV written in the simulation folder. It can be loaded directly with
pandas:

.. code-block:: python

    import pandas as pd

    df = pd.read_csv('RAYPy_Simulation_test/DetectorAtFocus_RawRaysOutgoing.csv')
    energy = df['Dipole.photonEnergy']
    flux = df['PhotonFlux']
    transmission = df['PercentageRaysSurvived']
