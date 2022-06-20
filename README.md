## installation

0. Install python3:

```
sudo apt install python3 python3-venv python3-wheel -y
```

or  (I still need to check ...)

```
sudo apt-get install python3-dev python3-pip python3-venv python3-wheel -y
```

1. Initialize virtual env:
```
python3 -m venv .venv
```

2. activate venv

3. install dependencies:

```
python3 -m pip install wheel
```


```
python3 -m pip install numpy matplotlib lxml ipython psutil
```

4. Install ray:

4.1 Install dependencies:
```
sudo apt install libxkbcommon0 libharfbuzz0b libxcb-render0
```

4.2 Intall ray
Download ray installer from https://www.helmholtz-berlin.de/forschung/oe/wi/optik-strahlrohre/arbeitsgebiete/ray_en.html. 
And run the installer...

4.3 History of resolving dependency issues:

Issue with the installer: missing `libxkbcommon.so.0`, searching solution:
```
lservice@ubjl-builder-01:~/projects/ray$ apt-file search libxkbcommon.so
libxkbcommon-dev: /usr/lib/x86_64-linux-gnu/libxkbcommon.so
libxkbcommon0: /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0
libxkbcommon0: /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0.0.0
```

Issue with rayui: missing `libharfbuzz.so.0`, search solution:
libharfbuzz-dev: /usr/lib/x86_64-linux-gnu/libharfbuzz.so
libharfbuzz0b: /usr/lib/x86_64-linux-gnu/libharfbuzz.so.0
libharfbuzz0b: /usr/lib/x86_64-linux-gnu/libharfbuzz.so.0.20600.4

rayui crashing with `Abort(core dumed)`

looking up: `ldd rayui` - seems to be OK
looking up libs: `ldd lib*` : we got `libxcb-render.so.0 not found`
```
lservice@ubjl-builder-01:~/projects/ray$ apt-file search libxcb-render
libxcb-render-util0: /usr/lib/x86_64-linux-gnu/libxcb-render-util.so.0
libxcb-render-util0: /usr/lib/x86_64-linux-gnu/libxcb-render-util.so.0.0.0
libxcb-render-util0: /usr/share/doc/libxcb-render-util0/NEWS.gz
libxcb-render-util0: /usr/share/doc/libxcb-render-util0/README
libxcb-render-util0: /usr/share/doc/libxcb-render-util0/changelog.Debian.gz
libxcb-render-util0: /usr/share/doc/libxcb-render-util0/copyright
libxcb-render-util0-dev: /usr/lib/x86_64-linux-gnu/libxcb-render-util.a
libxcb-render-util0-dev: /usr/lib/x86_64-linux-gnu/libxcb-render-util.so
libxcb-render-util0-dev: /usr/share/doc/libxcb-render-util0-dev/NEWS.gz
libxcb-render-util0-dev: /usr/share/doc/libxcb-render-util0-dev/README
libxcb-render-util0-dev: /usr/share/doc/libxcb-render-util0-dev/changelog.Debian.gz
libxcb-render-util0-dev: /usr/share/doc/libxcb-render-util0-dev/copyright
libxcb-render0: /usr/lib/x86_64-linux-gnu/libxcb-render.so.0
libxcb-render0: /usr/lib/x86_64-linux-gnu/libxcb-render.so.0.0.0
libxcb-render0: /usr/share/doc/libxcb-render0/changelog.Debian.gz
libxcb-render0: /usr/share/doc/libxcb-render0/copyright
libxcb-render0-dev: /usr/lib/x86_64-linux-gnu/libxcb-render.a
libxcb-render0-dev: /usr/lib/x86_64-linux-gnu/libxcb-render.so
libxcb-render0-dev: /usr/share/doc/libxcb-render0-dev/changelog.Debian.gz
libxcb-render0-dev: /usr/share/doc/libxcb-render0-dev/copyright
```
libxcb-render0 seems to be the answer ....

NOW IT WORKS!!!


5. Headless run (removing those annoying flashing windows...)

5.1 Using `xvfb`

xvfb is a virtual X11 framebuffer server.

Install xvfb:
```
sudo apt install xvfb
```

Modify ray to use xvfb:
```python
    # set the ray location, substitute the '...'
    #(pay attention to the slashes, the first and last one must be there)
    ray_loc = "xvfb-run "+path_to_RAY+"/rayui.sh"
```
Note: xvfb-run script is a part of the xvfb distribuion and runs an app on a new virtual X11 server



6. What we want to have for the Rml file processing:

Simple access like:

```ipython
# load template and be ready to save to mybeamline.rml
bl = RmlFile('mybeamline.rml', template='rml/beamline.rml')

# modify some parameter
bl.Screen2.distanceImagePlane = 4348.5

# modify another parameter (note that original rml object name has spaces)
bl.SimpleUndulator.numberRays = 10000
# access rml level info:
print(bl.SimpleUndulator.rml().name)
"Simple Undulator"
print(bl.SimpleUndulator.rml().type)
"Simple Undulator"


# see some service information
print(bl.rml().version)  # Access to non-beamline parts of the rml file using rml() method
print(bl.rml().ExtraInfo)

# save the result
bl.save()


def setSourceDivergence(mrad):
    if bl.lab.beamline[0].type=="Dipole":
        bl.lab.beamline[0].sourceWidth = mrad*1000 # dipole param is in urads!
    elif bl.lab.beamline[0].type=="SimpleUndulator":
        bl.lab.beamline[0].sourceWidth = mrad
    else
        raise Exception("Unknonw source type")
```


7. Paramter setting API

Idea 1
```ipython
rml1.beamline.M1.inicidence.value = Range(1,5,points=21)
rml1.beamline.M1.inicidence.value = Range(lambda: random(1,5),points=21)
```

Idea 2
```ipython

Element(rml1.beamline.M2).Parameter("incidence",Range(lambda: random(1,5),points=21))
                         .Parameter("cff",5) # Always use 5 as a value
                         .Parameter("xpos", Range(1,5)) # number of points automatically linked to the first parameter

Element(rml1.beamline.M3).Parameter("incidence",Range(1,3,points=11))
```

idea3:
```ipython
params = [
            {rml1.beamline.M1.alpha:[1 2 3 4], rml1.beamline.M2.beta:[5 6 7 8]}}, # set two parameters: "alpha" and "beta" in a dependent way. 
            {rml1.beamline.M2.posX:0.1}, # set a value - in independed way
            {rml1.beamline.M2.posy:range(1,5,1)} # set a range of  values - in independed way
        ]

simulate(params)


with rml1.beamline:
    params = [
            {M1.alpha:[1 2 3 4], M2.beta:[5 6 7 8]}}, # set two parameters: "alpha" and "beta" in a dependent way. 
            {M2.posX:0.1}, # set a value - in independed way
            {M2.posY:range(1,5,1)} # set a range of  values - in independed way
        ]
```

idea4:
```python
# this can be used to set a value or a range of values
simulation.addIndependentParam(param=rml1.beamline.M1.alpha,                              value=[1,2,3,4])
# this can be used add dependent parameters
simulation.addDependentParam(param=rml1.beamline.M1.posY,    
                             values=[10,20,30,40],
                             dependency=rml.beamline.M1:alpha)
```
