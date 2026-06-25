.. RayPyNG documentation master file, created by
   sphinx-quickstart on Fri Aug 12 08:56:07 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to raypyng's documentation!
===================================
raypyng provides a simple python API to work with
`RAY-UI
<https://www.helmholtz-berlin.de/forschung/oe/wi/optik-strahlrohre/arbeitsgebiete/ray_en.html>`_,
a software for optical simulation of synchrotron
beamlines and x-ray systems developed by
Helmholtz-Zentrum Berlin.

raypyng loads a beamline saved from RAY-UI as an ``.rml`` file, scans any number
of its parameters, runs the traces in parallel, and post-processes the exported
rays for you.

Quickstart
----------
You need a beamline ``.rml`` file created and saved with RAY-UI. The following
minimal script scans the photon energy of a dipole source and writes the
analyzed rays at the focus:

.. code-block:: python

    import numpy as np
    from raypyng import Simulate

    if __name__ == '__main__':
        # a beamline previously saved from RAY-UI
        sim = Simulate('rml/dipole_beamline.rml', hide=True)
        beamline = sim.rml.beamline

        # scan the source photon energy
        sim.params = [
            {beamline.Dipole.photonEnergy: np.arange(200, 2001, 200)},
        ]

        sim.simulation_name = 'quickstart'
        sim.analyze = False          # let raypyng (not RAY-UI) analyze the rays
        sim.raypyng_analysis = True
        sim.exports = [{beamline.DetectorAtFocus: ['RawRaysOutgoing']}]

        # run, using as many parallel RAY-UI instances as the machine allows
        sim.run(multiprocessing="auto", force=True)

The results are written to a ``RAYPy_Simulation_quickstart`` folder. See the
:doc:`tutorial` for a full walk-through, including how the parameters combine and
how to read the output.

.. note::

   The ``if __name__ == '__main__':`` guard is required on macOS, where
   raypyng's parallel workers re-import your script. See the :doc:`tutorial`
   for details. (raypyng runs simulations on Linux and macOS only — not on
   Windows.)


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   installation
   tutorial
   examples/index
   how_to
   troubleshooting
   API
   

