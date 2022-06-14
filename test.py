from RayPyNG import runner

r = runner.RayUIRunner()
a = runner.RayUIAPI(r)

r.run()

a.load("test")