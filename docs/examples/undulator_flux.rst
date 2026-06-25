08 external undulator flux table
********************************

This example shows how to use an external undulator flux table. The top-level
recap file ``DetectorAtFocus_RawRaysOutgoing.csv`` contains the geometric
results together with the harmonic-resolved flux columns such as
``PhotonFlux1`` and ``FluxPerMilPerBwAbs1``. That recap file is the main result
to inspect and plot after the simulation. Outside the tabulated energy window
of a harmonic, the harmonic-derived recap columns are written as ``NaN`` so the
plot can ignore them naturally.

The simulation script:

.. literalinclude:: ../../examples/08_external_undulator_flux_table/simulation_external_undulator_flux_table.py
   :language: python

The eval script:

.. literalinclude:: ../../examples/08_external_undulator_flux_table/eval_external_undulator_flux_table.py
   :language: python

Result:

.. image:: ../images/08_external_undulator_flux_table.png
   :alt: external undulator flux table example plot
   :width: 700px
