from __future__ import annotations

from pathlib import Path
from textwrap import dedent

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
