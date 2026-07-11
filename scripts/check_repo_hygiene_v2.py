#!/usr/bin/env python3
"""High-signal repository privacy/license hygiene gate.

The default scope inspects only lines added in staged and unstaged diffs plus
complete untracked files. Use --all for an explicit whole-repository audit.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


BASELINE_ALLOWLIST: tuple[tuple[str, str], ...] = (
    ("**/de/rtl/vendor/**", "vendored RTL baseline"),
    ("**/de/rtl/generated/**", "generated RTL baseline"),
    ("ip/digital/aes/de/rtl/src/**", "imported OpenTitan AES baseline"),
    ("chip/top/dv/tb/tests/opentitan_*.json", "generated OpenTitan test index"),
    ("chip/top/dv/tb/sw/**/manifest.json", "imported OpenTitan software manifest"),
    ("chip/top/docs/opentitan_case_migration_manifest.json", "generated migration manifest"),
)

ABSOLUTE_PATH_BOUNDARY = r"(?<![A-Za-z0-9_.-])"
PERSONAL_PATHS = (
    re.compile(ABSOLUTE_PATH_BOUNDARY + "/" + r"Users/[^/\s]+/"),
    re.compile(ABSOLUTE_PATH_BOUNDARY + "/" + r"home/[^/\s]+/"),
    re.compile(ABSOLUTE_PATH_BOUNDARY + "/" + r"project/[^/\s]+/"),
    re.compile(r"[A-Za-z]:\\(?:Users\\)?[^\\\s]+\\"),
)
LICENSE_ENDPOINT = re.compile(
    r"(?:SNPSLMD_LICENSE_FILE|LM_LICENSE_FILE|CDS_LIC_FILE)\s*[:?+]?=\s*[\"']?\d+@[A-Za-z0-9_.-]+"
)
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
WORKSPACE_LINE = re.compile(r'^\s*"workspace"\s*:\s*("(?:[^"\\]|\\.)*")\s*,?\s*$')


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line_no: int
    kind: str


def _git_bytes(root: Path, arguments: list[str]) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _git_paths(root: Path, arguments: list[str]) -> set[str]:
    return {
        item.decode(errors="surrogateescape")
        for item in _git_bytes(root, [*arguments, "-z"]).split(b"\0")
        if item
    }


def repository_files(root: Path) -> set[str]:
    return _git_paths(root, ["ls-files", "--cached", "--others", "--exclude-standard"])


def changed_path_groups(root: Path) -> tuple[set[str], set[str], set[str]]:
    unstaged = _git_paths(root, ["diff", "--name-only", "--diff-filter=ACMR"])
    staged = _git_paths(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard"])
    return unstaged, staged, untracked


def _safe_path(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _is_allowlisted(relative: str, patterns: Iterable[str]) -> str | None:
    for pattern, reason in BASELINE_ALLOWLIST:
        if fnmatch.fnmatchcase(relative, pattern):
            return reason
    for pattern in patterns:
        if fnmatch.fnmatchcase(relative, pattern):
            return "command-line allowlist"
    return None


def _file_lines(path: Path) -> Iterator[tuple[int, str]]:
    if not path.is_file():
        return
    data = path.read_bytes()
    if b"\0" in data:
        return
    for line_no, line in enumerate(data.decode(errors="replace").splitlines(), 1):
        yield line_no, line


def _added_lines(root: Path, relative: str, *, cached: bool) -> Iterator[tuple[int, str]]:
    command = ["diff"]
    if cached:
        command.append("--cached")
    command.extend(["--no-ext-diff", "--no-color", "--unified=0", "--", relative])
    text = _git_bytes(root, command).decode(errors="replace")
    current_line: int | None = None
    for line in text.splitlines():
        header = HUNK_HEADER.match(line)
        if header:
            current_line = int(header.group(1))
            continue
        if current_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield current_line, line[1:]
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        elif line.startswith(" "):
            current_line += 1


def _workspace_allow_lines(path: Path) -> set[int]:
    if path.name != "pipeline_state.json" or not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    if not isinstance(payload, dict):
        return set()
    if payload.get("mode") not in {"single", "multi_module"}:
        return set()
    if not isinstance(payload.get("workspace"), str):
        return set()
    if "pipeline" not in payload and "modules" not in payload:
        return set()

    expected = payload["workspace"]
    for line_no, line in _file_lines(path):
        match = WORKSPACE_LINE.match(line)
        if match:
            try:
                value = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if value == expected:
                return {line_no}
    return set()


def _findings_for_lines(
    relative: str,
    lines: Iterable[tuple[int, str]],
    workspace_allow_lines: set[int],
) -> Iterator[Finding]:
    for line_no, line in lines:
        if line_no not in workspace_allow_lines and any(pattern.search(line) for pattern in PERSONAL_PATHS):
            yield Finding(relative, line_no, "personal absolute path")
        if LICENSE_ENDPOINT.search(line):
            yield Finding(relative, line_no, "license endpoint")


def scan_repository(
    root: Path,
    *,
    scan_all: bool,
    allow_patterns: Iterable[str],
    max_findings: int,
    show_skipped: bool,
) -> tuple[list[Finding], int, int]:
    self_path = Path(__file__).resolve()
    findings: set[Finding] = set()
    scanned_paths: set[str] = set()
    skipped = 0

    def accept_path(relative: str) -> Path | None:
        nonlocal skipped
        path = _safe_path(root, relative)
        if path is None or path == self_path or not path.is_file():
            return None
        reason = _is_allowlisted(relative, allow_patterns)
        if reason:
            skipped += 1
            if show_skipped:
                print(f"[REPO] SKIP: {relative}: {reason}")
            return None
        scanned_paths.add(relative)
        return path

    if scan_all:
        for relative in sorted(repository_files(root)):
            path = accept_path(relative)
            if path is None:
                continue
            findings.update(
                _findings_for_lines(relative, _file_lines(path), _workspace_allow_lines(path))
            )
            if len(findings) >= max_findings:
                break
    else:
        unstaged, staged, untracked = changed_path_groups(root)
        for cached, paths in ((False, unstaged), (True, staged)):
            for relative in sorted(paths):
                path = accept_path(relative)
                if path is None:
                    continue
                findings.update(
                    _findings_for_lines(
                        relative,
                        _added_lines(root, relative, cached=cached),
                        _workspace_allow_lines(path),
                    )
                )
                if len(findings) >= max_findings:
                    break
            if len(findings) >= max_findings:
                break
        if len(findings) < max_findings:
            for relative in sorted(untracked):
                path = accept_path(relative)
                if path is None:
                    continue
                findings.update(
                    _findings_for_lines(relative, _file_lines(path), _workspace_allow_lines(path))
                )
                if len(findings) >= max_findings:
                    break

    return sorted(findings)[:max_findings], len(scanned_paths), skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--diff-only", action="store_true", help="scan added/pending lines (default)")
    scope.add_argument("--all", action="store_true", help="scan every tracked and untracked file")
    parser.add_argument(
        "--allow-path",
        action="append",
        default=[],
        metavar="GLOB",
        help="additional repository-relative path glob to skip; may be repeated",
    )
    parser.add_argument("--max-findings", type=int, default=100)
    parser.add_argument("--show-skipped", action="store_true")
    args = parser.parse_args()
    if args.max_findings <= 0:
        parser.error("--max-findings must be positive")

    root = args.root.resolve()
    try:
        findings, scanned, skipped = scan_repository(
            root,
            scan_all=args.all,
            allow_patterns=args.allow_path,
            max_findings=args.max_findings,
            show_skipped=args.show_skipped,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[REPO] ERROR: hygiene scan failed: {exc}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(f"[REPO] ERROR: {finding.path}:{finding.line_no}: {finding.kind}")
        print(
            f"[REPO] Hygiene failed: {len(findings)} finding(s), "
            f"scanned {scanned} file(s), skipped {skipped} allowlisted file(s)"
        )
        return 2

    scope_name = "all" if args.all else "diff-only"
    print(
        f"[REPO] Hygiene passed ({scope_name}): scanned {scanned} file(s), "
        f"skipped {skipped} allowlisted file(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
