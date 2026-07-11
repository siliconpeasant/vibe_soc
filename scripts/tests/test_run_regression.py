"""Focused unit tests for the regression runner."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "run_regression.py"
SPEC = importlib.util.spec_from_file_location("vibe_soc_run_regression", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class RunRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.sim_dir = self.root / "sim"
        self.output_dir = self.root / "regress"
        self.module_dir = self.root / "module"
        self.sim_dir.mkdir()
        self.output_dir.mkdir()
        self.module_dir.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _completed_run(self, *args, **kwargs):
        kwargs["stdout"].write("TEST PASSED CHECKS\n")
        return Mock(returncode=0)

    def _run_one(self, name: str, seed: int = 1, case_args: str = ""):
        with patch.object(RUNNER.subprocess, "run", side_effect=self._completed_run) as run:
            result = RUNNER.run_one(
                self.sim_dir,
                self.output_dir,
                "",
                RUNNER.TestSpec(name, case_args),
                seed,
                r"TEST PASSED CHECKS",
                r"\[(?:ERROR|FAIL)\]",
                "",
                self.module_dir,
                "vcs",
                "tb",
            )
        return result, run

    def test_inline_tests_override_existing_test_file(self) -> None:
        tests_file = self.root / "tests.list"
        tests_file.write_text("from_file\n", encoding="utf-8")
        specs = RUNNER.load_tests(tests_file, "inline_a,inline_b")
        self.assertEqual([spec.name for spec in specs], ["inline_a", "inline_b"])

    def test_default_uses_existing_test_file(self) -> None:
        tests_file = self.root / "tests.list"
        tests_file.write_text("from_file +foo=1\n", encoding="utf-8")
        specs = RUNNER.load_tests(tests_file, "default")
        self.assertEqual(specs, [RUNNER.TestSpec("from_file", "+foo=1")])

    def test_recursive_make_binds_case_before_make_parsing(self) -> None:
        result, run = self._run_one("rom_keymgr_functest", seed=7, case_args="+extra=1")
        command = run.call_args.args[0]
        self.assertIsInstance(command, list)
        self.assertIn("TEST=rom_keymgr_functest", command)
        self.assertIn("SEED=7", command)
        self.assertIn("SIMULATOR=vcs", command)
        self.assertIn("TOP_MODULE=tb", command)
        self.assertIn("REGRESS_CASE_ARGS=+extra=1", command)
        self.assertFalse(any("+UVM_TESTNAME" in item for item in command))
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertIsNone(run.call_args.kwargs["executable"])
        self.assertEqual(result.status, "PASS")

    def test_recursive_make_isolates_case_and_seed_directories(self) -> None:
        _, first = self._run_one("case_a", seed=1)
        _, second = self._run_one("case_b", seed=2)
        first_sim_dir = next(item for item in first.call_args.args[0] if item.startswith("SIM_DIR="))
        second_sim_dir = next(item for item in second.call_args.args[0] if item.startswith("SIM_DIR="))
        self.assertNotEqual(first_sim_dir, second_sim_dir)
        self.assertIn("cases/case_a/seed_1", first_sim_dir)
        self.assertIn("cases/case_b/seed_2", second_sim_dir)

    def test_recursive_make_rejects_unsafe_test_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsafe recursive-make test name"):
            RUNNER.run_one(
                self.sim_dir,
                self.output_dir,
                "",
                RUNNER.TestSpec("bad;name"),
                1,
                "",
                "",
                "",
                self.module_dir,
                "vcs",
                "tb",
            )

    def test_template_runner_matches_live_runner(self) -> None:
        template = ROOT / ".agents/skills/soc-build/templates/project/scripts/run_regression.py"
        self.assertEqual(RUNNER_PATH.read_text(encoding="utf-8"), template.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
