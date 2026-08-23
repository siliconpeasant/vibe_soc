from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PublicEdaFlowContractTest(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_formal_is_generic_and_upf_is_optional(self) -> None:
        script = self.read("scripts/formal/formality_verify.tcl")
        self.assertIn("set use_upf", script)
        self.assertIn("FORMAL_REPORTS_READY", script)
        self.assertNotIn('expected top upf_dc_demo', script)
        self.assertNotIn("logic_rtl", script)

    def test_dc_formal_and_clp_share_rtl_f_without_filtering(self) -> None:
        dc = self.read("scripts/syn/dc_upf_synth.tcl")
        formal = self.read("scripts/formal/formality_verify.tcl")
        clp = self.read("scripts/clp/clp_rtl_upf_check.tcl")
        config = self.read("scripts/config.mk")
        common = self.read("scripts/common.mk")
        module_make = self.read("ip/digital/upf_dc_demo/Makefile")
        self.assertIn('set analyze_options "-f $filelist"', dc)
        self.assertIn("analyze -format sverilog -vcs $analyze_options", dc)
        vc_common = self.read("scripts/vc_static/vc_flow_common.tcl")
        self.assertIn('set analyze_vcs "-f $prepared $vcs_opts"', vc_common)
        self.assertIn("analyze -format $format -vcs $analyze_vcs", vc_common)
        self.assertIn("LINT_TOOL ?= verilator", config)
        self.assertIn("CDC_TOOL            ?= spyglass", config)
        self.assertIn("VC_LINT_GATE", config)
        self.assertIn("DFT_TOOL            ?= vc_static", config)
        self.assertIn("RTL_SYNTHESIS_DEFINE ?= SYNTHESIS", config)
        self.assertIn('DC_RTL_DEFINE="$(DC_RTL_DEFINE)"', common)
        self.assertIn('FM_RTL_DEFINE="$(FORMAL_RTL_DEFINE)"', common)
        self.assertIn('CLP_RTL_DEFINE="$(CLP_RTL_DEFINE)"', common)
        self.assertIn("DC_NETLIST       ?=", common)
        self.assertIn("DC_NETLIST   :=", module_make)
        plain_dc = self.read("scripts/syn/dc_synth.tcl")
        self.assertIn("compile_transcript.rpt", plain_dc)
        self.assertIn("compile transcript contains an error diagnostic", plain_dc)
        self.assertIn("Design Compiler log contains an Error diagnostic", common)
        for script in (dc, formal, clp):
            self.assertNotIn("logic_rtl.f", script)
            self.assertNotIn("upf_dc_demo_(pll_macro", script)
            self.assertIn("SYNTHESIS", script)
        self.assertIn("lappend reference_read_args -f $filelist", formal)
        self.assertIn("lappend read_args -f $filelist -noelaborate", clp)

    def test_shared_filelist_check_accepts_tool_native_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            filelist = temp / "rtl.f"
            filelist.write_text(
                "// canonical\n"
                "+incdir+/does/not/need/reparse\n"
                "-y /native/tool/library\n"
                "-v /native/tool/cells.v\n"
                "/native/tool/design.sv\n",
                encoding="utf-8",
            )
            driver = temp / "check.tcl"
            driver.write_text(
                f"source {{{ROOT / 'scripts/tcl/flow_common.tcl'}}}\n"
                f"flow::require_filelist {{{filelist}}}\n"
                'puts "FILELIST_OK"\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                ["tclsh", str(driver)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FILELIST_OK", result.stdout)

    def test_common_make_owns_formal_and_clp_targets(self) -> None:
        common = self.read("scripts/common.mk")
        self.assertIn("formal-upf: formal", common)
        self.assertIn("clp-upf:\n", common)
        self.assertIn("rdc: $(RTL_FLIST)", common)
        self.assertIn("dft: $(RTL_FLIST)", common)
        self.assertIn("VC_LINT_GATE", common)
        self.assertIn("VC_DFT_GATE", common)
        root_make = self.read("Makefile")
        self.assertIn("verdi lint cdc rdc dft syn formal formal-upf clp-upf", root_make)
        module_make = self.read("ip/digital/upf_dc_demo/Makefile")
        self.assertIn("scripts/syn/dc_upf_synth.tcl", module_make)
        self.assertFalse(
            (ROOT / "ip/digital/upf_dc_demo/de/syn/formal/formality_upf_verify.tcl").exists()
        )

    def test_iverilog_is_not_a_supported_backend(self) -> None:
        config = self.read("scripts/config.mk")
        server = self.read(".agents/skills/soc-build/mcp_server.py")
        self.assertIn("SUPPORTED_SIMULATORS := verilator vcs xcelium", config)
        self.assertIn('SIMULATOR ?= verilator', config)
        self.assertNotIn('"iverilog", "vcs"', server)
        self.assertFalse((ROOT / "scripts/toolchains/iverilog.mk").exists())

    def test_verilator_timeout_is_fail_closed(self) -> None:
        harness = self.read("scripts/verilator/generic_main.cpp")
        config = self.read("scripts/config.mk")
        toolchain = self.read("scripts/toolchains/verilator.mk")
        self.assertIn("VERILATOR_TIMEOUT", harness)
        self.assertIn("return 2;", harness)
        self.assertIn("VERILATOR_TIMING_MODE", config)
        self.assertNotIn("VERILATOR_TIMING_SUPPORTED := $(shell", config)
        self.assertIn("VERILATOR_REQUIRE_TIMING", toolchain)
        self.assertIn('timing_flags="--timing"', toolchain)
        self.assertIn("+max_cycles=$(VERILATOR_MAX_CYCLES)", toolchain)
        self.assertIn("verilator_timing=$(VERILATOR_TIMING_MODE)", self.read("scripts/common.mk"))

    def test_project_template_exposes_public_eda_flow(self) -> None:
        template = ROOT / ".agents/skills/soc-build/templates/project"
        common = (template / "scripts/common.mk").read_text(encoding="utf-8")
        root_make = (template / "Makefile").read_text(encoding="utf-8")
        self.assertIn("formal-upf: formal", common)
        self.assertIn("clp-upf:\n", common)
        self.assertIn("syn-artifacts:\n", common)
        self.assertIn("rdc: $(RTL_FLIST)", common)
        self.assertIn("dft: $(RTL_FLIST)", common)
        self.assertIn("verdi lint cdc rdc dft syn formal formal-upf clp-upf", root_make)
        config = (template / "scripts/config.mk").read_text(encoding="utf-8")
        self.assertIn("LINT_TOOL ?= verilator", config)
        self.assertIn("CDC_TOOL            ?= spyglass", config)
        for relative in (
            "scripts/syn/dc_synth.tcl",
            "scripts/syn/dc_upf_synth.tcl",
            "scripts/formal/formality_verify.tcl",
            "scripts/clp/clp_rtl_upf_check.tcl",
            "scripts/tcl/flow_common.tcl",
            "scripts/lint/vc_lint.tcl",
            "scripts/cdc/vc_cdc.tcl",
            "scripts/rdc/vc_rdc.tcl",
            "scripts/dft/vc_dft.tcl",
            "scripts/vc_static/vc_flow_common.tcl",
        ):
            self.assertTrue((template / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
