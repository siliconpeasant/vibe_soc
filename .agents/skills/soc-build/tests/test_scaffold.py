from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "soc_project_init.py"
SPEC = importlib.util.spec_from_file_location("soc_project_init", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScaffoldTest(unittest.TestCase):
    def test_canonical_project_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(MODULE.init_project("demo_soc", tmp, "demo_top"), 0)
            root = Path(tmp) / "demo_soc"
            self.assertTrue((root / "chip/top/de/rtl/demo_top.v").is_file())
            self.assertFalse((root / "chip/top/de/rtl/top.v").exists())
            for directory in (
                "docs",
                "de/rtl",
                "de/lint",
                "de/cdc",
                "de/syn",
                "de/formal",
                "de/run",
                "dv/tb",
                "dv/verif",
                "dv/tests",
                "dv/sim",
                "dv/cov",
            ):
                self.assertTrue((root / "chip/top" / directory).is_dir(), directory)
            self.assertEqual(
                (root / "chip/top/de/rtl/filelist.f").read_text(),
                "$SOC/chip/top/de/rtl/demo_top.v\n",
            )
            self.assertTrue((root / "ip/digital/template_ip/de/rtl/filelist.f").is_file())
            self.assertTrue((root / "ip/digital/template_ip/docs").is_dir())
            self.assertTrue((root / "scripts/paths.mk").is_file())
            self.assertTrue((root / "scripts/config.mk").is_file())
            self.assertTrue((root / "scripts/local.mk.example").is_file())
            self.assertTrue((root / "scripts/validate_filelist.py").is_file())
            self.assertTrue((root / "scripts/build_fingerprint.py").is_file())
            self.assertTrue((root / "scripts/run_regression.py").is_file())
            self.assertTrue((root / "scripts/toolchains/vcs.mk").is_file())
            self.assertFalse((root / "scripts/local.mk").exists())
            readme = (root / "README.md").read_text()
            self.assertIn("de/       # rtl/lint/cdc/syn/formal/run", readme)
            self.assertNotIn("template_ip/  # IP 模板示例 (可独立编译仿真)\n│           ├── rtl/", readme)
            project_contract = (root / "CLAUDE.md").read_text()
            self.assertIn("`doc -> rtl -> {verif, syn}`", project_contract)
            self.assertNotIn("`rtl/` + `constraints/`", project_contract)
            self.assertIn("include $(PROJECT_ROOT)/scripts/config.mk", (root / "Makefile").read_text())
            common = (root / "scripts/common.mk").read_text()
            self.assertIn("include $(PROJECT_ROOT)/scripts/paths.mk", common)
            self.assertIn("include $(PROJECT_ROOT)/scripts/config.mk", common)
            self.assertIn("comp: $(CANONICAL_FLIST)", common)
            self.assertIn("sim:\n", common)
            config = (root / "scripts/config.mk").read_text()
            self.assertIn(".SHELLFLAGS := -o pipefail -c", config)
            module_make = (root / "chip/top/Makefile").read_text()
            self.assertIn("MODULE_NAME   = demo_top", module_make)
            self.assertIn("RTL_TOP       = demo_top", module_make)
            self.assertIn("include $(PROJECT_ROOT)/scripts/common.mk", module_make)
            self.assertNotIn("lint.log || true", module_make)

    def test_add_chip_creates_rtl_and_filelist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            MODULE.init_project("demo_soc", tmp, "demo_top")
            root = Path(tmp) / "demo_soc"
            self.assertEqual(MODULE.add_chip_module("dma", root), 0)
            self.assertTrue((root / "chip/dma/de/rtl/dma.v").is_file())
            self.assertTrue((root / "chip/dma/de/lint").is_dir())
            self.assertTrue((root / "chip/dma/de/cdc").is_dir())
            self.assertTrue((root / "chip/dma/de/formal").is_dir())
            self.assertTrue((root / "chip/dma/docs").is_dir())
            self.assertEqual(
                (root / "chip/dma/de/rtl/filelist.f").read_text(),
                "$SOC/chip/dma/de/rtl/dma.v\n",
            )
            self.assertEqual(
                (root / "chip/dma/Makefile").read_text(),
                "# dma module\n"
                "PROJECT_ROOT ?= $(shell cd ../.. && pwd -P)\n"
                "MODULE_NAME   = dma\n"
                "include $(PROJECT_ROOT)/scripts/common.mk\n",
            )


if __name__ == "__main__":
    unittest.main()
