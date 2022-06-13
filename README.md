## installation

1. Initialize virtual env:
```
python3 -m venv .venv
```

2. activate venv

3. install dependencies:

```
python3 -m pip install numpy matplotlib lxml ipython
```

4. ray dependencies:

libharfbuzz-dev: /usr/lib/x86_64-linux-gnu/libharfbuzz.so
libharfbuzz0b: /usr/lib/x86_64-linux-gnu/libharfbuzz.so.0
libharfbuzz0b: /usr/lib/x86_64-linux-gnu/libharfbuzz.so.0.20600.4


rayui crashed.... 

looking up: ldd rayui - OK
ldd lib* : libxcb-render not found
apt=-file search : found in package libxcb-render0

NOW IT WORKS!!!


5. Headless run:

Using xvfb: 

5.1 Install xvfb:
```
sudo apt install xvfb
```

Modify ray to use xvfb:
```python
    # set the ray location, substitute the '...'
    #(pay attention to the slashes, the first and last one must be there)
    ray_loc = "xvfb-run "+path_to_RAY+"/rayui.sh"
```
xvfb-run script is a part of the xvfb distribuion and runs an app on a new virtual X11 server
