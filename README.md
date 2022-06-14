## installation

1. Initialize virtual env:
```
python3 -m venv .venv
```

2. activate venv

3. install dependencies:

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
