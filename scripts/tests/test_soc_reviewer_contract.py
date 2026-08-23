from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SocReviewerContractTest(unittest.TestCase):
    def test_agent_profiles_are_synchronized(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sync_agent_profiles.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_role_mcp_servers_define_transport(self) -> None:
        for role in ("soc-integrator", "soc-pd-engineer", "soc-dft-engineer"):
            profile = (ROOT / f".codex/agents/{role}.toml").read_text(encoding="utf-8")
            mcp_config = profile.split("\n[mcp_servers.", maxsplit=1)[1]
            self.assertTrue(
                'command = "' in mcp_config or 'url = "' in mcp_config,
                f"{role} MCP config must define a command or URL transport",
            )

    def test_ported_roles_exist(self) -> None:
        for role in (
            "soc-dft-engineer",
            "soc-cdc-engineer",
            "soc-low-power-engineer",
        ):
            self.assertTrue((ROOT / f".agents/agents/{role}.md").is_file(), role)
            self.assertTrue((ROOT / f".codex/agents/{role}.toml").is_file(), role)
        self.assertTrue((ROOT / ".agents/rules/14_dft_gate.md").is_file())
        self.assertTrue((ROOT / ".agents/rules/15_reset_ownership.md").is_file())

    def test_required_review_sections_and_classifications(self) -> None:
        contract = (ROOT / ".agents/agents/soc-reviewer.md").read_text(encoding="utf-8")
        gate = (ROOT / ".agents/rules/13_review_gate.md").read_text(encoding="utf-8")
        combined = contract + gate
        for section in (
            "Review Summary",
            "Key Risks",
            "Issue List",
            "Waiver Review",
            "Delivery Checklist",
            "Next Actions",
        ):
            self.assertIn(section, combined)
        for severity in ("Blocker", "Critical", "Major", "Minor", "Info"):
            self.assertIn(severity, combined)
        self.assertIn("13_review_gate.md", contract)
        self.assertIn("Need Human Confirmation", gate)
        self.assertIn("soc-ai-kb", gate)
        self.assertIn("soc/review/rule_library/", gate)
        self.assertIn("Reference Evidence", gate)
        self.assertIn("Never state that the design is signed off", gate)

    def test_review_gate_matches_knowledge_fallback(self) -> None:
        gate = (ROOT / ".agents/rules/13_review_gate.md").read_text(encoding="utf-8")
        self.assertIn("project rules before narrower", gate)
        self.assertIn("Need Human Confirmation", gate)
        self.assertIn("Never invent a rule", gate)
        self.assertIn("ID, source, version", gate)
        self.assertIn("authoritative `Project Rule`", gate)
        self.assertIn("Local Evidence", gate)
        self.assertIn("Project Rule|Reference Evidence|Local Evidence", gate)


if __name__ == "__main__":
    unittest.main()
