# Change Log
All notable changes to this project will be documented in this file.

 
## [1.2.900] - 2025-02-03
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
 
