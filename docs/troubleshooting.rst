Troubleshooting / FAQ
*********************

A short list of the most common questions and pitfalls. Many of these are also
mentioned in context in the :doc:`installation` and :doc:`tutorial` pages; they
are collected here for convenience.

Do I need the ``if __name__ == '__main__':`` guard?
===================================================
**Yes, on macOS and Windows.** raypyng runs the simulations in parallel through
Python's :code:`multiprocessing`. On macOS and Windows the worker processes are
created with the :code:`spawn` start method, which **re-imports your script** in
every worker. If the call to :code:`sim.run()` is not protected by
:code:`if __name__ == '__main__':`, each worker re-runs it on import, leading to
runaway process creation and a :code:`RuntimeError` about the bootstrapping
phase.

On Linux the default start method is :code:`fork`, which does not re-import the
script, so the guard is not strictly required there — but adding it is harmless
and makes the same script work on every platform.

I get a ``RuntimeError`` about "bootstrapping phase"
====================================================
This is the symptom of the missing guard described above. Wrap your simulation
setup and the :code:`sim.run()` call in :code:`if __name__ == '__main__':`.

On macOS, "Ray-UI is not responding" / "Ray-UI quit unexpectedly"
=================================================================
**This is harmless and can be ignored.** While simulations run, macOS may
sporadically show a dialog saying that Ray-UI is not responding or quit
unexpectedly. It is just macOS noticing that the headless RAY-UI instances are
started and stopped rapidly. The simulations are not affected and complete
normally — simply dismiss the dialogs.

Do I need to install xvfb?
==========================
**Only on Linux.** On Linux, xvfb provides the virtual X11 framebuffer that lets
RAY-UI run headless, and raypyng uses ``xvfb-run`` automatically. On macOS xvfb
is **not** needed and must not be installed; raypyng skips it automatically and
the :code:`hide` parameter is simply ignored.

raypyng cannot find RAY-UI
==========================
By default raypyng searches the standard installation folders. If your
installation is elsewhere, pass the path explicitly:

.. code-block:: python

    sim = Simulate('rml/dipole_beamline.rml', hide=True, ray_path='/path/to/RAY-UI')

On macOS the installer creates a ``Ray-UI.app`` bundle, so the installation
folder is the directory that *contains* ``Ray-UI.app`` (for example
``~/Applications/RAY-UI``), not the ``.app`` itself.

How many parallel instances should I use?
=========================================
The ``multiprocessing`` argument to :code:`sim.run()` controls how many RAY-UI
instances run in parallel:

- an integer ``>= 1`` — that exact number of instances,
- ``"auto"`` — the minimum between the available CPU count and the available
  RAM in GB minus 2,
- ``"max"`` — the minimum between the available CPU count and the available RAM
  in GB.

As a rule of thumb, do not use more instances than you have CPU cores. If your
simulations use many rays, watch the RAM usage: if the machine runs out of
memory the program may block or produce incorrect results. In that case reduce
the number of parallel instances or the number of rays.

My simulations are slow
=======================
The speedup from running many RAY-UI instances in parallel is effective only
when RAY-UI is **not** doing the analysis. Prefer letting raypyng analyze the
results:

.. code-block:: python

    sim.analyze = False          # don't let RAY-UI analyze the results
    sim.raypyng_analysis = True  # let raypyng analyze the results
