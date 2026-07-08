RAY-UI API
**********

Using the :code:`RayUIRunner` and :code:`RayUIAPI` classes it is possible to
interact with RAY-UI directly from Python.

.. code-block:: python

    from raypyng.runner import RayUIRunner, RayUIAPI

    r = RayUIRunner(ray_path=None, hide=True)
    a = RayUIAPI(r)

    r.run()

Once an instance of RAY-UI is running, we can confirm that it is running and
ask for its :code:`pid`:

.. code-block:: python

    print(r.isrunning)
    print(r.pid)

It is possible to load an RML file and trace it:

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

Save the RML file used for the simulation:

.. code-block:: python

    a.save('rml/new_dipole_beamline')

And finally quit the RAY-UI instance:

.. code-block:: python

    a.quit()
