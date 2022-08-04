from RayPyNG.simulate import Simulate
from RayPyNG.beamwaist import PlotBeamwaist 


sim = Simulate('examples/rml/high_energy_branch_flux_1200_test_beamwaist.rml',
                template='examples/rml/high_energy_branch_flux_1200_test_beamwaist.rml', 
                hide=True)
sim_folder = 'Beamwaist_test'

bw = PlotBeamwaist(sim_folder, sim)

energy = 500
nrays = 100000
bw.simulate_beamline(energy,nrays=nrays, force=False)


bw.define_hist(lim=20,step=.5)  # lim should be larger than max beam waist
bw.define_zstep(step_z=100)      # in mm, step in optical direction to trace RAYS
bw.reduce_Nrays(factor = 100)   # this reduces the n of rays by the factor you set

bw.trace_beamwaist(save_results=True)

bw.load_previous_results() # set the firs argument to true if you already saved the results of the trace


bw.change_name(new_name = 'Dip', pos=0)

xh,yh,x,y=bw.plot(save_img=True,img_name='high_energy_branch',extension='.png',show_img=True,annotate_OE=True, debug=False)

# xh,yh,x,y=bw.plot(save_img=True,img_name='high_energy_branch_zoom',extension='.png',show_img=False,annotate_OE=True,lim_top=[38.5,41.5,-3,3],lim_side=[38.5,41.5,-.7,.7])

# one can use xh,yh,x,y to buld his own plots:
# suggested usage: ax.pcolormesh(x,y,np.log(self.xh), cmap='inferno')


