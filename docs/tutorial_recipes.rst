Recipes
*******

raypyng provides recipes to simplify common simulation workflows.

The main built-in recipes are:

- :code:`raypyng.recipes.ResolvingPower`
- :code:`raypyng.recipes.Flux`
- :code:`raypyng.recipes.BeamWaist`

These recipes package together parameter scans, exports, and setup choices for
common beamline studies.

For custom workflows, see :doc:`how_to`, which shows how to write your own
recipe by subclassing :code:`SimulationRecipe`.

Example:

.. code-block:: python

    from raypyng import Simulate
    from raypyng.recipes import Flux

    sim = Simulate('rml/dipole_beamline.rml', hide=True)
    recipe = Flux(energy=1000, nrays=10000, sim_folder='MyRecipeTest')

    if __name__ == '__main__':
        sim.run(recipe, multiprocessing="auto", force=True)
