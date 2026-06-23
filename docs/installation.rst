Installation
*************
raypyng runs the simulations on **Linux** and **macOS**.

.. warning::

   **Windows is not supported for running simulations.** Driving RAY-UI from
   Python relies on RAY-UI's *background mode*, which lets raypyng send commands
   and read results over a pipe. RAY-UI does not provide a background mode on
   Windows, so there is no way for raypyng to communicate with it there. The
   pure-Python helpers that do not launch RAY-UI (for example reading/writing
   ``.rml`` files or the standalone ``Dipole`` spectrum) may still work on
   Windows, but the whole simulation workflow does not.

The installation has two parts that are common to every supported platform:

#. Install **RAY-UI**, the ray-tracing engine that raypyng drives.
#. Install the **raypyng** Python package.

On Linux there is one extra step: installing **xvfb** so that RAY-UI can run
headless. On macOS xvfb is **not** needed and must not be installed.

Pick the section for your operating system below.


Install RAY-UI
==============
Download the RAY-UI installer from `this link
<https://www.helmholtz-berlin.de/forschung/oe/wi/optik-strahlrohre/arbeitsgebiete/ray_en.html>`_
and run it. The installer is available for both Linux and macOS.

On macOS the installer creates a ``Ray-UI.app`` bundle inside the chosen
installation folder (for example ``~/Applications/RAY-UI/Ray-UI.app``). raypyng
detects this layout automatically.


Install raypyng (Python package)
================================
You will need Python 3.10 or newer. From a shell ("Terminal" on macOS), check
your current Python version:

.. code-block:: bash

  python3 --version

If that version is older than 3.10, update it before continuing.

We strongly recommend installing raypyng into a **virtual environment** so that
this installation does not interfere with any existing Python software. Setting
up and activating a virtual environment is outside the scope of this guide;
please refer to your preferred tool's documentation.

Once your environment is ready, install raypyng:

.. code-block:: bash

   python3 -m pip install --upgrade raypyng


Linux installation
===================
On Linux, RAY-UI needs a virtual X11 framebuffer to run without a visible
graphical display. This is provided by **xvfb**.

Install xvfb:

.. code-block:: bash

  sudo apt install xvfb

.. note::

  The ``xvfb-run`` script is part of the xvfb distribution and runs an
  application on a new virtual X11 server. raypyng uses it automatically to
  launch RAY-UI headlessly.

After installing RAY-UI, xvfb, and raypyng (see the sections above), you are
ready to run simulations.


macOS installation
===================
On macOS you only need to install **RAY-UI** and the **raypyng** Python package
(see the sections above). You do **not** need to install xvfb — raypyng skips it
automatically on macOS, and trying to install it is unnecessary.

.. note::

  While simulations are running on macOS, the system may sporadically show a
  dialog saying that **"Ray-UI is not responding" / "Ray-UI quit unexpectedly"**.
  This is harmless: it is just macOS noticing that the headless RAY-UI instances
  are being started and stopped rapidly. The simulations are not affected and
  complete normally — you can safely **ignore and dismiss these dialogs**.


Optional: rayx engine (experimental)
=====================================

.. warning::

   **The rayx integration is work in progress and not yet complete.**
   Results may differ from RAY-UI, particularly for beamlines containing
   diffraction gratings.  Use it for exploratory purposes only and always
   cross-check against a RAY-UI simulation.

raypyng can optionally use `rayx <https://github.com/hz-b/rayx>`_, a GPU-based
ray-tracing engine, as an alternative simulation backend.  The rayx engine and
the grating-efficiency library `graxpy <https://pypi.org/project/graxpy/>`_ are
both installed with:

.. code-block:: bash

   pip install "raypyng[rayx]"

rayx itself must also be installed separately following its own installation
instructions.  Once rayx is available, you can switch the engine by passing
``engine="rayx"`` to :class:`~raypyng.Simulate`:

.. code-block:: python

   sim = Simulate('beamline.rml', hide=True, engine='rayx')

Known limitations at this stage:

* Per-element photon flux calculated with the rayx engine may differ
  significantly from RAY-UI for beamlines with a plane grating monochromator,
  because the two engines model grating energy selectivity differently.
* Grating diffraction efficiency is applied via graxpy (RCWA) as a
  post-processing step, weighted by each ray's electric-field amplitude squared.
* The ``graxpy_efficiency`` parameter must be set to ``True`` on
  :class:`~raypyng.Simulate` to enable the efficiency correction.
