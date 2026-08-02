#!/usr/bin/env python3
"""Regression tests for Loop prompt budgets."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LoopPromptBudgetTest(unittest.TestCase):
    def test_context_bundles_stay_within_budget(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/loop_prompt_budget.py", "--check", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["pass"])
        self.assertLessEqual(
            result["bundles"]["dev_rtl"]["words"],
            result["bundles"]["dev_rtl"]["budget"],
        )
        self.assertLessEqual(
            result["bundles"]["delivery_merge_router"]["words"],
            result["bundles"]["delivery_merge_router"]["budget"],
        )
        self.assertLessEqual(
            result["bundles"]["delivery_signoff_router"]["words"],
            result["bundles"]["delivery_signoff_router"]["budget"],
        )


if __name__ == "__main__":
    unittest.main()
