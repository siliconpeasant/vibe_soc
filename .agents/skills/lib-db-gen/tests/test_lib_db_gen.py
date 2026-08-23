from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lib_db_gen.py"
SPEC = importlib.util.spec_from_file_location("lib_db_gen_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
LIB_DB_GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LIB_DB_GEN
SPEC.loader.exec_module(LIB_DB_GEN)


class LibDbGenTclLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.lib_path = self.root / "unit.lib"
        self.lib_path.write_text("library (unit_lib) {\n}\n", encoding="utf-8")
        self.db_path = self.root / "out" / "unit.db"
        self.work_dir = self.root / "lc_work"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def convert_args(self, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "lib": str(self.lib_path),
            "db": str(self.db_path),
            "library_name": None,
            "tcl": None,
            "work_dir": str(self.work_dir),
            "no_run": False,
            "keep_tcl": False,
            "lc_shell": "lc_shell",
            "dc_shell": "dc_shell",
            # Force LC path so unit tests exercise the run_lc_shell hook.
            "shell_mode": "lc",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    @property
    def default_tcl(self) -> Path:
        return self.work_dir / "unit.lc.tcl"

    def output_path_from_tcl(self, tcl_path: Path) -> Path:
        text = tcl_path.read_text(encoding="utf-8")
        match = re.search(r'write_lib .* -format db -output "([^"]+)"', text)
        self.assertIsNotNone(match)
        assert match is not None
        return Path(match.group(1))

    def successful_lc(self, _shell: str, tcl_path: Path, work_dir: Path) -> None:
        self.assertEqual(tcl_path, self.default_tcl)
        self.assertEqual(work_dir, self.work_dir)
        self.assertTrue(tcl_path.is_file())
        staged_db = self.output_path_from_tcl(tcl_path)
        self.assertNotEqual(staged_db, self.db_path)
        staged_db.write_bytes(b"fake-db")

    def test_convert_success_removes_default_tcl_from_work_dir(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell", side_effect=self.successful_lc):
            self.assertEqual(LIB_DB_GEN.cmd_convert(self.convert_args()), 0)
        self.assertFalse(self.default_tcl.exists())
        self.assertTrue(self.db_path.is_file())
        self.assertEqual(list(self.db_path.parent.glob("*.lc.tcl")), [])

    def test_convert_failure_retains_tcl_in_work_dir(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell", side_effect=RuntimeError("lc failed")):
            with self.assertRaisesRegex(RuntimeError, "lc failed"):
                LIB_DB_GEN.cmd_convert(self.convert_args())
        self.assertTrue(self.default_tcl.is_file())

    def test_convert_missing_current_run_db_retains_tcl_and_fails(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell"):
            with self.assertRaisesRegex(RuntimeError, "current-run DB"):
                LIB_DB_GEN.cmd_convert(self.convert_args())
        self.assertTrue(self.default_tcl.is_file())

    def test_convert_stale_db_is_not_accepted_as_current_run_output(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_bytes(b"old-db")
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell"):
            with self.assertRaisesRegex(RuntimeError, "current-run DB"):
                LIB_DB_GEN.cmd_convert(self.convert_args())
        self.assertEqual(self.db_path.read_bytes(), b"old-db")
        self.assertTrue(self.default_tcl.is_file())

    def test_convert_no_run_retains_tcl_in_work_dir(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell") as run_lc:
            self.assertEqual(LIB_DB_GEN.cmd_convert(self.convert_args(no_run=True)), 0)
        run_lc.assert_not_called()
        self.assertTrue(self.default_tcl.is_file())

    def test_convert_no_run_default_dc_emits_enable_write_lib_mode(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell") as run_lc:
            self.assertEqual(
                LIB_DB_GEN.cmd_convert(self.convert_args(no_run=True, shell_mode="dc")),
                0,
            )
        run_lc.assert_not_called()
        self.assertIn(
            "enable_write_lib_mode",
            self.default_tcl.read_text(encoding="utf-8"),
        )

    def test_default_work_dir_contains_no_run_tcl(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell") as run_lc:
            self.assertEqual(
                LIB_DB_GEN.cmd_convert(
                    self.convert_args(no_run=True, work_dir=None)
                ),
                0,
            )
        run_lc.assert_not_called()
        self.assertTrue((self.db_path.parent / "lc_work" / "unit.lc.tcl").is_file())
        self.assertFalse(self.db_path.with_suffix(".lc.tcl").exists())

    def test_convert_keep_tcl_retains_tcl_after_success(self) -> None:
        with mock.patch.object(LIB_DB_GEN, "run_lc_shell", side_effect=self.successful_lc):
            self.assertEqual(LIB_DB_GEN.cmd_convert(self.convert_args(keep_tcl=True)), 0)
        self.assertTrue(self.default_tcl.is_file())
        self.assertEqual(self.output_path_from_tcl(self.default_tcl), self.db_path.resolve())

    def test_explicit_tcl_obeys_default_cleanup(self) -> None:
        explicit_tcl = self.root / "commands" / "convert.tcl"

        def successful_explicit(_shell: str, tcl_path: Path, work_dir: Path) -> None:
            self.assertEqual(tcl_path, explicit_tcl)
            self.assertEqual(work_dir, self.work_dir)
            self.assertTrue(tcl_path.is_file())
            self.output_path_from_tcl(tcl_path).write_bytes(b"fake-db")

        with mock.patch.object(LIB_DB_GEN, "run_lc_shell", side_effect=successful_explicit):
            self.assertEqual(
                LIB_DB_GEN.cmd_convert(self.convert_args(tcl=str(explicit_tcl))),
                0,
            )
        self.assertFalse(explicit_tcl.exists())

    def test_stub_success_uses_same_cleanup_policy(self) -> None:
        top_v = self.root / "block.v"
        top_v.write_text(
            "module block(input logic clk, output logic done); endmodule\n",
            encoding="utf-8",
        )
        stub_lib = self.root / "stub" / "block.lib"
        stub_db = self.root / "stub" / "block.db"
        stub_work = self.root / "stub_work"
        expected_tcl = stub_work / "block.lc.tcl"
        args = argparse.Namespace(
            top_v=str(top_v),
            top="block",
            lib=str(stub_lib),
            db=str(stub_db),
            library_name=None,
            tcl=None,
            work_dir=str(stub_work),
            no_run=False,
            keep_tcl=False,
            lc_shell="lc_shell",
            dc_shell="dc_shell",
            shell_mode="lc",
        )

        def successful_stub(_shell: str, tcl_path: Path, work_dir: Path) -> None:
            self.assertEqual(tcl_path, expected_tcl)
            self.assertEqual(work_dir, stub_work)
            self.assertTrue(tcl_path.is_file())
            self.output_path_from_tcl(tcl_path).write_bytes(b"fake-db")

        with mock.patch.object(LIB_DB_GEN, "run_lc_shell", side_effect=successful_stub):
            self.assertEqual(LIB_DB_GEN.cmd_stub(args), 0)
        self.assertTrue(stub_lib.is_file())
        self.assertFalse(expected_tcl.exists())

    def test_convert_rejects_resolved_tcl_input_collision(self) -> None:
        alias = self.root / "unit-alias.lib"
        alias.symlink_to(self.lib_path)
        original = self.lib_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "path collision"):
            LIB_DB_GEN.cmd_convert(self.convert_args(tcl=str(alias)))
        self.assertEqual(self.lib_path.read_bytes(), original)

    def test_convert_rejects_tcl_db_collision(self) -> None:
        with self.assertRaisesRegex(ValueError, "path collision"):
            LIB_DB_GEN.cmd_convert(self.convert_args(tcl=str(self.db_path)))
        self.assertFalse(self.db_path.exists())

    def test_stub_rejects_tcl_top_input_collision(self) -> None:
        top_v = self.root / "collision.v"
        top_v.write_text(
            "module collision(input logic clk); endmodule\n",
            encoding="utf-8",
        )
        original = top_v.read_bytes()
        args = argparse.Namespace(
            top_v=str(top_v),
            top="collision",
            lib=str(self.root / "collision.lib"),
            db=str(self.root / "collision.db"),
            library_name=None,
            tcl=str(top_v),
            work_dir=str(self.root / "collision_work"),
            no_run=False,
            keep_tcl=False,
            lc_shell="lc_shell",
        )
        with self.assertRaisesRegex(ValueError, "path collision"):
            LIB_DB_GEN.cmd_stub(args)
        self.assertEqual(top_v.read_bytes(), original)
        self.assertFalse((self.root / "collision.lib").exists())

    def test_stub_rejects_tcl_db_collision(self) -> None:
        top_v = self.root / "collision_db.v"
        top_v.write_text(
            "module collision_db(input logic clk); endmodule\n",
            encoding="utf-8",
        )
        db_path = self.root / "collision_db.db"
        args = argparse.Namespace(
            top_v=str(top_v),
            top="collision_db",
            lib=str(self.root / "collision_db.lib"),
            db=str(db_path),
            library_name=None,
            tcl=str(db_path),
            work_dir=str(self.root / "collision_db_work"),
            no_run=False,
            keep_tcl=False,
            lc_shell="lc_shell",
        )
        with self.assertRaisesRegex(ValueError, "path collision"):
            LIB_DB_GEN.cmd_stub(args)
        self.assertFalse(db_path.exists())


class LibDbShellBackendTest(unittest.TestCase):
    """DC prefer + LC post-write SIGSEGV recovery (lc_shell crash-on-exit fix)."""

    def test_is_crash_exit(self) -> None:
        self.assertTrue(LIB_DB_GEN._is_crash_exit(-11))
        self.assertTrue(LIB_DB_GEN._is_crash_exit(139))
        self.assertTrue(LIB_DB_GEN._is_crash_exit(11))
        self.assertFalse(LIB_DB_GEN._is_crash_exit(0))
        self.assertFalse(LIB_DB_GEN._is_crash_exit(1))
        self.assertFalse(LIB_DB_GEN._is_crash_exit(2))
        self.assertFalse(LIB_DB_GEN._is_crash_exit(-9))
        self.assertFalse(LIB_DB_GEN._is_crash_exit(-15))

    def test_write_db_tcl_dc_enables_write_lib_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_path = root / "a.lib"
            lib_path.write_text("library (a) {\n}\n", encoding="utf-8")
            db_path = root / "a.db"
            tcl_path = root / "a.tcl"
            LIB_DB_GEN.write_db_tcl(lib_path, db_path, tcl_path, "a", backend="dc")
            text = tcl_path.read_text(encoding="utf-8")
            self.assertIn("enable_write_lib_mode", text)
            self.assertIn("read_lib", text)
            self.assertIn("write_lib", text)
            self.assertTrue(text.strip().endswith("exit"))

    def test_write_db_tcl_lc_omits_enable_write_lib_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_path = root / "a.lib"
            lib_path.write_text("library (a) {\n}\n", encoding="utf-8")
            db_path = root / "a.db"
            tcl_path = root / "a.tcl"
            LIB_DB_GEN.write_db_tcl(lib_path, db_path, tcl_path, "a", backend="lc")
            text = tcl_path.read_text(encoding="utf-8")
            self.assertNotIn("enable_write_lib_mode", text)

    def test_resolve_default_and_dc_mode_use_dc_shell(self) -> None:
        with mock.patch.object(
            LIB_DB_GEN,
            "_resolve_executable",
            side_effect=lambda name: f"/bin/{name}" if name else None,
        ):
            for mode in ("dc", "", None):
                backend, exe = LIB_DB_GEN.resolve_db_backend(
                    mode,  # type: ignore[arg-type]
                    lc_shell="lc_shell",
                    dc_shell="dc_shell",
                )
                self.assertEqual(backend, "dc")
                self.assertEqual(exe, "/bin/dc_shell")

    def test_resolve_auto_prefers_dc_when_both_present(self) -> None:
        with mock.patch.object(
            LIB_DB_GEN,
            "_resolve_executable",
            side_effect=lambda name: f"/bin/{name}" if name else None,
        ):
            backend, exe = LIB_DB_GEN.resolve_db_backend(
                "auto", lc_shell="lc_shell", dc_shell="dc_shell"
            )
        self.assertEqual(backend, "dc")
        self.assertEqual(exe, "/bin/dc_shell")

    def test_resolve_auto_falls_back_to_lc(self) -> None:
        def resolve(name: str) -> str | None:
            if name == "lc_shell":
                return "/bin/lc_shell"
            return None

        with mock.patch.object(LIB_DB_GEN, "_resolve_executable", side_effect=resolve):
            backend, exe = LIB_DB_GEN.resolve_db_backend(
                "auto", lc_shell="lc_shell", dc_shell="dc_shell"
            )
        self.assertEqual(backend, "lc")
        self.assertEqual(exe, "/bin/lc_shell")

    def test_run_db_shell_recovers_lc_sigsegv_when_db_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = root / "out.tmp.db"
            tcl = root / "c.tcl"
            tcl.write_text("exit\n", encoding="utf-8")
            work = root / "work"

            def fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
                staged.write_bytes(b"db-bytes")
                return mock.Mock(returncode=-11)

            with mock.patch.object(LIB_DB_GEN.subprocess, "run", side_effect=fake_run):
                LIB_DB_GEN.run_db_shell(
                    "lc_shell", tcl, work, staged, backend="lc"
                )
            self.assertTrue(staged.is_file())

    def test_run_db_shell_confines_crash_artifacts_to_work_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller_dir = root / "caller"
            caller_dir.mkdir()
            work = root / "output" / "lc_work"
            staged = root / "output" / "out.tmp.db"
            tcl = root / "convert.tcl"
            tcl.write_text("exit\n", encoding="utf-8")

            def fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
                self.assertEqual(Path(cwd), work)
                Path(cwd).mkdir(parents=True, exist_ok=True)
                (Path(cwd) / "Synopsys_stack_trace_123.txt").write_text(
                    "diagnostic\n", encoding="utf-8"
                )
                (Path(cwd) / "crte_000123.txt").write_text(
                    "diagnostic\n", encoding="utf-8"
                )
                staged.write_bytes(b"db-bytes")
                return mock.Mock(returncode=-11)

            with mock.patch.object(LIB_DB_GEN.subprocess, "run", side_effect=fake_run):
                LIB_DB_GEN.run_db_shell(
                    "lc_shell", tcl, work, staged, backend="lc"
                )

            self.assertTrue((work / "Synopsys_stack_trace_123.txt").is_file())
            self.assertTrue((work / "crte_000123.txt").is_file())
            self.assertEqual(list(caller_dir.iterdir()), [])

    def test_run_db_shell_does_not_mask_lc_functional_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = root / "out.tmp.db"
            staged.write_bytes(b"partial")
            tcl = root / "c.tcl"
            tcl.write_text("exit\n", encoding="utf-8")
            work = root / "work"

            with mock.patch.object(
                LIB_DB_GEN.subprocess,
                "run",
                return_value=mock.Mock(returncode=1),
            ):
                with self.assertRaisesRegex(RuntimeError, "failed with status 1"):
                    LIB_DB_GEN.run_db_shell(
                        "lc_shell", tcl, work, staged, backend="lc"
                    )

    def test_run_db_shell_lc_sigsegv_without_db_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = root / "missing.tmp.db"
            tcl = root / "c.tcl"
            tcl.write_text("exit\n", encoding="utf-8")
            work = root / "work"

            with mock.patch.object(
                LIB_DB_GEN.subprocess,
                "run",
                return_value=mock.Mock(returncode=-11),
            ):
                with self.assertRaisesRegex(RuntimeError, "failed with status -11"):
                    LIB_DB_GEN.run_db_shell(
                        "lc_shell", tcl, work, staged, backend="lc"
                    )

    def test_convert_lc_calledprocesserror_sigsegv_installs_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_path = root / "unit.lib"
            lib_path.write_text("library (unit_lib) {\n}\n", encoding="utf-8")
            db_path = root / "out" / "unit.db"
            work_dir = root / "lc_work"
            args = argparse.Namespace(
                lib=str(lib_path),
                db=str(db_path),
                library_name=None,
                tcl=None,
                work_dir=str(work_dir),
                no_run=False,
                keep_tcl=False,
                lc_shell="lc_shell",
                dc_shell="dc_shell",
                shell_mode="lc",
            )

            def crash_after_write(_shell: str, tcl_path: Path, _work: Path) -> None:
                text = tcl_path.read_text(encoding="utf-8")
                match = re.search(r'write_lib .* -format db -output "([^"]+)"', text)
                assert match is not None
                Path(match.group(1)).write_bytes(b"fake-db")
                raise subprocess.CalledProcessError(-11, ["lc_shell"])

            with mock.patch.object(
                LIB_DB_GEN, "run_lc_shell", side_effect=crash_after_write
            ):
                self.assertEqual(LIB_DB_GEN.cmd_convert(args), 0)
            self.assertTrue(db_path.is_file())
            self.assertEqual(db_path.read_bytes(), b"fake-db")


if __name__ == "__main__":
    unittest.main()
