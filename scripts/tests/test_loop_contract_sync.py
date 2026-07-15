from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LoopContractSyncTest(unittest.TestCase):
    def test_contracts_are_synchronized(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sync_loop_contracts.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_dispatch_and_execution_invariants(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        loop = (ROOT / ".agents/skills/vibe-soc-loop/SKILL.md").read_text(encoding="utf-8")
        pd_skill = (ROOT / ".agents/skills/soc-openroad/SKILL.md").read_text(encoding="utf-8")
        state_rule = (ROOT / ".agents/rules/05_pipeline_state.md").read_text(encoding="utf-8")
        mode_rule = (ROOT / ".agents/rules/00_loop_modes.md").read_text(encoding="utf-8")
        self.assertIn("prepare_task_worktree.sh", agents)
        self.assertIn("do not run both by default", agents)
        self.assertIn("fewest useful tool loops", loop)
        self.assertIn("compact state", loop)
        for mode in ("dev", "merge", "signoff"):
            self.assertIn(mode, mode_rule)
        self.assertIn("--compact", state_rule)
        self.assertIn("immutable artifact paths", state_rule)
        self.assertIn("PD handoff summary", pd_skill)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", state_rule)


if __name__ == "__main__":
    unittest.main()
