from __future__ import annotations

"""
Manual check:
after running this script, open the generated RML files with RAY and verify
that reflectivity, alignment errors, and slope errors are ON in the
`*_enabled.rml` file and OFF in the `*_disabled.rml` file for each supported
element.
"""

from pathlib import Path
import sys
import types

SRC_DIR = Path(__file__).resolve().parents[3] / "src"
PACKAGE_DIR = SRC_DIR / "raypyng"
sys.path.insert(1, str(SRC_DIR))

if "raypyng" not in sys.modules:
    package = types.ModuleType("raypyng")
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules["raypyng"] = package

from raypyng.rml import RMLFile


THIS_DIR = Path(__file__).resolve().parent
SOURCE_RML = THIS_DIR.parent / "rml" / "dipole_beamline.rml"
ENABLED_OUTPUT = THIS_DIR / "dipole_beamline_errors_enabled.rml"
DISABLED_OUTPUT = THIS_DIR / "dipole_beamline_errors_disabled.rml"


def _supports_param(element, param_name: str) -> bool:
    return hasattr(element, param_name)


def _apply_toggles(rml: RMLFile, enabled: bool) -> dict[str, list[str]]:
    updated = {"reflectivityType": [], "slopeError": [], "alignmentError": []}

    for element in rml.beamline.children():
        if _supports_param(element, "reflectivityType"):
            element.reflectivity_enabled = enabled
            updated["reflectivityType"].append(element.resolvable_name())
        if _supports_param(element, "slopeError"):
            element.slope_error_enabled = enabled
            updated["slopeError"].append(element.resolvable_name())
        if _supports_param(element, "alignmentError"):
            element.alignment_error_enabled = enabled
            updated["alignmentError"].append(element.resolvable_name())

    return updated


def _write_variant(output_path: Path, enabled: bool) -> dict[str, list[str]]:
    rml = RMLFile(str(SOURCE_RML))
    updated = _apply_toggles(rml, enabled)
    rml.write(str(output_path))
    return updated


def _print_summary(output_path: Path, updated: dict[str, list[str]]) -> None:
    print(f"Saved: {output_path}")
    print(f"  reflectivity updated on: {', '.join(updated['reflectivityType']) or 'none'}")
    print(f"  slopeError updated on: {', '.join(updated['slopeError']) or 'none'}")
    print(f"  alignmentError updated on: {', '.join(updated['alignmentError']) or 'none'}")


def main() -> None:
    print(f"Source RML: {SOURCE_RML}")

    enabled_updates = _write_variant(ENABLED_OUTPUT, True)
    disabled_updates = _write_variant(DISABLED_OUTPUT, False)

    _print_summary(ENABLED_OUTPUT, enabled_updates)
    _print_summary(DISABLED_OUTPUT, disabled_updates)


if __name__ == "__main__":
    main()
