"""Plot the beamwaist for the beamwaist example."""

import os

from raypyng.beamwaist import PlotBeamwaist
from raypyng.simulate import Simulate

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, '..', 'rml', 'dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim.path = this_file_dir
    sim_folder = 'Beamwaist'

    bw = PlotBeamwaist(sim_folder, sim)
    bw.directory = os.path.join(this_file_dir, bw.directory)

    bw.define_hist(lim=20, step=.5)
    bw.define_zstep(step_z=100)
    bw.reduce_Nrays(factor=1)

    # load the trace produced by simulation_beamwaist.py
    bw.load_previous_results()

    bw.change_name(new_name='Dip', pos=0)
    bw.change_name(new_name='Focus', pos=8)

    bw.plot(
        save_img=True,
        img_name='eval_beamwaist',
        extension='.png',
        show_img=False,
        annotate_OE=True,
        debug=False,
    )
    source_png = os.path.join(this_file_dir, 'RAYPy_Simulation_Beamwaist', 'eval_beamwaist.png')
    target_png = os.path.join(this_file_dir, 'eval_beamwaist.png')
    os.replace(source_png, target_png)
    print('Saved beamwaist plot:', target_png)
