"""Example: inspect a beamline layout with raypyng.inspect.

Builds two summary tables (all elements + mirrors/dipoles) from an RML file
and produces a 2D/3D layout plot — no RAY-UI installation required.
"""

from __future__ import annotations

import os
from pathlib import Path

from raypyng import build_tables, plot_beamline_views, save_tables

if __name__ == "__main__":
    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    rml_path = this_dir / "rml" / "dipole_beamline.rml"

    # ── build tables ──────────────────────────────────────────────────────────
    # mirror_name_pattern selects elements whose name starts with M + digits.
    # special_names adds the dipole source regardless of its name.
    mirror_table, beamline_table = build_tables(
        rml_path,
        mirror_name_pattern=r"^M\d+",
        special_names=("Dipole",),
    )

    print("=== Beamline elements ===")
    print(beamline_table.to_string(index=False))
    print()
    print("=== Mirrors / dipole ===")
    print(mirror_table.to_string(index=False))

    # ── save tables to CSV ────────────────────────────────────────────────────
    tables_dir = this_dir / "inspect_output" / "tables"
    mirror_path, beamline_path = save_tables(mirror_table, beamline_table, tables_dir)
    print(f"\nTables written to:\n  {mirror_path}\n  {beamline_path}")

    # ── plot layout ───────────────────────────────────────────────────────────
    plot_path = this_dir / "inspect_output" / "beamline_views.png"
    plot_beamline_views(
        beamline_table,
        mirror_table,
        output_path=plot_path,
        title="Dipole Beamline Layout",
        show_plot=False,
    )
    print(f"\nLayout plot saved to:\n  {plot_path}")
