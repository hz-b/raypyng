API
****

Simulation
============

Simulate
----------------
.. autoclass:: raypyng.simulate.Simulate
   :members:

SimulationParams
----------------
.. autoclass:: raypyng.simulate.SimulationParams
   :members:

WaveHelper
------------
Some source in RAY-UI can take as an input a file obtained by simulating the 
insertion device with WAVE. This class inspects the folder where the WAVES results are
stored and provides a simple way to get a list of absolute paths to the simulation files.

.. autoclass:: raypyng.wave_helper.WaveHelper
   :members:

VLS Grating Coefficient Calculation
====================================

This is a set of helper functions that can be used to calculate VLS gratings.

.. autofunction:: raypyng.vls_grating.calculate_vls_coeff


.. autofunction:: raypyng.vls_grating.N1_to_b2

.. autofunction:: raypyng.vls_grating.cff_for_fixed_focus


Recipes
==================

Resolving Power
----------------
.. autoclass:: raypyng.recipes.ResolvingPower
   :members:

Flux
----------------
.. autoclass:: raypyng.recipes.Flux
   :members:


Process simulation files
==========================

PostProcess rays analyzed by raypyng
--------------------------------------
.. autoclass:: raypyng.postprocessing.PostProcess
   :members:

PostProcess rays analyzed by RAY-UI
------------------------------------
.. autoclass:: raypyng.postprocessing.PostProcessAnalyzed
   :members:

RayProperties
------------------------------------
.. autoclass:: raypyng.postprocessing.RayProperties
   :members:
   
RAY-UI API
============
RayUIRunner
----------------
.. autoclass:: raypyng.runner.RayUIRunner
   :members:

RayUIAPI
----------------
.. autoclass:: raypyng.runner.RayUIAPI
   :members:

RML
==================

RMLFile
----------------
.. autoclass:: raypyng.rml.RMLFile
   :members:
   :inherited-members:

BeamlineElement
----------------
.. autoclass:: raypyng.rml.BeamlineElement
   :members:
   :inherited-members:

ObjectElement
----------------
.. autoclass:: raypyng.rml.ObjectElement
   :members:
   :inherited-members:

ParamElement
----------------
.. autoclass:: raypyng.rml.ParamElement
   :members:
   :inherited-members:

Beamline Inspection
====================

These functions build a summary table from any ``.rml`` file without running a
simulation. They are useful for quickly checking element positions and key
beamline parameters after loading a new beamline design.

.. autofunction:: raypyng.inspect.build_tables

.. autofunction:: raypyng.inspect.save_tables

.. autofunction:: raypyng.inspect.world_position


Dipole
==================
Based on  `srxraylib <https://srxraylib.readthedocs.io/en/latest/>`_

.. autoclass:: raypyng.dipole_flux.Dipole
   :members:
   :inherited-members:

