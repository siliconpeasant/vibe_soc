#!/usr/bin/env python3
"""Unit tests for xml2yml / ipxact2yml."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / ".agents" / "skills" / "xml2yml"
SCRIPTS = SKILL / "scripts"
YML2REG_SCRIPTS = ROOT / ".agents" / "skills" / "yml2reg" / "scripts"
REFS = SKILL / "references"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Xml2YmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SCRIPTS))
        sys.path.insert(0, str(YML2REG_SCRIPTS))
        cls.xml2yml = _load("xml2yml_mod", SCRIPTS / "xml2yml.py")
        cls.yml_model = _load("yml_model_mod", YML2REG_SCRIPTS / "yml_model.py")
        cls.yml2xml = _load("yml2xml_mod", YML2REG_SCRIPTS / "yml2xml.py")

    def test_project_spirit_reference(self) -> None:
        models = self.xml2yml.xml_to_models(REFS / "demo_spirit.xml")
        self.assertEqual(len(models), 1)
        m = models[0]
        self.assertEqual(m["name"], "DEMO_SYS_CTRL")
        self.assertEqual(m["protocol"], "apb")
        names = [r["name"] for r in m["registers"]]
        self.assertEqual(names, ["version", "ctrl", "scratch", "status"])
        self.assertEqual(len(m.get("interrupts") or []), 1)
        self.assertEqual(m["interrupts"][0]["name"], "err_irq")
        # lock field preserved
        ctrl = next(r for r in m["registers"] if r["name"] == "ctrl")
        soft = next(f for f in ctrl["fields"] if f["name"] == "soft_rst")
        self.assertEqual(soft["lock_lsb"], 16)
        self.assertEqual(soft["lock_bits"], 1)
        self.assertEqual(soft["lock_value"], "0x1")

    def test_ieee_ipxact_reference(self) -> None:
        models = self.xml2yml.xml_to_models(REFS / "demo_ipxact.xml")
        self.assertEqual(len(models), 1)
        m = models[0]
        self.assertEqual(m["name"], "DEMO_IPXACT_UART")
        self.assertEqual([r["name"] for r in m["registers"]], ["ctrl", "status"])
        enable = m["registers"][0]["fields"][0]
        self.assertEqual(enable["name"], "enable")
        self.assertEqual(enable["access"], "rw")
        self.assertEqual(enable["reset"], "0x1")  # sliced from reg reset
        busy = m["registers"][1]["fields"][0]
        self.assertEqual(busy["access"], "ro")

    def test_roundtrip_yml2xml_xml2yml(self) -> None:
        src_yml = ROOT / ".agents" / "skills" / "yml2reg" / "references" / "demo_docs.yml"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            model = self.yml_model.load_yml_model(src_yml)
            xml_path = tmp_path / "roundtrip.xml"
            xml_path.write_text(self.yml2xml.generate_xml(model), encoding="utf-8")
            out = self.xml2yml.convert_file(xml_path, str(tmp_path / "out"))
            self.assertEqual(len(out), 1)
            back = self.yml_model.load_yml_model(out[0])
            self.assertEqual(back["component_name"], model["component_name"])
            self.assertEqual(len(back["registers"]), len(model["registers"]))
            self.assertEqual(len(back["interrupts"]), len(model["interrupts"]))
            for a, b in zip(model["registers"], back["registers"]):
                self.assertEqual(a["name"], b["name"])
                self.assertEqual(int(a["offset"], 0), int(b["offset"], 0))
                self.assertEqual(len(a["fields"]), len(b["fields"]))
                for fa, fb in zip(a["fields"], b["fields"]):
                    self.assertEqual(fa["name"], fb["name"])
                    self.assertEqual(fa["bit_offset"], fb["bit_offset"])
                    self.assertEqual(fa["bit_width"], fb["bit_width"])
                    self.assertEqual(fa["access"].lower(), fb["access"].lower())

    def test_cli_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rc = self.xml2yml.main(
                [str(REFS / "demo_ipxact.xml"), "-o", str(tmp_path), "--protocol", "apb"]
            )
            self.assertEqual(rc, 0)
            ymls = list(tmp_path.glob("*.yml"))
            self.assertEqual(len(ymls), 1)
            text = ymls[0].read_text(encoding="utf-8")
            self.assertIn("name: DEMO_IPXACT_UART", text)
            self.assertIn("protocol: apb", text)


if __name__ == "__main__":
    unittest.main()
