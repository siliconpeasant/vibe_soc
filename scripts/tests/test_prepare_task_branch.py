#!/usr/bin/env python3
"""Tests for scripts/prepare_task_branch.sh."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_task_branch.sh"


def run(*args: str, cwd: Path, check: bool = True, env: dict[str, str] | None = None):
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


class PrepareTaskBranchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.remote = root / "remote.git"
        self.seed = root / "seed"
        self.work = root / "work"

        run("git", "init", "--bare", str(self.remote), cwd=root)
        run("git", "init", str(self.seed), cwd=root)
        run("git", "checkout", "-b", "main", cwd=self.seed)
        run("git", "config", "user.name", "Branch Test", cwd=self.seed)
        run("git", "config", "user.email", "branch-test@example.com", cwd=self.seed)
        (self.seed / "README.md").write_text("seed\n", encoding="utf-8")
        run("git", "add", "README.md", cwd=self.seed)
        run("git", "commit", "-m", "Seed main", cwd=self.seed)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.seed)
        run("git", "push", "-u", "origin", "main", cwd=self.seed)
        run("git", "symbolic-ref", "HEAD", "refs/heads/main", cwd=self.remote)
        run("git", "clone", str(self.remote), str(self.work), cwd=root)

        self.env = os.environ.copy()
        self.env["GIT_PUBLISH_TIMESTAMP"] = "20260711-120000"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_creates_unique_branch_from_latest_origin_main(self) -> None:
        result = run(
            str(SCRIPT),
            "fix-ate-regression",
            cwd=self.work,
            env=self.env,
        )

        branch = run(
            "git", "branch", "--show-current", cwd=self.work
        ).stdout.strip()
        self.assertEqual(branch, "codex/fix-ate-regression-20260711-120000")
        head = run("git", "rev-parse", "HEAD", cwd=self.work).stdout.strip()
        base = run("git", "rev-parse", "origin/main", cwd=self.work).stdout.strip()
        self.assertEqual(head, base)
        self.assertIn("Created fresh task branch", result.stdout)

    def test_adds_suffix_when_name_already_exists(self) -> None:
        run(
            "git",
            "branch",
            "codex/fix-ate-regression-20260711-120000",
            cwd=self.work,
        )
        run(str(SCRIPT), "fix-ate-regression", cwd=self.work, env=self.env)
        branch = run(
            "git", "branch", "--show-current", cwd=self.work
        ).stdout.strip()
        self.assertEqual(branch, "codex/fix-ate-regression-20260711-120000-1")

    def test_rejects_dirty_worktree(self) -> None:
        (self.work / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        result = run(
            str(SCRIPT),
            "new-task",
            cwd=self.work,
            env=self.env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty worktree", result.stderr)
        branch = run(
            "git", "branch", "--show-current", cwd=self.work
        ).stdout.strip()
        self.assertEqual(branch, "main")

    def test_rejects_invalid_slug(self) -> None:
        result = run(
            str(SCRIPT),
            "Bad Task",
            cwd=self.work,
            env=self.env,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Invalid task slug", result.stderr)


if __name__ == "__main__":
    unittest.main()
