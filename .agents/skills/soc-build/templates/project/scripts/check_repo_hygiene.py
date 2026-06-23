#!/usr/bin/env python3
"""Reject tracked or pending files that expose local paths or license endpoints."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def repository_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [root / item.decode(errors="surrogateescape") for item in completed.stdout.split(b"\0") if item]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    self_path = Path(__file__).resolve()

    personal_paths = [
        re.compile("/" + r"Users/[^/\s]+/"),
        re.compile("/" + r"home/[^/\s]+/"),
        re.compile("/" + r"project/[^/\s]+/"),
        re.compile(r"[A-Za-z]:\\(?:Users\\)?[^\\\s]+\\"),
    ]
    license_endpoint = re.compile(
        r"(?:SNPSLMD_LICENSE_FILE|LM_LICENSE_FILE|CDS_LIC_FILE)\s*[:?+]?=\s*[\"']?\d+@[A-Za-z0-9_.-]+"
    )

    findings: list[tuple[Path, int, str]] = []
    for path in repository_files(root):
        if path.resolve() == self_path or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        for line_no, line in enumerate(data.decode(errors="replace").splitlines(), 1):
            if any(pattern.search(line) for pattern in personal_paths):
                findings.append((path, line_no, "personal absolute path"))
            if license_endpoint.search(line):
                findings.append((path, line_no, "license endpoint"))

    if findings:
        for path, line_no, kind in findings:
            print(f"[REPO] ERROR: {path.relative_to(root)}:{line_no}: {kind}")
        return 2

    print(f"[REPO] Hygiene passed: scanned {len(repository_files(root))} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
