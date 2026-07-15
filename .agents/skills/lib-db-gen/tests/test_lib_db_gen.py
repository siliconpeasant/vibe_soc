from __future__ import annotations

import argparse
import importlib.util
import re
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


if __name__ == "__main__":
    unittest.main()
