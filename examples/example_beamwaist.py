import os

from raypyng.beamwaist import PlotBeamwaist
from raypyng.simulate import Simulate

if __name__ == '__main__':
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    rml_file = os.path.join(this_file_dir, 'rml/dipole_beamline.rml')

    sim = Simulate(rml_file, hide=True)
    sim_folder = 'Beamwaist'

    bw = PlotBeamwaist(sim_folder, sim)

    energy = 500
    nrays = 1000
    bw.simulate_beamline(energy, nrays=nrays, force=False)

    bw.define_hist(lim=20, step=.5)  # lim should be larger than max beam waist
    bw.define_zstep(step_z=100)      # in mm, step in optical direction to trace RAYS
    bw.reduce_Nrays(factor=1)        # this reduces the n of rays by the factor you set

    bw.trace_beamwaist(save_results=True)

    # set the first argument to True if you already saved the results of the trace
    bw.load_previous_results()

    bw.change_name(new_name='Dip', pos=0)
    bw.change_name(new_name='Focus', pos=8)

    xh, yh, x, y = bw.plot(
        save_img=True,
        img_name='high_energy_branch',
        extension='.png',
        show_img=True,
        annotate_OE=True,
        debug=False,
    )

    # one can use xh, yh, x, y to build custom plots:
    # suggested usage: ax.pcolormesh(x, y, np.log(self.xh), cmap='inferno')
