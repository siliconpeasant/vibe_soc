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

    def test_required_review_sections_and_classifications(self) -> None:
        contract = (ROOT / ".agents/agents/soc-reviewer.md").read_text(encoding="utf-8")
        for section in (
            "Review Summary",
            "Key Risks",
            "Issue List",
            "Waiver Review",
            "Delivery Checklist",
            "Next Actions",
        ):
            self.assertIn(section, contract)
        for severity in ("Blocker", "Critical", "Major", "Minor", "Info"):
            self.assertIn(severity, contract)
        self.assertIn("Need Human Confirmation", contract)
        self.assertIn("soc-ai-kb", contract)
        self.assertIn("soc/review/rule_library/", contract)
        self.assertIn("Reference Evidence", contract)
        self.assertIn("contains only a title/heading", contract)
        self.assertIn("Never state that the design is signed off", contract)

    def test_review_gate_matches_knowledge_fallback(self) -> None:
        gate = (ROOT / ".agents/rules/13_review_gate.md").read_text(encoding="utf-8")
        self.assertIn("project-specific rules first", gate)
        self.assertIn("Need Human Confirmation", gate)
        self.assertIn("rule ID, source, version", gate)
        self.assertIn("Hard source gate", gate)
        self.assertIn("cannot independently establish a project violation", gate)
        self.assertIn("Project Rule|Reference Evidence|Local Evidence", gate)


if __name__ == "__main__":
    unittest.main()
