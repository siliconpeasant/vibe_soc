#!/usr/bin/env python3
"""Regression tests for the PreToolUse EDA policy hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "pre_tool_use_policy.py"
WRAPPER = Path(__file__).resolve().parents[1] / "pre-tool-use.sh"


class PreToolUsePolicyTest(unittest.TestCase):
    def _run(self, command: str) -> subprocess.CompletedProcess[str]:
        payload = json.dumps({"tool_input": {"cmd": command}})
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )

    def test_allows_non_eda_command(self) -> None:
        result = self._run("git status --short")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_direct_eda_command(self) -> None:
        result = self._run("make sim MODULE=chip/top")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_does_not_require_stdin_eof(self) -> None:
        payload = json.dumps({"tool_input": {"cmd": "git status --short"}}).encode()
        process = subprocess.Popen(
            [sys.executable, str(HOOK)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertIsNotNone(process.stdin)
        process.stdin.write(payload)
        process.stdin.flush()
        try:
            self.assertEqual(process.wait(timeout=1), 0)
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=1)

    def test_wrapper_uses_its_own_location(self) -> None:
        result = subprocess.run(
            [str(WRAPPER)],
            input=json.dumps({"tool_input": {"cmd": "git status --short"}}),
            text=True,
            capture_output=True,
            cwd="/tmp",
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrapper_ignores_hostile_eda_python_environment(self) -> None:
        env = os.environ.copy()
        env.update(
            PYTHONHOME="/nonexistent/python2",
            PYTHONPATH="/nonexistent/vendor/site-packages",
            SILICON_CREW_HOOK_PYTHON=sys.executable,
        )
        result = subprocess.run(
            [str(WRAPPER)],
            input=json.dumps({"tool_input": {"cmd": "make sim MODULE=chip/top"}}),
            text=True,
            capture_output=True,
            cwd="/tmp",
            env=env,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_top_level_error_is_logged_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "hook.log"
            code = (
                "import io, runpy, sys; "
                "sys.stdin = io.StringIO('{}'); "
                f"runpy.run_path({str(HOOK)!r}, run_name='__main__')"
            )
            env = os.environ.copy()
            env["VIBE_SOC_HOOK_DIAGNOSTIC_LOG"] = str(log_path)
            result = subprocess.run(
                [sys.executable, "-c", code],
                text=True,
                capture_output=True,
                env=env,
                timeout=5,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fileno", result.stderr)
            self.assertIn("UnsupportedOperation", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
