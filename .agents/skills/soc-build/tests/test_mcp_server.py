from __future__ import annotations

import importlib.util
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

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        self.env_patcher.stop()

    def test_tool_registry_contains_new_interfaces(self) -> None:
        tools = SERVER.mcp._tool_manager._tools
        self.assertTrue({"soc_sim", "soc_regress", "soc_coverage", "soc_syn"} <= set(tools))

    def test_rejects_direct_tool_object_invocation(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError, "registered soc-build MCP server"
            ):
                SERVER.soc_sim(str(self.module_dir), "vcs", 1, "default")

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_builds_before_running(self, run) -> None:
        result = SERVER.soc_sim(str(self.module_dir), "vcs", 7, "uart_all")
        self.assertEqual(result, "ok")
        run.assert_called_once_with(
            ["make", "comp", "sim", "SIMULATOR=vcs", "SEED=7", "TEST=uart_all"],
            cwd=str(self.module_dir.resolve()),
            timeout=600,
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
            timeout=3600,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_sim_accepts_valid_top_module(self, run) -> None:
        SERVER.soc_sim(
            str(self.module_dir), "iverilog", 1, "smoke", top_module="tb_uart"
        )
        run.assert_called_once_with(
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
            timeout=600,
        )

    @patch.object(SERVER, "_run", return_value="ok")
    def test_syn_uses_project_target(self, run) -> None:
        SERVER.soc_syn(str(self.module_dir), "uart")
        run.assert_called_once_with(
            ["make", "syn", "RTL_TOP=uart"],
            cwd=str(self.module_dir.resolve()),
            timeout=1200,
        )

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
