# Change Log
All notable changes to this project will be documented in this file.

## [1.3.04] - 14-August-2025
### Added

### Changed

### Fixed
- issue [#60](https://github.com/hz-b/raypyng/issues/60), check that rayui.sh exists and it is executable, if not throw an Exception

## [1.3.03] - 13-August-2025
### Added
- VLS grating parameter calculations (beta)
### Changed
- add source bandwidth to results of raypyng analysis
- Normalize flux to 0.1% bandwidth
### Fixed


## [1.3.02] - 24-June-2025
### Added
- report center of rays in the recap file

### Changed

### Fixed


## [1.3.01] - 23-June-2025
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




