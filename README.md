# raypyng

raypyng is a Python interface for [RAY-UI](https://www.helmholtz-berlin.de/forschung/oe/wi/optik-strahlrohre/arbeitsgebiete/ray_en.html), the ray-tracing software developed at Helmholtz-Zentrum Berlin for synchrotron beamlines and X-ray optics.

It loads a beamline saved from RAY-UI as an `.rml` file, scans beamline parameters, runs traces in parallel, and post-processes the exported rays.

## Highlights

- Works on Linux, macOS, and Windows.
- Drives RAY-UI from Python through a simple simulation API.
- Supports parameter scans and parallel execution.
- Can post-process raw exported rays directly in raypyng.
- Includes automated unit, smoke, platform, and functional tests.
- Offers experimental `rayx` backend support.

## Installation

raypyng requires:

1. RAY-UI installed on your machine.
2. Python 3.10 or newer.

Install the Python package with:

```bash
python3 -m pip install --upgrade raypyng
```

For local development in this repository:

```bash
./tools/bootstrap.sh
```

On Windows PowerShell:

```powershell
.\tools\bootstrap_windows.ps1
.\.venv\Scripts\Activate.ps1
```

Notes:

- On Linux, `xvfb` is needed for headless RAY-UI execution.
- On macOS and Windows, `xvfb` is not needed.
- On Windows and macOS, put `sim.run(...)` under `if __name__ == "__main__":` when using multiprocessing.

## Quickstart

```python
import numpy as np
from raypyng import Simulate

if __name__ == "__main__":
    sim = Simulate("rml/dipole_beamline.rml", hide=True)
    beamline = sim.rml.beamline

    sim.params = [
        {beamline.Dipole.photonEnergy: np.arange(200, 2001, 200)},
    ]
    sim.exports = [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    sim.simulation_name = "quickstart"
    sim.analyze = False
    sim.raypyng_analysis = True

    sim.run(multiprocessing="auto", force=True)
```

This writes the simulation output into a `RAYPy_Simulation_quickstart` folder.

## Experimental rayx support

raypyng can also use [rayx](https://github.com/hz-b/rayx) as an experimental backend:

```bash
pip install "raypyng[rayx]"
```

The integration is still unstable and should be cross-checked against RAY-UI, especially for beamlines with diffraction gratings.

## Tests

The repository includes four kinds of automated tests:

- `unit`
- `smoke`
- `platform`
- `functional`

See [`tests/test.md`](tests/test.md) for setup and run commands.

## Documentation

- Full documentation: https://raypyng.readthedocs.io/en/latest/index.html
- Installation guide: https://raypyng.readthedocs.io/en/latest/installation.html
- Tutorial: https://raypyng.readthedocs.io/en/latest/tutorial.html
- Troubleshooting: https://raypyng.readthedocs.io/en/latest/troubleshooting.html
