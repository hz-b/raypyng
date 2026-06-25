from __future__ import annotations

import shutil
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
IMAGES_DIR = DOCS_DIR / "images"

ASSETS = {
    "00_raypyng.png": REPO_ROOT / "examples/00_raypyng/eval_raypyng.png",
    "02_dipole_demo.png": REPO_ROOT / "examples/02_dipole_demo/plot_dipole.png",
    "04_vls.png": REPO_ROOT / "examples/04_vls/vls_cff_vs_energy.png",
    "05_beamwaist.png": REPO_ROOT / "examples/05_beamwaist/eval_beamwaist.png",
    "08_external_undulator_flux_table.png": REPO_ROOT
    / "examples/08_external_undulator_flux_table/eval_external_undulator_flux_table.png",
}


def main():
    IMAGES_DIR.mkdir(exist_ok=True)

    for target_name, source_path in ASSETS.items():
        if not source_path.exists():
            raise FileNotFoundError(f"Missing example figure: {source_path}")
        shutil.copy2(source_path, IMAGES_DIR / target_name)
        print(f"copied {source_path} -> {IMAGES_DIR / target_name}")


if __name__ == "__main__":
    main()
