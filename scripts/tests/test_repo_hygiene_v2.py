#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/check_repo_hygiene_v2.py"
SYNC = ROOT / "scripts/sync_repo_hygiene_entrypoint.py"


class RepoHygieneV2Test(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.update(
            {
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@example.invalid",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@example.invalid",
            }
        )
        self.git("init", "-q")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.commit()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            check=True,
            text=True,
            capture_output=True,
        )

    def commit(self) -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def check(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.repo), *args],
            cwd=self.repo,
            check=False,
            text=True,
            capture_output=True,
        )

    @staticmethod
    def personal_path() -> str:
        return "/" + "home/alice/private/tool"

    def test_diff_only_scans_added_lines_not_historical_lines(self) -> None:
        path = self.repo / "owned.txt"
        path.write_text(self.personal_path() + "\n", encoding="utf-8")
        self.commit()
        path.write_text(path.read_text(encoding="utf-8") + "safe addition\n", encoding="utf-8")
        completed = self.check()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_untracked_personal_path_and_license_are_rejected(self) -> None:
        license_value = "LM" + "_LICENSE_FILE=27000@license-host"
        (self.repo / "bad.txt").write_text(
            self.personal_path() + "\n" + license_value + "\n",
            encoding="utf-8",
        )
        completed = self.check()
        self.assertEqual(completed.returncode, 2)
        self.assertIn("personal absolute path", completed.stdout)
        self.assertIn("license endpoint", completed.stdout)

    def test_valid_pipeline_workspace_is_schema_allowlisted(self) -> None:
        state = self.repo / "ip/example/pipeline_state.json"
        state.parent.mkdir(parents=True)
        state.write_text(
            json.dumps(
                {
                    "module": "example",
                    "workspace": self.personal_path(),
                    "mode": "single",
                    "pipeline": {},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        completed = self.check()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workspace_field_in_unrecognized_json_is_rejected(self) -> None:
        (self.repo / "config.json").write_text(
            json.dumps({"workspace": self.personal_path()}, indent=2) + "\n",
            encoding="utf-8",
        )
        completed = self.check()
        self.assertEqual(completed.returncode, 2)

    def test_vendor_baseline_is_skipped(self) -> None:
        vendor = self.repo / "chip/top/de/rtl/vendor/upstream/file.txt"
        vendor.parent.mkdir(parents=True)
        vendor.write_text(self.personal_path() + "\n", encoding="utf-8")
        completed = self.check()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_embedded_project_directory_is_not_an_absolute_path(self) -> None:
        fixture = self.repo / "test_fixture.py"
        fixture.write_text(
            'template = ROOT / ".agents/skills/tool/templates/project/scripts/run.py"\n',
            encoding="utf-8",
        )
        completed = self.check()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_all_scope_detects_committed_first_party_debt(self) -> None:
        (self.repo / "owned.txt").write_text(self.personal_path() + "\n", encoding="utf-8")
        self.commit()
        self.assertEqual(self.check().returncode, 0)
        self.assertEqual(self.check("--all").returncode, 2)

    def test_generated_entrypoint_is_synchronized(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
