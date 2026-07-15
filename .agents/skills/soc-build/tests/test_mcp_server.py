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

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        self.env_patcher.stop()

    def test_tool_registry_contains_new_interfaces(self) -> None:
        tools = SERVER.mcp._tool_manager._tools
        self.assertTrue({"soc_sim", "soc_regress", "soc_coverage", "soc_syn", "soc_verdi", "soc_cdc"} <= set(tools))

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

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_accepts_valid_top_module(self, run) -> None:
        SERVER.soc_sim(
            str(self.module_dir), "iverilog", 1, "smoke", top_module="tb_uart"
        )
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            [
                "make",
                "comp",
                "sim",
                "SIMULATOR=iverilog",
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
        with self.assertRaisesRegex(ValueError, "spyglass, verilator"):
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

    def test_cdc_rejects_non_spyglass(self) -> None:
        with self.assertRaisesRegex(ValueError, "spyglass"):
            SERVER.soc_cdc(str(self.module_dir), "bad_cdc_tool", "uart")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_syn_uses_project_target(self, run) -> None:
        SERVER.soc_syn(str(self.module_dir), "uart")
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            ["make", "syn", "SYN_TOOL=yosys", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_syn_accepts_dc(self, run) -> None:
        result = SERVER.soc_syn(str(self.module_dir), "uart", syn_tool="dc")
        evidence = json.loads(result.split("LOOP_EVIDENCE=", 1)[1])
        self.assertEqual(evidence["tool_family"], "soc_syn")
        self.assertEqual(len(evidence["artifacts"]), 1)
        self.assertEqual(
            (self.module_dir / evidence["artifacts"][0]).read_text(encoding="utf-8"),
            "ok\n",
        )
        self.assertEqual(run.call_count, 2)
        run.assert_any_call(
            ["make", "syn", "SYN_TOOL=dc", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

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
