00 raypyng
**********

This is the main raypyng workflow example. It scans a dipole beamline over
photon energy and exit-slit size, lets raypyng analyze the exported rays, and
then plots the combined recap file written in the simulation folder.

The simulation script:

.. literalinclude:: ../../examples/00_raypyng/simulation_raypyng.py
   :language: python

The eval script:

.. literalinclude:: ../../examples/00_raypyng/eval_raypyng.py
   :language: python

Result:

.. image:: ../images/00_raypyng.png
   :alt: raypyng example plot
   :width: 700px
