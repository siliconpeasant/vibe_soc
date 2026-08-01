#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYNC_PATH = ROOT / "scripts/sync_mcp_runtime.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_mcp_runtime", SYNC_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class McpRuntimeSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = load_sync_module()

    def test_manifest_and_requirements_are_complete(self) -> None:
        self.sync.validate_inputs()
        manifest = json.loads((ROOT / ".agents/mcp-servers.json").read_text(encoding="utf-8"))
        names = [server["name"] for server in manifest["servers"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 9)
        upf_gen = next(server for server in manifest["servers"] if server["name"] == "upf-gen")
        self.assertEqual(upf_gen["script"], ".agents/skills/upf-gen/mcp_server.py")
        self.assertGreaterEqual(upf_gen["tool_timeout_sec"], 43200)
        soc_build = next(server for server in manifest["servers"] if server["name"] == "soc-build")
        self.assertGreaterEqual(soc_build["tool_timeout_sec"], 43200)
        openroad = next(server for server in manifest["servers"] if server["name"] == "soc-openroad")
        self.assertGreaterEqual(openroad["tool_timeout_sec"], 7200)
        openroad_mcp = next(server for server in manifest["servers"] if server["name"] == "openroad-mcp")
        self.assertEqual(openroad_mcp["command"], "/usr/bin/env")
        self.assertIn(".openroad-mcp-venv/bin/openroad-mcp", openroad_mcp["args"])
        self.assertGreaterEqual(openroad_mcp["tool_timeout_sec"], 120)

    def test_generated_shell_is_posix_parseable(self) -> None:
        for content in self.sync.expected_runtime_files().values():
            with tempfile.NamedTemporaryFile("w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                completed = subprocess.run(["/bin/sh", "-n", stream.name], check=False)
                self.assertEqual(completed.returncode, 0)

    def test_runtime_contract_is_present(self) -> None:
        runtime = self.sync.expected_runtime_files()[ROOT / ".agents/scripts/run_mcp_python.sh"]
        for required in (
            "unset PYTHONHOME PYTHONPATH PYTHONVERSION",
            "mcp openpyxl pandas yaml xlrd",
            "sys.version_info >= (3, 10)",
            "mcp-requirements.txt",
            "silicon-crew/venv",
            "--setup-only",
            "install.lock",
        ):
            self.assertIn(required, runtime)
        self.assertIn("numpy==1.26.4", (ROOT / ".agents/mcp-requirements.txt").read_text(encoding="utf-8"))

    def test_generated_files_are_synchronized(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC_PATH), "--check"],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
