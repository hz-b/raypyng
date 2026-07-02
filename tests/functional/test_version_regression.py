"""Functional regression tests: compare stable vs development RAY-UI.

Both RAY-UI paths must be supplied via CLI options or environment variables —
see tests/conftest.py.  Tests are silently skipped when paths are absent.

Run with uv on Python 3.12:
    uv run --python 3.12 pytest tests/functional/ \
        --stable-ray-path=/path/to/RAY-UI \
        --dev-ray-path=/path/to/Ray-UI-development \
        -v
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from raypyng import Simulate

# RML shipped with the test suite — small, fast, known-good beamline
_RML = Path(__file__).parent.parent / "data" / "rml" / "dipole.rml"

# Metrics to compare and their per-metric tolerance multipliers.
# Final tolerance = base_tolerance * multiplier.
_METRICS = {
    "PercentageRaysSurvived": 1.0,
    "PhotonFlux": 1.0,
    "HorizontalFocusFWHM": 5.0,
    "VerticalFocusFWHM": 5.0,
    "Bandwidth": 2.0,
}


# ── helpers ───────────────────────────────────────────────────────────────────


def _run_sim(rml_path: Path, ray_path: str, sim_name: str, out_dir: Path, energies) -> pd.DataFrame:
    """Run a Simulate job and return the aggregated DetectorAtFocus CSV."""
    sim = Simulate(str(rml_path), hide=True, ray_path=ray_path)
    beamline = sim.rml.beamline
    sim.params = [{beamline.Dipole.photonEnergy: energies}]
    sim.exports = [{beamline.DetectorAtFocus: ["RawRaysOutgoing"]}]
    sim.simulation_name = sim_name
    out_dir.mkdir(parents=True, exist_ok=True)
    sim.path = str(out_dir)
    sim.analyze = False
    sim.raypyng_analysis = True
    sim.run(multiprocessing=1, force=True)
    csv = out_dir / f"RAYPy_Simulation_{sim_name}" / "DetectorAtFocus_RawRaysOutgoing.csv"
    df = pd.read_csv(csv, index_col=0)
    df.columns = df.columns.str.strip()
    return df


def _assert_metrics_close(
    df_stable: pd.DataFrame,
    df_dev: pd.DataFrame,
    base_tol: float,
    label: str = "",
) -> None:
    """Assert that every tracked metric is within tolerance at every row."""
    errors = []
    for metric, multiplier in _METRICS.items():
        if metric not in df_stable.columns or metric not in df_dev.columns:
            continue
        tol = base_tol * multiplier
        for i, (vs, vd) in enumerate(
            zip(df_stable[metric].values, df_dev[metric].values)
        ):
            if np.isnan(vs) and np.isnan(vd):
                continue
            denom = max(abs(float(vs)), 1e-30)
            rel_diff = abs(float(vs) - float(vd)) / denom
            if rel_diff > tol:
                errors.append(
                    f"  row {i}: {metric}: stable={vs:.6g}  dev={vd:.6g}"
                    f"  rel_diff={rel_diff:.3%}  tol={tol:.1%}"
                )
    if errors:
        header = f"Metric mismatch{' — ' + label if label else ''}:\n"
        pytest.fail(header + "\n".join(errors))


# ── single-energy test ────────────────────────────────────────────────────────


@pytest.mark.functional
def test_detector_metrics_stable_vs_dev(stable_ray_path, dev_ray_path, tolerance, tmp_path):
    """Run one energy point with both RAY-UI versions and compare detector metrics."""
    energy = np.array([500.0])

    df_stable = _run_sim(_RML, stable_ray_path, "stable", tmp_path / "stable", energy)
    df_dev = _run_sim(_RML, dev_ray_path, "dev", tmp_path / "dev", energy)

    _assert_metrics_close(df_stable, df_dev, tolerance, label="500 eV")


# ── multi-energy test (slow) ──────────────────────────────────────────────────


@pytest.mark.functional
@pytest.mark.slow
def test_detector_metrics_multi_energy(stable_ray_path, dev_ray_path, tolerance, tmp_path):
    """Run several energy points and compare detector metrics at each."""
    energies = np.array([200.0, 500.0, 1000.0, 1500.0, 2000.0])

    df_stable = _run_sim(_RML, stable_ray_path, "stable_multi", tmp_path / "stable", energies)
    df_dev = _run_sim(_RML, dev_ray_path, "dev_multi", tmp_path / "dev", energies)

    _assert_metrics_close(df_stable, df_dev, tolerance, label="multi-energy")


# ── sanity: output files exist ────────────────────────────────────────────────


@pytest.mark.functional
def test_output_files_created(stable_ray_path, dev_ray_path, tmp_path):
    """Both versions must produce the expected aggregated CSV and per-sim RMLs."""
    energy = np.array([500.0])

    for name, rpath in [("stable", stable_ray_path), ("dev", dev_ray_path)]:
        _run_sim(_RML, rpath, name, tmp_path / name, energy)
        sim_dir = tmp_path / name / f"RAYPy_Simulation_{name}"
        assert (sim_dir / "DetectorAtFocus_RawRaysOutgoing.csv").exists(), (
            f"{name}: aggregated CSV not found in {sim_dir}"
        )
        # At least one per-simulation RML must have been saved
        round_dir = sim_dir / "round_0"
        rmls = list(round_dir.glob("*.rml")) if round_dir.exists() else []
        assert rmls, f"{name}: no per-simulation RML found under {round_dir}"
