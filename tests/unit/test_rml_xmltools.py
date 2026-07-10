from __future__ import annotations

import sys
import types
from pathlib import Path
from textwrap import dedent

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
PACKAGE_DIR = SRC_DIR / "raypyng"
sys.path.insert(1, str(SRC_DIR))

if "raypyng" not in sys.modules:
    package = types.ModuleType("raypyng")
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules["raypyng"] = package

from raypyng.rml import RMLFile
from raypyng.xmltools import XmlElement
from raypyng.xmltools.dictionaries import sanitizeName


def _write_sample_rml(tmp_path: Path) -> Path:
    rml_path = tmp_path / "sample.rml"
    rml_path.write_text(
        dedent(
            """\
            <lab>
              <version>1.0</version>
              <beamline>
                <object name="Source" type="Undulator">
                  <param id="photonEnergy" enabled="T">1000</param>
                  <param id="numberRays" enabled="T">100000</param>
                </object>
                <object name="DetectorAtFocus" type="Detector">
                  <param id="worldPosition" enabled="F">
                    <x>0</x>
                    <y>0</y>
                    <z>10</z>
                  </param>
                </object>
              </beamline>
            </lab>
            """
        ),
        encoding="utf-8",
    )
    return rml_path


def _write_error_toggle_rml(tmp_path: Path) -> Path:
    rml_path = tmp_path / "error_toggles.rml"
    rml_path.write_text(
        dedent(
            """\
            <lab>
              <version>1.0</version>
              <beamline>
                <object name="MirrorOn" type="Mirror">
                  <param id="reflectivityType" comment="Derived by Material" enabled="T">1</param>
                  <param id="slopeError" comment="Yes" enabled="T">0</param>
                  <param id="alignmentError" comment="No" enabled="T">1</param>
                </object>
                <object name="MirrorOff" type="Mirror">
                  <param id="reflectivityType" comment="100%" enabled="T">0</param>
                  <param id="slopeError" comment="No" enabled="T">1</param>
                  <param id="alignmentError" comment="Yes" enabled="T">0</param>
                </object>
                <object name="SourceOnlyAlignment" type="Source">
                  <param id="alignmentError" comment="No" enabled="T">1</param>
                  <param id="photonEnergy" enabled="T">1000</param>
                </object>
                <object name="Detector" type="Detector">
                  <param id="photonEnergy" enabled="T">1000</param>
                </object>
              </beamline>
            </lab>
            """
        ),
        encoding="utf-8",
    )
    return rml_path


def test_xml_element_sanitizes_attribute_keys():
    element = XmlElement("object", {"data-field": "ok", "class": "primary"})

    assert element["data-field"] == "ok"
    assert element["class"] == "primary"
    assert element.attributes().original()["data-field"] == "ok"
    assert element.attributes().original()["class"] == "primary"
    assert sanitizeName("beam line:version-2") == "beamline_version_2"


def test_rmlfile_parses_and_serializes_round_trip(tmp_path: Path):
    rml_path = _write_sample_rml(tmp_path)

    rml = RMLFile(str(rml_path))

    assert rml.beamline.Source.photonEnergy.cdata == "1000"
    assert rml.beamline.Source.get_full_path() == "lab.beamline.Source"
    assert rml.beamline.DetectorAtFocus.worldPosition.z.cdata == "10"

    xml_text = rml.xml()
    assert '<object name="Source" type="Undulator">' in xml_text
    assert '<param id="photonEnergy" enabled="T">1000</param>' in xml_text

    roundtrip_path = tmp_path / "roundtrip.rml"
    roundtrip_path.write_text(xml_text, encoding="utf-8")
    roundtrip = RMLFile(str(roundtrip_path))

    assert [child["name"] for child in roundtrip.beamline.children()] == [
        "Source",
        "DetectorAtFocus",
    ]
    assert roundtrip.beamline.DetectorAtFocus["type"] == "Detector"


def test_rml_error_toggle_properties_read_expected_states(tmp_path: Path):
    rml = RMLFile(str(_write_error_toggle_rml(tmp_path)))

    assert rml.beamline.MirrorOn.reflectivity_enabled is True
    assert rml.beamline.MirrorOff.reflectivity_enabled is False
    assert rml.beamline.MirrorOn.slope_error_enabled is True
    assert rml.beamline.MirrorOn.alignment_error_enabled is False
    assert rml.beamline.MirrorOff.slope_error_enabled is False
    assert rml.beamline.MirrorOff.alignment_error_enabled is True


def test_rml_error_toggle_properties_write_comment_and_value(tmp_path: Path):
    rml = RMLFile(str(_write_error_toggle_rml(tmp_path)))

    rml.beamline.MirrorOn.reflectivity_enabled = False
    rml.beamline.MirrorOn.slope_error_enabled = False
    rml.beamline.MirrorOn.alignment_error_enabled = True

    assert rml.beamline.MirrorOn.reflectivityType.attributes()["comment"] == "100%"
    assert rml.beamline.MirrorOn.reflectivityType.cdata == "0"
    assert rml.beamline.MirrorOn.slopeError.attributes()["comment"] == "No"
    assert rml.beamline.MirrorOn.slopeError.cdata == "1"
    assert rml.beamline.MirrorOn.alignmentError.attributes()["comment"] == "Yes"
    assert rml.beamline.MirrorOn.alignmentError.cdata == "0"


def test_rml_error_toggle_properties_round_trip_and_update_only_supported_elements(tmp_path: Path):
    source_path = _write_error_toggle_rml(tmp_path)
    rml = RMLFile(str(source_path))

    for element in rml.beamline.children():
        if hasattr(element, "reflectivityType"):
            element.reflectivity_enabled = True
        if hasattr(element, "slopeError"):
            element.slope_error_enabled = True
        if hasattr(element, "alignmentError"):
            element.alignment_error_enabled = False

    roundtrip_path = tmp_path / "error_toggles_roundtrip.rml"
    roundtrip_path.write_text(rml.xml(), encoding="utf-8")
    roundtrip = RMLFile(str(roundtrip_path))

    assert roundtrip.beamline.MirrorOn.reflectivityType.attributes()["comment"] == "DerivedbyMaterial"
    assert roundtrip.beamline.MirrorOn.reflectivityType.cdata == "1"
    assert roundtrip.beamline.MirrorOff.reflectivityType.attributes()["comment"] == "DerivedbyMaterial"
    assert roundtrip.beamline.MirrorOff.reflectivityType.cdata == "1"
    assert roundtrip.beamline.MirrorOn.slopeError.attributes()["comment"] == "Yes"
    assert roundtrip.beamline.MirrorOn.slopeError.cdata == "0"
    assert roundtrip.beamline.MirrorOff.slopeError.attributes()["comment"] == "Yes"
    assert roundtrip.beamline.MirrorOff.slopeError.cdata == "0"
    assert roundtrip.beamline.MirrorOn.alignmentError.attributes()["comment"] == "No"
    assert roundtrip.beamline.MirrorOn.alignmentError.cdata == "1"
    assert roundtrip.beamline.SourceOnlyAlignment.alignmentError.attributes()["comment"] == "No"
    assert roundtrip.beamline.SourceOnlyAlignment.alignmentError.cdata == "1"
    assert roundtrip.beamline.Detector.photonEnergy.cdata == "1000"


def test_rml_error_toggle_properties_raise_for_unsupported_elements(tmp_path: Path):
    rml = RMLFile(str(_write_error_toggle_rml(tmp_path)))

    try:
        _ = rml.beamline.Detector.reflectivity_enabled
    except AttributeError as exc:
        assert "Detector" in str(exc)
        assert "reflectivityType" in str(exc)
    else:
        raise AssertionError("Expected AttributeError when reading unsupported reflectivityType")

    try:
        _ = rml.beamline.Detector.slope_error_enabled
    except AttributeError as exc:
        assert "Detector" in str(exc)
        assert "slopeError" in str(exc)
    else:
        raise AssertionError("Expected AttributeError when reading unsupported slopeError")

    try:
        rml.beamline.Detector.alignment_error_enabled = True
    except AttributeError as exc:
        assert "Detector" in str(exc)
        assert "alignmentError" in str(exc)
    else:
        raise AssertionError("Expected AttributeError when writing unsupported alignmentError")

    try:
        rml.beamline.Detector.reflectivity_enabled = True
    except AttributeError as exc:
        assert "Detector" in str(exc)
        assert "reflectivityType" in str(exc)
    else:
        raise AssertionError("Expected AttributeError when writing unsupported reflectivityType")
