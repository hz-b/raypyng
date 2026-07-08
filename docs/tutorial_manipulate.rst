Manipulate an RML File
**********************

Using the :code:`RMLFile` class it is possible to inspect and manipulate a
beamline file produced by RAY-UI.

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

It is possible to list all the elements present in the beamline using the
:code:`children()` method:

.. code-block:: python

    for i, oe in enumerate(beamline.children()):
        print('OE ', i, ':', oe.resolvable_name())

In a similar way one can print all the available parameters of a certain
element:

.. code-block:: python

    for param in beamline.Dipole.children():
        print('Dipole param: ', param.id)

Any parameter can be read and modified through its :code:`cdata` attribute:

.. code-block:: python

    print(beamline.Dipole.photonEnergy.cdata)
    beamline.Dipole.photonEnergy.cdata = str(2000)
    print(beamline.Dipole.photonEnergy.cdata)

Once you are done with the modifications, you can save the RML file using the
:code:`write()` method:

.. code-block:: python

    rml.write('rml/new_dipole_beamline.rml')
