## Project Description
raypyng provides a simple API to work with RAY-UI, a software for optical simulation of synchrotron beamlines and x-ray systems developed by Helmholtz-Zentrum Berlin.

raypyng works only under linux distributions.


## Install RAY-UI

Download the RAY-UI installer from https://www.helmholtz-berlin.de/forschung/oe/wi/optik-strahlrohre/arbeitsgebiete/ray_en.html, and run the installer.


## Install xvfb 
xvfb is a virtual X11 framebuffer server that let you run RAY-UI headless

Install xvfb:
```
sudo apt install xvfb
```

Note: xvfb-run script is a part of the xvfb distribuion and runs an app on a new virtual X11 server

## Install raypyng
```
pip install raypyng
```