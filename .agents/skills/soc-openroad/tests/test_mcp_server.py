from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVER_PATH = ROOT / "skills/soc-openroad/mcp_server.py"
SPEC = importlib.util.spec_from_file_location("soc_openroad_mcp_server_test", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVER)


class SocOpenroadServerTest(unittest.TestCase):
    def test_init_generates_portable_orfs_config_from_run_rtl_filelist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            self._write_module(project, "chip/core", "core")
            self._write_module(project, "chip/bus", "bus")
            self._write_module(project, "chip/top", "demo_top")
            run_dir = project / "chip/top/de/run"
            run_dir.mkdir(parents=True)
            (run_dir / "rtl.f").write_text(
                "\n".join(
                    [
                        f"{project}/chip/core/de/rtl/core.v",
                        f"{project}/chip/bus/de/rtl/bus.v",
                        f"{project}/chip/top/de/rtl/demo_top.v",
                    ]
                )
                + "\n"
            )

            result = SERVER.soc_openroad_init(
                str(project),
                module_dir="chip/top",
                design_name="demo_top",
                top_module="demo_top",
                platform="nangate45",
                clock_period_ns=5.0,
            )

            self.assertIn("[OK] OpenROAD config generated", result)
            self.assertIn("[INFO] Filelists: chip/top/de/run/rtl.f", result)
            config = project / "pd/openroad/nangate45/demo_top/config.mk"
            sdc = project / "pd/openroad/nangate45/demo_top/constraint.sdc"
            self.assertTrue(config.is_file())
            self.assertTrue(sdc.is_file())
            text = config.read_text()
            self.assertIn("export DESIGN_NAME = demo_top", text)
            self.assertIn("$(PROJECT_ROOT)/chip/core/de/rtl/core.v", text)
            self.assertIn("$(PROJECT_ROOT)/chip/bus/de/rtl/bus.v", text)
            self.assertIn("$(PROJECT_ROOT)/chip/top/de/rtl/demo_top.v", text)
            self.assertNotIn(str(project), text)
            self.assertIn("set clk_period 5", sdc.read_text())

    def test_init_requires_run_rtl_filelist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            self._write_module(project, "ip/digital/uart", "uart")

            with self.assertRaisesRegex(ValueError, "missing required PD RTL filelist"):
                SERVER.soc_openroad_init(
                    str(project),
                    module_dir="ip/digital/uart",
                    design_name="uart",
                    top_module="uart",
                    platform="nangate45",
                    clock_period_ns=10.0,
                )

    def test_status_reports_missing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status = SERVER.soc_openroad_status(tmp, design_name="demo_top")
            self.assertIn('"synth"', status)
            self.assertIn('"exists": false', status)

    def test_run_uses_docker_backend_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            config = project / "pd/openroad/nangate45/demo_top/config.mk"
            config.parent.mkdir(parents=True)
            config.write_text("export DESIGN_NAME = demo_top\n")
            captured: dict[str, object] = {}
            original_run_command = SERVER.run_command
            original_resolve_engine = SERVER._resolve_container_engine
            original_active = os.environ.get(SERVER.MCP_SERVER_ACTIVE_ENV)

            def fake_run_command(command, *, cwd=None, timeout=120):
                captured["command"] = command
                captured["cwd"] = cwd
                captured["timeout"] = timeout
                return "container ok"

            try:
                os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = "1"
                SERVER.run_command = fake_run_command
                SERVER._resolve_container_engine = lambda backend: ("docker", "docker")
                result = SERVER.soc_openroad_run(
                    str(project),
                    stage="synth",
                    design_name="demo_top",
                    jobs=2,
                    docker_image="openroad/orfs:test",
                    backend="docker",
                    timeout=33,
                )
            finally:
                SERVER.run_command = original_run_command
                SERVER._resolve_container_engine = original_resolve_engine
                if original_active is None:
                    os.environ.pop(SERVER.MCP_SERVER_ACTIVE_ENV, None)
                else:
                    os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = original_active

            command = captured["command"]
            self.assertIsNone(captured["cwd"])
            self.assertEqual(captured["timeout"], 33)
            self.assertEqual(command[0], "docker")
            self.assertIn(f"{project}:/work", command)
            self.assertIn("openroad/orfs:test", command)
            inner = command[-1]
            self.assertIn("make -j2 synth", inner)
            self.assertIn("DESIGN_CONFIG=/work/pd/openroad/nangate45/demo_top/config.mk", inner)
            self.assertIn("WORK_HOME=/work/pd/openroad/work", inner)
            self.assertIn("[INFO] BACKEND=docker", result)
            self.assertIn("container ok", result)

    def test_run_defaults_to_local_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            config_dir = project / "pd/openroad/nangate45/demo_top"
            config_dir.mkdir(parents=True)
            (config_dir / "config.mk").write_text("export DESIGN_NAME = demo_top\n")
            local_config = config_dir / "config.local.mk"
            local_config.write_text("include config.mk\n")
            orfs = Path(tmp) / "OpenROAD-flow-scripts/flow"
            (orfs / "scripts").mkdir(parents=True)
            (orfs / "Makefile").write_text("# test ORFS\n")
            (orfs / "scripts/variables.mk").write_text("# test variables\n")
            captured: dict[str, object] = {}
            original_run_command = SERVER.run_command
            original_active = os.environ.get(SERVER.MCP_SERVER_ACTIVE_ENV)
            original_orfs = os.environ.get(SERVER.LOCAL_ORFS_ENV)

            def fake_run_command(command, *, cwd=None, timeout=120):
                captured["command"] = command
                captured["cwd"] = cwd
                captured["timeout"] = timeout
                return "local ok"

            try:
                os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = "1"
                os.environ[SERVER.LOCAL_ORFS_ENV] = str(orfs)
                SERVER.run_command = fake_run_command
                result = SERVER.soc_openroad_run(str(project), stage="all", design_name="demo_top", timeout=44)
            finally:
                SERVER.run_command = original_run_command
                if original_active is None:
                    os.environ.pop(SERVER.MCP_SERVER_ACTIVE_ENV, None)
                else:
                    os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = original_active
                if original_orfs is None:
                    os.environ.pop(SERVER.LOCAL_ORFS_ENV, None)
                else:
                    os.environ[SERVER.LOCAL_ORFS_ENV] = original_orfs

            self.assertEqual(captured["cwd"], orfs)
            self.assertEqual(captured["timeout"], 44)
            self.assertEqual(captured["command"][0:2], ["make", "-j1"])
            self.assertIn("all", captured["command"])
            self.assertIn(f"DESIGN_CONFIG={local_config.resolve()}", captured["command"])
            self.assertIn(f"WORK_HOME={(project / 'pd/openroad/work_local').resolve()}", captured["command"])
            self.assertIn("[INFO] BACKEND=local", result)
            self.assertIn("local ok", result)

    def test_run_auto_requires_container_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            config = project / "pd/openroad/nangate45/demo_top/config.mk"
            config.parent.mkdir(parents=True)
            config.write_text("export DESIGN_NAME = demo_top\n")
            original_resolve_engine = SERVER._resolve_container_engine
            original_active = os.environ.get(SERVER.MCP_SERVER_ACTIVE_ENV)
            try:
                os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = "1"
                SERVER._resolve_container_engine = lambda backend: None
                with self.assertRaisesRegex(RuntimeError, "container backend unavailable"):
                    SERVER.soc_openroad_run(str(project), design_name="demo_top", backend="auto")
            finally:
                SERVER._resolve_container_engine = original_resolve_engine
                if original_active is None:
                    os.environ.pop(SERVER.MCP_SERVER_ACTIVE_ENV, None)
                else:
                    os.environ[SERVER.MCP_SERVER_ACTIVE_ENV] = original_active

    def _write_module(self, project: Path, relative: str, name: str) -> None:
        rtl = project / relative / "de/rtl"
        rtl.mkdir(parents=True)
        (rtl / f"{name}.v").write_text(f"module {name}(input clk); endmodule\n")
        (rtl / "filelist.f").write_text(f"$SOC/{relative}/de/rtl/{name}.v\n")
        (rtl / "filelist.mk").write_text("# unit test filelist\n")


if __name__ == "__main__":
    unittest.main()
