import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "src" / "raypyng"


def _load_inspect_module():
    package = types.ModuleType("raypyng")
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules["raypyng"] = package

    spec = importlib.util.spec_from_file_location("raypyng.inspect", PACKAGE_DIR / "inspect.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["raypyng.inspect"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


inspect_module = _load_inspect_module()
TABLE_COLUMNS = inspect_module.TABLE_COLUMNS
build_tables = inspect_module.build_tables
save_tables = inspect_module.save_tables
save_tables_xlsx = inspect_module.save_tables_xlsx


def test_build_tables_uses_expected_schema_and_na_values():
    rml_path = Path("examples/rml/dipole_beamline.rml")

    table = build_tables(rml_path)

    assert list(table.columns) == TABLE_COLUMNS
    assert len(table) == 9

    dipole_row = table.loc[table["name"] == "Dipole"].iloc[0]
    assert dipole_row["type"] == "Dipole"
    assert dipole_row["grazingIncAngle"] == "n.a."
    assert dipole_row["materialCoating1"] == "n.a."
    assert dipole_row["x"] == "0.00"
    assert dipole_row["y"] == "0.00"
    assert dipole_row["z"] == "0.00"

    m1_row = table.loc[table["name"] == "M1"].iloc[0]
    assert m1_row["grazingIncAngle"] == "1"
    assert m1_row["azimuthalAngle"] == "90"
    assert m1_row["totalWidth"] == "50"
    assert m1_row["totalLength"] == "1000"
    assert m1_row["materialCoating1"] == "Pt"
    assert m1_row["slopeErrorSag"] == "1.5"
    assert m1_row["slopeErrorMer"] == "0.5"
    assert m1_row["z"] == "12500.00"

    slit_row = table.loc[table["name"] == "ExitSlit"].iloc[0]
    assert slit_row["totalWidth"] == "50"
    assert slit_row["totalLength"] == "n.a."
    assert slit_row["slopeErrorSag"] == "n.a."
    assert slit_row["materialTopLayer"] == "n.a."


def test_build_tables_keeps_enabled_coating_values(tmp_path):
    rml_path = tmp_path / "enabled_coating.rml"
    rml_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<lab>
 <version>1.15</version>
 <beamline>
  <object name="Mcustom" type="Plane Mirror">
   <param id="grazingIncAngle" enabled="F">3.4</param>
   <param id="azimuthalAngle" enabled="T">180</param>
   <param id="totalWidth" enabled="T">25</param>
   <param id="totalLength" enabled="T">400</param>
   <param id="materialCoating1" enabled="T">Rh</param>
   <param id="thicknessCoating1" enabled="T">30</param>
   <param id="roughnessCoating1" enabled="T">0.2</param>
   <param id="materialCoating2" enabled="F">B4C</param>
   <param id="thicknessCoating2" enabled="F">5</param>
   <param id="roughnessCoating2" enabled="F">0.1</param>
   <param id="materialTopLayer" enabled="T">C</param>
   <param id="thicknessTopLayer" enabled="T">1.5</param>
   <param id="roughnessTopLayer" enabled="T">0.05</param>
   <param id="slopeErrorSag" enabled="T">0.3</param>
   <param id="slopeErrorMer" enabled="T">0.1</param>
   <param id="worldPosition" enabled="F">
    <x>1.0</x>
    <y>2.0</y>
    <z>3.0</z>
   </param>
  </object>
 </beamline>
</lab>
""",
        encoding="utf-8",
    )

    table = build_tables(rml_path)
    row = table.iloc[0]

    assert row["grazingIncAngle"] == "3.4"
    assert row["materialCoating1"] == "Rh"
    assert row["thicknessCoating1"] == "30"
    assert row["roughnessCoating1"] == "0.2"
    assert row["materialCoating2"] == "n.a."
    assert row["thicknessCoating2"] == "n.a."
    assert row["roughnessCoating2"] == "n.a."
    assert row["materialTopLayer"] == "C"
    assert row["thicknessTopLayer"] == "1.5"
    assert row["roughnessTopLayer"] == "0.05"
    assert row["x"] == "1.00"
    assert row["y"] == "2.00"
    assert row["z"] == "3.00"


def test_save_tables_writes_single_csv(tmp_path):
    table = pd.DataFrame([["A", "Type"] + ["n.a."] * 18], columns=TABLE_COLUMNS)

    beamline_path = save_tables(table, tmp_path)
    header = beamline_path.read_text(encoding="utf-8").splitlines()[0]

    assert beamline_path == tmp_path / "beamline_elements_table.csv"
    assert beamline_path.exists()
    assert not (tmp_path / "mirror_table.csv").exists()
    assert "grazingIncAngle [deg]" in header
    assert "totalWidth [mm]" in header
    assert "thicknessCoating1 [nm]" in header
    assert "slopeErrorMer [sec]" in header
    assert header.endswith("x [mm],y [mm],z [mm]")


def test_save_tables_xlsx_writes_single_workbook(tmp_path):
    table = pd.DataFrame([["A", "Type"] + ["n.a."] * 18], columns=TABLE_COLUMNS)

    beamline_path = save_tables_xlsx(table, tmp_path)

    assert beamline_path == tmp_path / "beamline_elements_table.xlsx"
    assert beamline_path.exists()
