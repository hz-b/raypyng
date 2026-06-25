# rayx vs RAY-UI: known behavioural differences

This file tracks differences observed when comparing rayx and RAY-UI results on the
`test_dipole.rml` beamline (BESSY II dipole, 1.7 GeV, R = 4.35 m).
All differences listed here are **rayx limitations or bugs**, not postprocessing errors.

---

## 1. Dipole source FWHM — constant across energies in rayx

**Symptom:** `HorizontalFocusFWHM` and `VerticalFocusFWHM` at the Dipole element are
identical to 8 significant figures for every photon energy in rayx; RAY-UI values vary
by ~0.5–1% across energies.

| Engine | H-FWHM (mm) | V-FWHM (mm) | varies with energy? |
|--------|-------------|-------------|---------------------|
| RAY-UI | 0.123–0.143 | 0.076–0.092 | yes (~15 %) |
| rayx   | 0.12253     | 0.09155     | no (constant) |

**Root cause:** rayx samples the Dipole source using the static RML geometry parameters
(`sourceWidth`, `sourceHeight`, `horDiv`, `verEbeamDiv`) with a fixed random seed.
The same positions and directions are generated for every photon energy.
RAY-UI internally applies the Schwinger emission pattern, whose vertical opening angle
is energy-dependent (proportional to Ec / E at low energies), so the OY distribution at
the source exit varies with photon energy.

**Impact:** Dipole source FWHM cannot be compared between engines; rayx does not model
the energy-dependent emission cone of synchrotron radiation.

---

## 2. Energy bandwidth — constant in rayx, energy-proportional in RAY-UI

**Symptom:** `Bandwidth` at the Dipole is fixed at ~0.10 eV for all photon energies in
rayx; RAY-UI correctly scales it as 0.1 % of the photon energy.

| Photon energy (eV) | RAY-UI BW (eV) | rayx BW (eV) |
|--------------------|----------------|--------------|
| 200                | 0.198          | 0.100        |
| 700                | 0.698          | 0.100        |
| 1200               | 1.197          | 0.100        |
| 1700               | 1.699          | 0.100        |
| 2200               | 2.198          | 0.100        |

Expected value: `photonEnergy × 0.001` (from RML: `energySpread=0.1`,
`energySpreadUnit="%"`).

**Root cause:** rayx ignores the `energySpreadUnit="%"` field and treats `energySpread`
as an absolute value in eV. It therefore always spreads rays over a fixed ±0.05 eV
window regardless of the centre photon energy.

**Impact:** `Bandwidth` and any metric derived from it (`FluxPerMilPerBwPerc`,
`FluxPerMilPerBwAbs`) are wrong in rayx for all energies except the one where
0.1 % × E ≈ 0.1 eV (i.e. E ≈ 100 eV).

**Fix implemented in `RayXAPI.load()` via `_patch_source_params()`:**
Before loading the beamline, raypyng rewrites the per-simulation RML:

```python
spread_abs = photon_energy_eV * spread_pct / 100.0
oe.energySpread.cdata = f"{spread_abs:.6g}"
oe.energySpreadUnit._attributes["comment"] = "eV"
```

The unit comment is also changed to `"eV"` so that `postprocessing.extract_bw_from_source()`
returns `NaN` for the derived `FluxPerMilPerBw*` metrics (only handles `"%"`) instead of
applying the percentage formula to an already-absolute value and producing a nonsense result.
The primary `Bandwidth` column is unaffected — it is always computed from `_extract_fwhm`
of the actual ray EN data.

---

## 3. Surviving ray selection — stray light included without explicit filter

**Symptom:** Without filtering, the rays DataFrame returned by `rays_to_df()` at a given
element includes all rays that ever hit that element, regardless of the path they took.
At `DetectorAtFocus` this gives ~940k rows, of which only ~183k are primary-beam rays;
the rest are stray/scattered rays that arrived via shorter paths and inflate the spot size.

**Root cause:** rayx does not trace elements sequentially. Every ray-surface interaction
is recorded independently. A ray can reach the detector having bypassed one or more
optical elements.

**Fix implemented in `RayXAPI.export()` via `path_id` chain intersection:**
For an element with `object_id = idx`, raypyng selects only rays whose `path_id` appears
at **every** preceding element (object_id 0, 1, …, idx−1) as well as the target element:

```python
surviving = set(df.loc[df["object_id"] == idx, "path_id"])
for preceding in range(idx):
    surviving &= set(df.loc[df["object_id"] == preceding, "path_id"])
```

This yields the rays that traversed the complete optical path from source to target.
Verified counts at design energy (1500 eV, `test_dipole.rml`):

| Element        | Rays survived |
|----------------|---------------|
| Dipole (src)   | 1,000,000     |
| M1             |   698,001     |
| Premirror M2   |   648,674     |
| PG (grating)   |   233,056     |
| M3             |   193,235     |
| ExitSlit       |   193,232     |
| KB1_hor        |   182,814     |
| KB2_ver        |   182,811     |
| DetectorAtFocus|   182,811     |

**Residual discrepancy:** at strongly off-design energies (e.g. 200 eV and 2200 eV for a
beamline optimised at 1500 eV) the chain filter gives 0 surviving rays at the detector,
because the grating diffracts rays in the wrong direction and none reach the detector via
the full optical path. RAY-UI reports a small number of surviving rays (~50–85) at these
energies. The origin of this difference is not yet understood and is a candidate question
for the rayx development team.
