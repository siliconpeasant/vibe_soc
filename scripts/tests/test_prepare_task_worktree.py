#!/usr/bin/env python3
"""Tests for isolated task worktree creation and safe cleanup."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
PREPARE = SCRIPTS / "prepare_task_worktree.sh"
CLEANUP = SCRIPTS / "cleanup_task_worktree.sh"


def run(*args: str, cwd: Path, check: bool = True, env: dict[str, str] | None = None):
    return subprocess.run(
        args, cwd=cwd, env=env, text=True, capture_output=True, check=check
    )


class PrepareTaskWorktreeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.remote = root / "github.com" / "remote.git"
        self.seed = root / "seed"
        self.work = root / "work"
        self.tasks = root / "tasks"
        self.remote.parent.mkdir()
        run("git", "init", "--bare", str(self.remote), cwd=root)
        run("git", "init", str(self.seed), cwd=root)
        run("git", "checkout", "-b", "main", cwd=self.seed)
        run("git", "config", "user.name", "Worktree Test", cwd=self.seed)
        run("git", "config", "user.email", "worktree-test@example.com", cwd=self.seed)
        (self.seed / "README.md").write_text("seed\n", encoding="utf-8")
        (self.seed / ".gitignore").write_text(
            "scripts/local.mk\n"
            "scripts/local.sh\n"
            "scripts/local.csh\n"
            "pd/openroad/local/\n"
            "pd/openroad/**/config.local.mk\n",
            encoding="utf-8",
        )
        run("git", "add", "README.md", ".gitignore", cwd=self.seed)
        run("git", "commit", "-m", "Seed main", cwd=self.seed)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.seed)
        run("git", "push", "-u", "origin", "main", cwd=self.seed)
        run("git", "symbolic-ref", "HEAD", "refs/heads/main", cwd=self.remote)
        run("git", "clone", str(self.remote), str(self.work), cwd=root)
        run("git", "config", "user.name", "Worktree Test", cwd=self.work)
        run("git", "config", "user.email", "worktree-test@example.com", cwd=self.work)
        self.env = os.environ.copy()
        self.env.update(
            GIT_PUBLISH_TIMESTAMP="20260715-010203",
            CODEX_WORKTREE_ROOT=str(self.tasks),
        )
        fake_bin = root / "bin"
        fake_bin.mkdir()
        fake_gh = fake_bin / "gh"
        fake_gh.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"${GH_FAKE_HEAD:-}\"\n",
            encoding="utf-8",
        )
        fake_gh.chmod(0o755)
        self.env["PATH"] = f"{fake_bin}:{self.env['PATH']}"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def prepare(self) -> tuple[subprocess.CompletedProcess[str], Path]:
        result = run(str(PREPARE), "loop-lite", cwd=self.work, env=self.env)
        line = next(item for item in result.stdout.splitlines() if item.startswith("WORKTREE="))
        return result, Path(line.split("=", 1)[1])

    def test_dirty_source_remains_untouched(self) -> None:
        (self.work / "local.txt").write_text("keep me\n", encoding="utf-8")
        result, task = self.prepare()
        self.assertTrue(task.is_dir())
        self.assertEqual(
            run("git", "branch", "--show-current", cwd=task).stdout.strip(),
            "codex/loop-lite-20260715-010203",
        )
        self.assertEqual(
            run("git", "branch", "--show-current", cwd=self.work).stdout.strip(), "main"
        )
        self.assertTrue((self.work / "local.txt").is_file())
        self.assertFalse((task / "local.txt").exists())
        self.assertIn("Start with:", result.stdout)

    def test_copies_whitelisted_local_config(self) -> None:
        scripts = self.work / "scripts"
        scripts.mkdir()
        (scripts / "local.mk").write_text("LOCAL_TOOL := test\n", encoding="utf-8")
        local_sh = scripts / "local.sh"
        local_sh.write_text("export LOCAL_TOOL=test\n", encoding="utf-8")
        local_sh.chmod(0o700)
        design = self.work / "pd" / "openroad" / "nangate45" / "uart"
        design.mkdir(parents=True)
        (design / "config.local.mk").write_text(
            "include config.mk\n", encoding="utf-8"
        )
        wrappers = self.work / "pd" / "openroad" / "local"
        wrappers.mkdir()
        wrapper = wrappers / "openroad-local"
        wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
        wrapper.chmod(0o755)

        result, task = self.prepare()

        self.assertEqual(
            (task / "scripts" / "local.mk").read_text(encoding="utf-8"),
            "LOCAL_TOOL := test\n",
        )
        self.assertTrue((task / "scripts" / "local.sh").stat().st_mode & 0o100)
        self.assertEqual(
            (
                task
                / "pd"
                / "openroad"
                / "nangate45"
                / "uart"
                / "config.local.mk"
            ).read_text(encoding="utf-8"),
            "include config.mk\n",
        )
        self.assertTrue(
            (task / "pd" / "openroad" / "local" / "openroad-local").is_file()
        )
        self.assertIn("Local config: copied=4", result.stdout)

    def test_links_configured_persistent_local_config(self) -> None:
        persistent = Path(self.tempdir.name) / "persistent-config"
        (persistent / "scripts").mkdir(parents=True)
        shared = persistent / "scripts" / "local.mk"
        shared.write_text("SHARED := yes\n", encoding="utf-8")
        run(
            "git",
            "config",
            "--local",
            "vibeSoc.localConfigRoot",
            str(persistent),
            cwd=self.work,
        )

        result, task = self.prepare()
        linked = task / "scripts" / "local.mk"

        self.assertTrue(linked.is_symlink())
        self.assertEqual(linked.resolve(), shared.resolve())
        shared.write_text("SHARED := updated\n", encoding="utf-8")
        self.assertEqual(linked.read_text(encoding="utf-8"), "SHARED := updated\n")
        self.assertIn("Local config: copied=0 linked=1", result.stdout)

    def test_missing_configured_root_cleans_partial_worktree(self) -> None:
        missing = Path(self.tempdir.name) / "missing-config"
        run(
            "git",
            "config",
            "--local",
            "vibeSoc.localConfigRoot",
            str(missing),
            cwd=self.work,
        )

        result = run(
            str(PREPARE),
            "loop-lite",
            cwd=self.work,
            env=self.env,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Configured local config root does not exist", result.stderr)
        branches = run(
            "git", "branch", "--format=%(refname:short)", cwd=self.work
        ).stdout.splitlines()
        self.assertNotIn("codex/loop-lite-20260715-010203", branches)
        self.assertEqual(list(self.tasks.iterdir()), [])

    def test_cleanup_accepts_merged_clean_branch(self) -> None:
        _, task = self.prepare()
        branch = run("git", "branch", "--show-current", cwd=task).stdout.strip()
        result = run(str(CLEANUP), str(task), cwd=self.work, env=self.env)
        self.assertFalse(task.exists())
        branches = run("git", "branch", "--format=%(refname:short)", cwd=self.work).stdout
        self.assertNotIn(branch, branches.splitlines())
        self.assertIn("Remote branches were not changed", result.stdout)

    def test_cleanup_rejects_unmerged_branch(self) -> None:
        _, task = self.prepare()
        (task / "change.txt").write_text("new\n", encoding="utf-8")
        run("git", "add", "change.txt", cwd=task)
        run("git", "commit", "-m", "Unmerged change", cwd=task)
        result = run(
            str(CLEANUP), str(task), cwd=self.work, env=self.env, check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmerged branch", result.stderr)
        self.assertTrue(task.is_dir())

    def test_cleanup_accepts_squash_merged_pr_evidence(self) -> None:
        _, task = self.prepare()
        (task / "change.txt").write_text("squashed\n", encoding="utf-8")
        run("git", "add", "change.txt", cwd=task)
        run("git", "commit", "-m", "Squash candidate", cwd=task)
        env = self.env.copy()
        env["GH_FAKE_HEAD"] = run("git", "rev-parse", "HEAD", cwd=task).stdout.strip()
        result = run(str(CLEANUP), str(task), cwd=self.work, env=env)
        self.assertFalse(task.exists())
        self.assertIn("Deleted merged local branch", result.stdout)


if __name__ == "__main__":
    unittest.main()
