#!/usr/bin/env python3
"""Generate/check scripts/check_repo_hygiene.py from the reviewed v2 source."""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/check_repo_hygiene_v2.py"
TARGET = ROOT / "scripts/check_repo_hygiene.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify entrypoint (default)")
    mode.add_argument("--write", action="store_true", help="replace entrypoint from v2 source")
    args = parser.parse_args()

    try:
        expected = SOURCE.read_text(encoding="utf-8")
        if args.write:
            TARGET.write_text(expected, encoding="utf-8")
            TARGET.chmod(TARGET.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"[REPO-SYNC] Wrote {TARGET.relative_to(ROOT)}")
            return 0
        actual = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else ""
    except OSError as exc:
        print(f"[REPO-SYNC] ERROR: {exc}", file=sys.stderr)
        return 2

    if actual != expected or not TARGET.stat().st_mode & stat.S_IXUSR:
        print(f"[REPO-SYNC] OUT-OF-DATE: {TARGET.relative_to(ROOT)}", file=sys.stderr)
        print("Run: python3 scripts/sync_repo_hygiene_entrypoint.py --write", file=sys.stderr)
        return 2
    print("[REPO-SYNC] Hygiene entrypoint is synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
