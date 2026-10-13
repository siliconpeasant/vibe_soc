from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "sync_mcp_configs", ROOT / "scripts/sync_mcp_configs.py"
)
assert SPEC and SPEC.loader
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class McpConfigSyncTest(unittest.TestCase):
    def test_local_transports_forward_runtime_overrides(self) -> None:
        for transport in (
            {"script": "server.py"},
            {"command": "node", "args": ["server.mjs"]},
        ):
            with self.subTest(transport=transport):
                server = dict(
                    name="test", default_enabled=False,
                    startup_timeout_sec=30, tool_timeout_sec=60, **transport,
                )
                lines = SYNC.render_codex_mcp_server(server, "launcher.sh")
                self.assertEqual(lines.count(
                    'env_vars = ["SILICON_CREW_PYTHON", "SILICON_CREW_MCP_VENV"]'
                ), 1)

    def test_remote_transport_has_no_stdio_environment(self) -> None:
        server = dict(
            name="remote", url="https://example.com/mcp", default_enabled=True,
            startup_timeout_sec=30, tool_timeout_sec=60,
        )
        self.assertFalse(any("env_vars" in line for line in
                             SYNC.render_codex_mcp_server(server, "launcher.sh")))

    def test_generated_configs_are_synchronized(self) -> None:
        self.assertEqual(SYNC.check(), 0)


if __name__ == "__main__":
    unittest.main()
