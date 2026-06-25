"""Example: inspect a beamline layout with raypyng.inspect."""

from __future__ import annotations

import os
from pathlib import Path

from raypyng import build_tables, save_tables, save_tables_xlsx

if __name__ == "__main__":
    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    rml_path = this_dir.parent / "rml" / "dipole_beamline_for_inspect.rml"

    beamline_table = build_tables(rml_path)

    print("=== Beamline elements ===")
    print(beamline_table.to_string(index=False))

    # ── save tables to CSV and XLSX ───────────────────────────────────────────
    tables_dir = this_dir / "inspect_output" / "tables"
    beamline_csv_path = save_tables(beamline_table, tables_dir)
    beamline_xlsx_path = save_tables_xlsx(beamline_table, tables_dir)
    print(f"\nTables written to:\n  {beamline_csv_path}\n  {beamline_xlsx_path}")
