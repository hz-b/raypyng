# Change Log
All notable changes to this project will be documented in this file.

## [1.4.3] - 23-June-2026

### Added
- **rayx engine support (experimental)**: `Simulate` now accepts `engine="rayx"` to use the rayx GPU ray-tracer as a drop-in alternative to RAY-UI. Install with `pip install raypyng[rayx]`.
- **graxpy grating efficiency**: optional RCWA-based diffraction efficiency via `graxpy_efficiency=True` on `Simulate`. Applied automatically to elements at and after the first grating. Install with `pip install raypyng[graxpy]`.
- `Intensity2D` added to the list of recognised RAY-UI export types.
- Version regression testing infrastructure: `tools/test_versions.sh`, `tests/functional/`, `tests/conftest.py` — run stable vs development RAY-UI comparisons with a single command.
- Unit tests for `PostProcess` helper methods and export validation (no RAY-UI required).
- `tools/bootstrap.sh` to create a `.venv` with uv + Python 3.12 and install dev dependencies.

### Changed
- `_execute_simulations` pre-check is now **2.2× faster**: replaced per-simulation `os.path.exists` calls (O(N × exports)) with a single `os.scandir` per round via `_missing_simulations_for_round`.
- Beamwaist tracing vectorised and parallelised across elements — significantly faster for multi-element beamlines.
- macOS support hardened: `xvfb-run` skipped on Darwin, RAY-UI binary path corrected (`Ray-UI.app/Contents/MacOS/Ray-UI`), SIGKILL escalation avoided (prevents crash-reporter dialogs), longer SIGTERM timeout (30 s).
- `cleanup_child_processes` now targets only RAY-UI/Xvfb processes, leaving Python's `resource_tracker` and executor workers untouched.
- Documentation: copy-pasteable examples, parameter guide, FAQ, and runtime tables added to the tutorial; simulations on Windows noted as unsupported.
- Example scripts: fixed path handling, added `__main__` guards, removed stale references.

### Fixed
- `_write_rml`: used bare folder name (`_sim_folder`) instead of full path (`sim_path`), causing RML files to be written to the wrong location.
- macOS multiprocessing spawn error fixed by using `fork` context on Darwin.
- Beamwaist `log(0)` warning silenced; example guard hardened.
- Example scripts with broken paths or missing `__main__` guards corrected.

## [1.4.1/2] - 18-May-2026

### Added
- Add regression test for mixed export-pair handling in raypyng analysis (`tests/test_raypyng_analysis_export_mismatch.py`).

### Changed

### Fixed
- Fix raypyng post-processing to respect exact `(object, export_type)` pairs configured in `sim.exports`.
- Prevent false cartesian-product lookups that required unrequested files (for example `M1_hor_foc_RawRaysIncoming.csv` when only outgoing was requested).
- Generate recap/dataframe and analysis metadata using configured export pairs only.
- Raise clear missing-file errors only for truly configured-but-missing analysis outputs.

## [1.4.0] - 16-April-2026

### Added
- Add `HorizontalDivergenceFWHM` and `VerticalDivergenceFWHM` to raypyng-analyzed outputs, computed from the ray direction vectors and exported in degrees.
- Add a shared `raypyng_analysis_metadata.json` sidecar file with the units of the analyzed output columns.
- Add `multiprocessing="auto"` and `multiprocessing="max"` modes to `Simulate.run()`.

### Changed
- Update examples to use `multiprocessing="auto"` instead of hardcoded worker counts.
- Update tutorial and how-to documentation to reflect the current simulation output structure, analyzed files, recap files, metadata sidecar, and multiprocessing options.
- Clean up several example scripts and fix stale file references and misleading comments.

### Fixed
- Fix a severe multiprocessing shutdown bug where simulations could finish writing outputs but the Python process could still hang during executor teardown.
- Prevent recursive retry of missing simulations while a previous `ProcessPoolExecutor` is still active.
- Handle unfinished futures more safely during shutdown, avoiding blocking exit when output files are already present.
- Fix postprocessing aggregation across repeated rounds by matching analyzed files by simulation index instead of file order.
- Ignore stale out-of-range analyzed files from previous runs during recap aggregation and final output checks.
- Reduce child-process cleanup output to a single terminal message instead of one line per PID.

## [1.3.53] - 26-January-2026

### Added
- Added analytical computation of the CFF required to maintain a fixed focus position when scanning photon energy with a plane VLS grating.
￼
### Changed

### Fixed

## [1.3.52] - 4-December-2025

### Added

### Changed

### Fixed
- Prevent simulations to stop if not simulations duration is available
 
 
## [1.3.51] - 18-August-2025
### Added

### Changed

### Fixed
- Revert Flux calculation, do not normalize to 0.1% source bandwidth

## [1.3.5] - 15-August-2025
### Added

### Changed

### Fixed
- Fix flux calculation

## [1.3.4] - 14-August-2025
### Added

### Changed

### Fixed
- issue [#60](https://github.com/hz-b/raypyng/issues/60), check that rayui.sh exists and it is executable, if not throw an Exception

## [1.3.3] - 13-August-2025
### Added
- VLS grating parameter calculations (beta)
### Changed
- add source bandwidth to results of raypyng analysis
- Normalize flux to 0.1% bandwidth
### Fixed


## [1.3.2] - 24-June-2025
### Added
- report center of rays in the recap file

### Changed

### Fixed


## [1.3.1] - 23-June-2025
### Added

### Changed

### Fixed
- Bug in dipole flux calculations


## [1.2.914] - 16-May-2025
### Added
- add slope_error and alignment_error functions to Simulate class, to switch on and off slope errors and alignment errors on all elements.
### Changed

### Fixed
- errors in formatting docstrings for readthedocs


## [1.2.913] - 13-May-2025
### Added
- add precommit, with black and ruff
- add possibility to multiply the results for an arbitrary efficiency, and relative example
### Changed

### Fixed
- issue [#46](https://github.com/hz-b/raypyng/issues/46), RawRaysOutgoing and RawRaysIncoming recap files were created even if not requested by the user, and even if individual files were not exported.



## [1.2.912] - 25-Feb-2025
### Added

### Changed

### Fixed
- xvfb and child process of the simulations were hanging once the simulations were finished, blocking RAM. Cleanup functions are added to prevent this.



## [1.2.911] - 05-Feb-2025
### Added

### Changed

### Fixed
- fix pandas version to 2.1.4 to avoid warnings
- remove debug print statements



## [1.2.910] - 2025-02-05
### Added
- it is now possible to load an undulator table in the form of a pandas dataframe. 
  - The dataframe should have, for each harmonic, one column for the energy and one for the number of photons produced. 
  - For instance, for the third harmonic the columns should be named `Energy3[eV]` and `Photons3`
  - If raypyng analysis is active, the resulting number of photons will be calculated for each harmonic
- add an example to show how to work with the undulator table, see `example_simulation_noanalyze_undulator.py`

### Changed
- RayProperties now uses pandas instead of numpy arrays. The recap files are exported only as `.csv` files, the `.dat` files are now deleted after they have been merged (and they were incomplete, as they are only an intermediate step).
 
### Fixed
- fixed postprocessing for undulator file beamlines, the bug was introduced with 1.2.900
- issue [#38](https://github.com/hz-b/raypyng/issues/38), [#39](https://github.com/hz-b/raypyng/issues/39)


### Fixed
- issue [#29](https://github.com/hz-b/raypyng/issues/29), Simulate.params used to throw an error when attempting list step-wise operation.



## [1.2.900] - 03-Feb-2025
### Added
 - When raypyng analyzes the results, if the number of photons is available, it calculates the **current generated in a AXUV or a GaAsP diode**. Pull Request [#32](https://github.com/hz-b/raypyng/pull/32)
 - Added **options to save space on disk** via pull request [#34](https://github.com/hz-b/raypyng/pull/34). If raypyng is doing the analysis, it means that RawRays files are exported, which can be pretty large. This pull request introduces the following changes:
   - individual analyzed rays files are deleted once they have been summarized
   - when running the simulations it is now possible to set the following two parameters in the run method:
    - remove_rawrays (bool, optional): removes RawRaysIncoming and RawRaysOutgoing files, if present. 
    - remove_round_folders (bool, optional): remove the round folders after the simulations are done.

### Changed
 
### Fixed
- issue [#29](https://github.com/hz-b/raypyng/issues/29), Simulate.params used to throw an error when attempting list step-wise operation.


