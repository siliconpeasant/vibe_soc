#!/usr/bin/env python3
"""Compute a stable build fingerprint from sources, config and command metadata."""

from __future__ import annotations

import argparse
import hashlib
import shlex
from pathlib import Path


def hash_file(digest: "hashlib._Hash", path: Path) -> None:
    digest.update(str(path.resolve()).encode())
    digest.update(b"\0")
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--filelist", type=Path, required=True)
    parser.add_argument("--metadata", default="")
    parser.add_argument("--extra", type=Path, action="append", default=[])
    args = parser.parse_args()

    digest = hashlib.sha256()
    digest.update(args.metadata.encode())
    digest.update(b"\0")
    hash_file(digest, args.filelist)

    for raw_line in args.filelist.read_text(errors="replace").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("#", "//", "+", "-")):
            continue
        for token in shlex.split(raw_line, comments=True, posix=True):
            path = Path(token)
            if path.is_file():
                hash_file(digest, path)

    for extra in args.extra:
        if extra.is_file():
            hash_file(digest, extra)
        elif extra.is_dir():
            for path in sorted(item for item in extra.rglob("*") if item.is_file()):
                hash_file(digest, path)

    print(digest.hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
