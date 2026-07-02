from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from raypyng.wave_helper import WaveHelper

DATA_WAVE = Path(__file__).resolve().parents[1] / "data" / "WAVE"


def _copy_wave_sample(tmp_path: Path) -> Path:
    wave_root = tmp_path / "WAVE"
    for harmonic, energies in {1: (100, 110), 3: (240, 270), 5: (400, 450)}.items():
        src_dir = DATA_WAVE / f"U49H{harmonic}allrayfiles"
        dst_dir = wave_root / f"U49H{harmonic}allrayfiles"
        dst_dir.mkdir(parents=True, exist_ok=True)
        for energy in energies:
            filename = f"U49H{harmonic}_{energy}eV_fo.dat"
            shutil.copy2(src_dir / filename, dst_dir / filename)
    return wave_root


def test_wave_helper_discovers_harmonics_and_energy_files(tmp_path: Path):
    wave_root = _copy_wave_sample(tmp_path)
    helper = WaveHelper(str(wave_root), harmonics=3, undulator="U49")

    helper.report_available_energies(verbose=False)

    assert helper._harmonic_to_folders_dict == {
        1: str(wave_root / "U49H1allrayfiles"),
        3: str(wave_root / "U49H3allrayfiles"),
        5: str(wave_root / "U49H5allrayfiles"),
    }
    assert helper._harmonic_to_energy_dict[3] == [240, 270]
    assert Path(helper.energies_to_file_dict[1][100]).name == "U49H1_100eV_fo.dat"


def test_wave_helper_converts_energy_lists_to_paths(tmp_path: Path):
    wave_root = _copy_wave_sample(tmp_path)
    helper = WaveHelper(str(wave_root), harmonics=3, undulator="U49")
    helper._explore_wave_folder()

    paths = helper.convert_energies_to_file_list(5, [400, 450])

    assert [Path(path).name for path in paths] == [
        "U49H5_400eV_fo.dat",
        "U49H5_450eV_fo.dat",
    ]
