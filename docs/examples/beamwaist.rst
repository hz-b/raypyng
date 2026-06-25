05 beamwaist
************

This example traces the beam through the line and renders the beamwaist along
the optical elements. The simulation prepares the result folder, and the eval
script loads those results and writes the final figure next to the example
scripts.

The simulation script:

.. literalinclude:: ../../examples/05_beamwaist/simulation_beamwaist.py
   :language: python

The eval script:

.. literalinclude:: ../../examples/05_beamwaist/eval_beamwaist.py
   :language: python

Result:

.. image:: ../images/05_beamwaist.png
   :alt: beamwaist example plot
   :width: 700px
