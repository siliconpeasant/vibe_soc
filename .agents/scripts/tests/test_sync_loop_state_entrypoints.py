from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "sync_loop_state_entrypoints.py"
SPEC = importlib.util.spec_from_file_location("sync_loop_state_entrypoints", SCRIPT)
sync_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_module)


class SyncEntrypointsTest(unittest.TestCase):
    def test_generation_is_deterministic_and_checkable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            changed = sync_module.sync(root)
            self.assertEqual(len(changed), 6)
            scripts = root / ".agents" / "scripts"
            for name, expected in sync_module.ENTRYPOINTS.items():
                self.assertEqual(
                    (scripts / name).read_text(encoding="utf-8"), expected
                )
                self.assertEqual(
                    (scripts / name).stat().st_mode & 0o777,
                    sync_module.ENTRYPOINT_MODES[name],
                )
            self.assertEqual(sync_module.sync(root, check=True), [])
            (scripts / "query_state.py").write_text("drift\n", encoding="utf-8")
            self.assertEqual(
                sync_module.sync(root, check=True),
                [".agents/scripts/query_state.py"],
            )

    def test_check_is_read_only_for_an_empty_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(
                len(sync_module.sync(root, check=True)),
                len(sync_module.ENTRYPOINTS),
            )
            self.assertFalse((root / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
