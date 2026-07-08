import os

from raypyng.recipes import plot_slopes_scan


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    simulation_folder = os.path.join(this_file_dir, "RAYPy_Simulation_1200_slopes_and_exit_slit_cff5")

    plot_slopes_scan(
        simulation_folder,
        output_folder=os.path.join(this_file_dir, "plot", "slopes"),
        exported_object_name="DetectorAtFocus",
        showplot=False,
        saveplot=True,
    )

