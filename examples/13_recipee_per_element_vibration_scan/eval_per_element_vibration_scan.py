import os

from raypyng.recipes import plot_per_element_vibration_scan


if __name__ == "__main__":
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    simulation_folder = os.path.join(this_file_dir, "RAYPy_Simulation_per_element_vibration_scan")

    plot_per_element_vibration_scan(
        simulation_folder,
        output_folder=os.path.join(this_file_dir, "plot", "per_element_vibration_scan"),
        exported_object_name="DetectorAtFocus",
        showplot=False,
        saveplot=True,
    )
