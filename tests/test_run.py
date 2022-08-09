from src.raypyng import runner

r = runner.RayUIRunner(ray_path='/home/simone/RAY-UI-development_bk/')
a = runner.RayUIAPI(r)

r.run()

a.load('rml/beamline.rml')