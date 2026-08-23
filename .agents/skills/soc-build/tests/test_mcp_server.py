from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().with_name("mcp_server.py")
if not MODULE_PATH.is_file():
    MODULE_PATH = Path(__file__).resolve().parents[1] / "mcp_server.py"
SPEC = importlib.util.spec_from_file_location("soc_build_mcp", MODULE_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVER)


class SocBuildMcpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict(
            os.environ, {SERVER.MCP_SERVER_ACTIVE_ENV: "1"}
        )
        self.env_patcher.start()
        self.tempdir = tempfile.TemporaryDirectory()
        self.module_dir = Path(self.tempdir.name)
        (self.module_dir / "Makefile").write_text("all:\n\t@true\n")
        rtl = self.module_dir / "de" / "rtl"
        rtl.mkdir(parents=True)
        (rtl / "demo.sv").write_text("module demo; endmodule\n")
        (rtl / "filelist.f").write_text("demo.sv\n")
        run_dir = self.module_dir / "de" / "run"
        run_dir.mkdir(parents=True)
        (run_dir / "rtl.f").write_text(
            str(rtl / "demo.sv") + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        self.env_patcher.stop()

    def write_syn_snapshot(self, *, upf: bool) -> tuple[str, str, Path]:
        fingerprint = SERVER.compute_rtl_fingerprint(self.module_dir)
        assert fingerprint is not None
        run_id = "soc_syn-" + "a" * 32
        native = (
            self.module_dir
            / "de"
            / "syn"
            / "loop_evidence"
            / run_id
            / "native"
            / "de"
            / "syn"
        )
        native.mkdir(parents=True)
        (native / "rtl.f").write_text(
            str(self.module_dir / "de" / "rtl" / "demo.sv") + "\n",
            encoding="utf-8",
        )
        (native / "demo_netlist.v").write_text(
            "module demo; endmodule\n", encoding="utf-8"
        )
        (native / "demo.svf").write_text("svf\n", encoding="utf-8")
        if upf:
            (native / "upf").mkdir()
            (native / "upf" / "demo.upf").write_text(
                "set_design_top demo\n", encoding="utf-8"
            )
            (native / "upf" / "demo_synth.upf").write_text(
                "set_design_top demo\n", encoding="utf-8"
            )
        structural = {
            "rtl_filelist": native / "rtl.f",
            "netlist": native / "demo_netlist.v",
            "svf": native / "demo.svf",
        }
        if upf:
            structural.update(
                {
                    "reference_upf": native / "upf" / "demo.upf",
                    "implementation_upf": native / "upf" / "demo_synth.upf",
                }
            )
        evidence_dir = native.parents[2]
        (evidence_dir / "artifact_manifest.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "run_id": run_id,
                    "source_fingerprint": fingerprint,
                    "structural_artifacts": {
                        label: {
                            "path": path.relative_to(evidence_dir).as_posix(),
                            "sha256": SERVER._sha256(path),
                            "size": path.stat().st_size,
                        }
                        for label, path in structural.items()
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return run_id, fingerprint, native

    def write_syn_contract(
        self, *, top: str, syn_tool: str, upf: bool = False
    ) -> dict[str, Path]:
        syn = self.module_dir / "de" / "syn"
        run_dir = self.module_dir / "de" / "run"
        syn.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        contract = {
            "rtl_filelist": syn / "rtl.f",
            "netlist": syn / f"{top}_netlist.v",
        }
        if syn_tool == "dc":
            contract["svf"] = syn / f"{top}.svf"
        if upf:
            upf_dir = syn / "upf"
            upf_dir.mkdir(parents=True, exist_ok=True)
            contract["reference_upf"] = upf_dir / f"{top}.upf"
            contract["implementation_upf"] = upf_dir / f"{top}_synth.upf"
            contract["reference_upf"].write_text(
                f"set_design_top {top}\n", encoding="utf-8"
            )
        values = {
            "RTL_FILELIST": contract["rtl_filelist"],
            "NETLIST": contract["netlist"],
            "SVF": contract.get("svf", ""),
            "REFERENCE_UPF": contract.get("reference_upf", ""),
            "IMPLEMENTATION_UPF": contract.get("implementation_upf", ""),
        }
        (run_dir / "syn_artifacts.env").write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()),
            encoding="utf-8",
        )
        return contract

    def write_syn_products(self, contract: dict[str, Path]) -> None:
        for path in contract.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        contract["rtl_filelist"].write_text(
            str(self.module_dir / "de" / "rtl" / "demo.sv") + "\n",
            encoding="utf-8",
        )
        contract["netlist"].write_text("module demo; endmodule\n", encoding="utf-8")
        if "svf" in contract:
            contract["svf"].write_text("svf\n", encoding="utf-8")
        if "implementation_upf" in contract:
            contract["implementation_upf"].write_text(
                "set_design_top demo\n", encoding="utf-8"
            )

    def write_formal_reports(self, *, upf: bool) -> None:
        run_dir = self.module_dir / "de" / "run" / "formality"
        run_dir.mkdir(parents=True, exist_ok=True)
        reports = {
            "formality.log": "formal log\n",
            "library_defects.rpt": "Defects:   None\n",
            "match_status.rpt": "matched\n",
            "setup_status.rpt": "setup clean\n",
            "verification_status.rpt": (
                "Status:             SUCCEEDED\n"
                "Failing Points:     0\n"
                "Aborted Points:     0\n"
                "Unverified Points:  0\n"
                "VERIFICATION_STATUS=SUCCEEDED\n"
            ),
        }
        if upf:
            reports.update(
                {
                    "upf_reference.rpt": "reference upf\n",
                    "upf_implementation.rpt": "implementation upf\n",
                }
            )
        for name, content in reports.items():
            (run_dir / name).write_text(content, encoding="utf-8")

    def test_tool_registry_contains_new_interfaces(self) -> None:
        tools = SERVER.mcp._tool_manager._tools
        self.assertTrue({"soc_sim", "soc_regress", "soc_coverage", "soc_syn", "soc_formal", "soc_verdi", "soc_cdc", "soc_rdc", "soc_dft"} <= set(tools))

    def test_rejects_direct_tool_object_invocation(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError, "registered soc-build MCP server"
            ):
                SERVER.soc_sim(str(self.module_dir), "vcs", 1, "default")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_builds_before_running(self, run) -> None:
        result = SERVER.soc_sim(str(self.module_dir), "vcs", 7, "uart_all")
        self.assertTrue(result.startswith("ok\nLOOP_EVIDENCE="))
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        self.assertEqual(evidence["tool_family"], "soc_sim")
        self.assertTrue(evidence["run_id"].startswith("soc_sim-"))
        self.assertRegex(evidence["source_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertEqual(len(evidence["artifacts"]), 1)
        captured = self.module_dir / evidence["artifacts"][0]
        self.assertEqual(captured.read_text(encoding="utf-8"), "ok\n")
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            ["make", "comp", "sim", "SIMULATOR=vcs", "SEED=7", "TEST=uart_all"],
            cwd=str(self.module_dir.resolve()),
            timeout=1800,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_relative_module_dir_resolves_from_project_root(self, run) -> None:
        project_root = self.module_dir / "project"
        relative_module = project_root / "chip" / "top"
        relative_module.mkdir(parents=True)
        (relative_module / "Makefile").write_text("all:\n\t@true\n")
        rtl = relative_module / "de" / "rtl"
        rtl.mkdir(parents=True)
        (rtl / "top.sv").write_text("module top; endmodule\n")
        (rtl / "filelist.f").write_text("top.sv\n")

        with patch.object(SERVER, "PROJECT_ROOT", project_root):
            result = SERVER.soc_sim("chip/top", "vcs", 7, "uart_all")

        self.assertTrue(result.startswith("ok\nLOOP_EVIDENCE="))
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            ["make", "comp", "sim", "SIMULATOR=vcs", "SEED=7", "TEST=uart_all"],
            cwd=str(relative_module.resolve()),
            timeout=1800,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_regress_matrix(self, run) -> None:
        SERVER.soc_regress(str(self.module_dir), "vcs", "smoke,irq", "1,4-6", 3)
        run.assert_called_once_with(
            [
                "make",
                "regress",
                "SIMULATOR=vcs",
                "REGRESS_SEEDS=1,4-6",
                "REGRESS_JOBS=3",
                "REGRESS_TESTS=smoke,irq",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=43200,
        )

    def test_sim_rejects_iverilog(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported simulator 'iverilog'"):
            SERVER.soc_sim(str(self.module_dir), "iverilog", 1, "smoke")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_defaults_to_verilator(self, run) -> None:
        SERVER.soc_sim(str(self.module_dir), seed=1, test="smoke", top_module="tb_uart")
        run.assert_any_call(
            [
                "make",
                "comp",
                "sim",
                "SIMULATOR=verilator",
                "SEED=1",
                "TEST=smoke",
                "TOP_MODULE=tb_uart",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=1800,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_accepts_fsdb(self, run) -> None:
        SERVER.soc_sim(str(self.module_dir), "vcs", 1, "smoke", fsdb=True)
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            [
                "make",
                "comp",
                "sim",
                "SIMULATOR=vcs",
                "SEED=1",
                "TEST=smoke",
                "FSDB=1",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=1800,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_lint_accepts_spyglass(self, run) -> None:
        SERVER.soc_lint(str(self.module_dir), "spyglass", "uart")
        run.assert_called_once_with(
            ["make", "lint", "LINT_TOOL=spyglass", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=120,
        )

    def test_lint_rejects_unknown_tool(self) -> None:
        with self.assertRaisesRegex(ValueError, "spyglass"):
            SERVER.soc_lint(str(self.module_dir), "bad_lint_tool", "uart")

    @patch.object(SERVER, "_detect_gui_variables", return_value={"DISPLAY": ":0", "XAUTHORITY": "/tmp/xauth"})
    @patch.object(SERVER, "_run", return_value="ok")
    def test_lint_accepts_gui(self, run, gui_vars) -> None:
        SERVER.soc_lint(str(self.module_dir), "spyglass", "uart", gui=True)
        run.assert_called_once_with(
            [
                "make",
                "lint",
                "LINT_TOOL=spyglass",
                "RTL_TOP=uart",
                "GUI=1",
                "DISPLAY=:0",
                "XAUTHORITY=/tmp/xauth",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=120,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_cdc_accepts_spyglass(self, run) -> None:
        SERVER.soc_cdc(str(self.module_dir), "spyglass", "uart")
        run.assert_called_once_with(
            ["make", "cdc", "CDC_TOOL=spyglass", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

    def test_cdc_rejects_unknown_tool(self) -> None:
        with self.assertRaisesRegex(ValueError, "spyglass"):
            SERVER.soc_cdc(str(self.module_dir), "bad_cdc_tool", "uart")

    def test_cdc_accepts_vc_static_contract(self) -> None:
        self.assertIn("vc_static", SERVER.SUPPORTED_CDC_TOOLS)
        self.assertEqual(SERVER.SUPPORTED_RDC_TOOLS, {"vc_static"})
        self.assertEqual(SERVER.SUPPORTED_DFT_TOOLS, {"vc_static"})

    @patch.object(SERVER, "_run")
    def test_syn_uses_project_target(self, run) -> None:
        contract: dict[str, Path] = {}

        def create_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(
                    self.write_syn_contract(top="uart", syn_tool="yosys")
                )
            elif command[1] == "syn":
                self.write_syn_products(contract)
            return "ok"

        run.side_effect = create_outputs
        SERVER.soc_syn(str(self.module_dir), "uart")
        self.assertEqual(run.call_count, 3)
        run.assert_any_call(
            ["make", "syn-artifacts", "SYN_TOOL=yosys", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=120,
        )
        run.assert_any_call(
            ["make", "syn", "SYN_TOOL=yosys", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

    @patch.object(SERVER, "_run")
    def test_syn_accepts_dc(self, run) -> None:
        contract: dict[str, Path] = {}

        def create_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(self.write_syn_contract(top="uart", syn_tool="dc"))
            elif command[1] == "syn":
                self.write_syn_products(contract)
            return "ok"

        run.side_effect = create_outputs
        result = SERVER.soc_syn(str(self.module_dir), "uart", syn_tool="dc")
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        self.assertEqual(evidence["tool_family"], "soc_syn")
        self.assertEqual(len(evidence["artifacts"]), 5)
        self.assertEqual(
            (self.module_dir / evidence["artifacts"][0]).read_text(encoding="utf-8"),
            "ok\n",
        )
        self.assertEqual(run.call_count, 3)
        run.assert_any_call(
            ["make", "syn", "SYN_TOOL=dc", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

    @patch.object(SERVER, "_run")
    def test_formal_accepts_plain_dc_snapshot(self, run) -> None:
        run_id, fingerprint, native = self.write_syn_snapshot(upf=False)

        def create_reports(*args, **kwargs):
            self.write_formal_reports(upf=False)
            return "FORMAL_REPORTS_READY mode=plain"

        run.side_effect = create_reports
        result = SERVER.soc_formal(
            str(self.module_dir), run_id, fingerprint, rtl_top="demo", timeout=60
        )
        evidence = json.loads(result.split("FORMAL_EVIDENCE=", 1)[1])
        self.assertEqual(evidence["mode"], "plain")
        self.assertTrue(evidence["passed"])
        self.assertEqual(evidence["syn_run_id"], run_id)
        run.assert_called_once_with(
            [
                "make",
                "formal",
                f"FORMAL_RTL_FILELIST={native / 'rtl.f'}",
                f"FORMAL_NETLIST={native / 'demo_netlist.v'}",
                f"FORMAL_SVF={native / 'demo.svf'}",
                "RTL_TOP=demo",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=60,
        )

    @patch.object(SERVER, "_run")
    def test_formal_accepts_upf_dc_snapshot(self, run) -> None:
        run_id, fingerprint, native = self.write_syn_snapshot(upf=True)

        def create_reports(*args, **kwargs):
            self.write_formal_reports(upf=True)
            return "FORMAL_REPORTS_READY mode=upf"

        run.side_effect = create_reports
        result = SERVER.soc_formal(str(self.module_dir), run_id, fingerprint, timeout=60)
        evidence = json.loads(result.split("FORMAL_EVIDENCE=", 1)[1])
        self.assertEqual(evidence["mode"], "upf")
        self.assertIn("reference_upf", evidence["input_artifacts"])
        command = run.call_args.args[0]
        self.assertIn(
            f"FORMAL_REFERENCE_UPF={native / 'upf' / 'demo.upf'}", command
        )
        self.assertIn(
            f"FORMAL_IMPLEMENTATION_UPF={native / 'upf' / 'demo_synth.upf'}",
            command,
        )

    def test_formal_rejects_lone_upf_manifest_entry(self) -> None:
        run_id, fingerprint, native = self.write_syn_snapshot(upf=True)
        manifest_path = native.parents[2] / "artifact_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["structural_artifacts"]["implementation_upf"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "must pair reference"):
            SERVER.soc_formal(str(self.module_dir), run_id, fingerprint)

    def test_formal_rejects_lone_implementation_upf_manifest_entry(self) -> None:
        run_id, fingerprint, native = self.write_syn_snapshot(upf=True)
        manifest_path = native.parents[2] / "artifact_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["structural_artifacts"]["reference_upf"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "must pair reference"):
            SERVER.soc_formal(str(self.module_dir), run_id, fingerprint)

    def test_formal_rejects_modified_snapshot_artifact(self) -> None:
        run_id, fingerprint, native = self.write_syn_snapshot(upf=False)
        (native / "demo_netlist.v").write_text(
            "module demo; wire modified; endmodule\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(RuntimeError, "(size|digest) mismatch"):
            SERVER.soc_formal(str(self.module_dir), run_id, fingerprint)

    @patch.object(SERVER, "_run")
    def test_syn_evidence_captures_upf_and_svf(self, run) -> None:
        contract: dict[str, Path] = {}

        def create_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(
                    self.write_syn_contract(top="uart", syn_tool="dc", upf=True)
                )
                transient = (
                    self.module_dir
                    / "de"
                    / "syn"
                    / "dc"
                    / "reports"
                    / "loaded_upf.pre_compile.upf"
                )
                transient.parent.mkdir(parents=True)
                transient.write_text("transient\n", encoding="utf-8")
            elif command[1] == "syn":
                self.write_syn_products(contract)
            return "ok"

        run.side_effect = create_outputs
        result = SERVER.soc_syn(str(self.module_dir), "uart", syn_tool="dc")
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        native = [item for item in evidence["artifacts"] if "/native/" in item]
        self.assertEqual(
            {Path(item).suffix for item in native},
            {".f", ".v", ".svf", ".upf"},
        )
        self.assertEqual(len(native), 5)
        self.assertFalse(any("loaded_upf.pre_compile.upf" in item for item in native))
        manifest = [
            item for item in evidence["artifacts"] if item.endswith("artifact_manifest.json")
        ]
        self.assertEqual(len(manifest), 1)

    @patch.object(SERVER, "_run")
    def test_syn_evidence_always_captures_canonical_rtl_f(self, run) -> None:
        syn = self.module_dir / "de" / "syn"
        syn.mkdir(parents=True)
        rtl_f = syn / "rtl.f"
        rtl_f.write_text(
            str(self.module_dir / "de" / "rtl" / "demo.sv") + "\n",
            encoding="utf-8",
        )

        contract: dict[str, Path] = {}

        def create_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(self.write_syn_contract(top="demo", syn_tool="dc"))
                contract["rtl_filelist"].write_text(
                    rtl_f.read_text(encoding="utf-8"), encoding="utf-8"
                )
            elif command[1] == "syn":
                contract["netlist"].write_text(
                    "module demo; endmodule\n", encoding="utf-8"
                )
                contract["svf"].write_text("svf\n", encoding="utf-8")
            return "ok"

        run.side_effect = create_outputs
        result = SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        native = [Path(item) for item in evidence["artifacts"] if "/native/" in item]
        captured_rtl = [item for item in native if item.name == "rtl.f"]
        self.assertEqual(len(captured_rtl), 1)
        self.assertEqual(
            (self.module_dir / captured_rtl[0]).read_text(encoding="utf-8"),
            rtl_f.read_text(encoding="utf-8"),
        )

    @patch.object(SERVER, "_run")
    def test_syn_rejects_missing_declared_dc_output(self, run) -> None:
        contract: dict[str, Path] = {}

        def create_incomplete_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(self.write_syn_contract(top="demo", syn_tool="dc"))
            elif command[1] == "syn":
                contract["rtl_filelist"].write_text(
                    str(self.module_dir / "de" / "rtl" / "demo.sv") + "\n",
                    encoding="utf-8",
                )
                contract["svf"].write_text("svf\n", encoding="utf-8")
            return "ok"

        run.side_effect = create_incomplete_outputs
        with self.assertRaisesRegex(RuntimeError, "required nonempty artifacts"):
            SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")

    @patch.object(SERVER, "_run")
    def test_syn_rejects_missing_declared_reference_upf(self, run) -> None:
        contract: dict[str, Path] = {}

        def declare_missing_reference(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(
                    self.write_syn_contract(
                        top="demo", syn_tool="dc", upf=True
                    )
                )
                contract["reference_upf"].unlink()
            return "ok"

        run.side_effect = declare_missing_reference
        with self.assertRaisesRegex(
            RuntimeError, "canonical reference UPF is missing or empty"
        ):
            SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")

    @patch.object(SERVER, "_run")
    def test_syn_rejects_empty_declared_reference_upf(self, run) -> None:
        contract: dict[str, Path] = {}

        def declare_empty_reference(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(
                    self.write_syn_contract(
                        top="demo", syn_tool="dc", upf=True
                    )
                )
                contract["reference_upf"].write_text("", encoding="utf-8")
            return "ok"

        run.side_effect = declare_empty_reference
        with self.assertRaisesRegex(
            RuntimeError, "canonical reference UPF is missing or empty"
        ):
            SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")

    @patch.object(SERVER, "_run")
    def test_syn_rejects_reference_upf_mutation(self, run) -> None:
        contract: dict[str, Path] = {}

        def mutate_reference(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(
                    self.write_syn_contract(
                        top="demo", syn_tool="dc", upf=True
                    )
                )
            elif command[1] == "syn":
                self.write_syn_products(contract)
                contract["reference_upf"].write_text(
                    "set_design_top changed\n", encoding="utf-8"
                )
            return "ok"

        run.side_effect = mutate_reference
        with self.assertRaisesRegex(RuntimeError, "changed during synthesis"):
            SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")

    @patch.object(SERVER, "_run")
    def test_syn_rejects_derived_logic_filelist(self, run) -> None:
        contract: dict[str, Path] = {}

        def create_filtered_outputs(command, **kwargs):
            if command[1] == "syn-artifacts":
                contract.update(self.write_syn_contract(top="demo", syn_tool="dc"))
            elif command[1] == "syn":
                self.write_syn_products(contract)
                contract["rtl_filelist"].write_text(
                    "/different/logic_only.sv\n", encoding="utf-8"
                )
            return "ok"

        run.side_effect = create_filtered_outputs
        with self.assertRaisesRegex(RuntimeError, "differs from the canonical"):
            SERVER.soc_syn(str(self.module_dir), "demo", syn_tool="dc")

    @patch.object(SERVER, "_run")
    def test_success_evidence_rejects_source_drift(self, run) -> None:
        def mutate(*args, **kwargs):
            if run.call_count == 2:
                (self.module_dir / "de" / "rtl" / "demo.sv").write_text(
                    "module demo; wire changed; endmodule\n"
                )
            return "ok"

        run.side_effect = mutate
        with self.assertRaisesRegex(RuntimeError, "changed during soc_sim"):
            SERVER.soc_sim(str(self.module_dir), "vcs", 1, "smoke")

    @patch.object(SERVER, "_run")
    def test_sim_evidence_keeps_immutable_native_log(self, run) -> None:
        mutable = self.module_dir / "dv" / "sim" / "smoke" / "sim.log"

        def create_log(*args, **kwargs):
            if run.call_count == 2:
                mutable.parent.mkdir(parents=True, exist_ok=True)
                mutable.write_text("RESULT: ALL TESTS PASS\n", encoding="utf-8")
                return "RESULT: ALL TESTS PASS"
            return "filelist ready"

        run.side_effect = create_log
        result = SERVER.soc_sim(str(self.module_dir), "vcs", 1, "smoke")
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        native = [item for item in evidence["artifacts"] if "/native/" in item]
        self.assertEqual(len(native), 1)
        immutable = self.module_dir / native[0]
        self.assertEqual(immutable.read_text(encoding="utf-8"), "RESULT: ALL TESTS PASS\n")
        mutable.write_text("RESULT: TESTS FAILED\n", encoding="utf-8")
        self.assertEqual(immutable.read_text(encoding="utf-8"), "RESULT: ALL TESTS PASS\n")

    def test_syn_rejects_unknown_tool(self) -> None:
        with self.assertRaisesRegex(ValueError, "dc, yosys"):
            SERVER.soc_syn(str(self.module_dir), "uart", syn_tool="bad_syn_tool")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_verdi_uses_scope(self, run) -> None:
        SERVER.soc_verdi(
            str(self.module_dir), scope="dv", simulator="vcs", top_module="tb", test="smoke"
        )
        run.assert_called_once_with(
            [
                "make",
                "verdi",
                "SUBDIR=dv",
                "SIMULATOR=vcs",
                "TEST=smoke",
                "TOP_MODULE=tb",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=120,
        )

    def test_verdi_rejects_bad_scope(self) -> None:
        with self.assertRaises(ValueError):
            SERVER.soc_verdi(str(self.module_dir), scope="wave")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_coverage_regress(self, run) -> None:
        SERVER.soc_coverage(
            str(self.module_dir), "vcs", "regress", tests="uart_all", seeds="1-2", jobs=2
        )
        run.assert_called_once_with(
            [
                "make",
                "coverage-regress",
                "SIMULATOR=vcs",
                "REGRESS_SEEDS=1-2",
                "REGRESS_JOBS=2",
                "REGRESS_TESTS=uart_all",
            ],
            cwd=str(self.module_dir.resolve()),
            timeout=3600,
        )

    def test_rejects_shell_metacharacters(self) -> None:
        with self.assertRaises(ValueError):
            SERVER.soc_sim(str(self.module_dir), test="smoke;touch_bad")
        with self.assertRaises(ValueError):
            SERVER.soc_sim(str(self.module_dir), top_module="tb_uart;bad")

    def test_rejects_descending_seed_range(self) -> None:
        with self.assertRaises(ValueError):
            SERVER.soc_regress(str(self.module_dir), seeds="10-1")

    def test_rejects_unbounded_seed_matrix(self) -> None:
        with self.assertRaises(ValueError):
            SERVER.soc_regress(str(self.module_dir), seeds="1-10001")


if __name__ == "__main__":
    unittest.main()
