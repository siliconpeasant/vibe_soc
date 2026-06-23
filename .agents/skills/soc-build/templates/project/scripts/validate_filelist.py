#!/usr/bin/env python3
"""Validate, flatten and de-duplicate a Verilog filelist."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path


SOURCE_SUFFIXES = {".v", ".sv", ".vh", ".svh", ".vp", ".vlib", ".svi", ".vt"}


class FilelistValidator:
    def __init__(self) -> None:
        self.output: list[str] = []
        self.seen_entries: set[tuple[str, str]] = set()
        self.visited: set[Path] = set()
        self.stack: list[Path] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @staticmethod
    def expand(value: str, base: Path) -> Path:
        expanded = os.path.expandvars(value)
        path = Path(expanded).expanduser()
        return (base / path).resolve() if not path.is_absolute() else path.resolve()

    def add(self, kind: str, value: str, rendered: str) -> None:
        key = (kind, value)
        if key in self.seen_entries:
            self.warnings.append(f"duplicate {kind}: {value}")
            return
        self.seen_entries.add(key)
        self.output.append(rendered)

    def parse(self, filelist: Path) -> None:
        filelist = filelist.resolve()
        if filelist in self.stack:
            cycle = " -> ".join(str(p) for p in [*self.stack, filelist])
            self.errors.append(f"filelist include cycle: {cycle}")
            return
        if filelist in self.visited:
            self.warnings.append(f"duplicate filelist include: {filelist}")
            return
        if not filelist.is_file():
            self.errors.append(f"missing filelist: {filelist}")
            return

        self.visited.add(filelist)
        self.stack.append(filelist)
        base = filelist.parent

        for line_no, raw_line in enumerate(filelist.read_text(errors="replace").splitlines(), 1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            try:
                tokens = shlex.split(raw_line, comments=True, posix=True)
            except ValueError as exc:
                self.errors.append(f"{filelist}:{line_no}: {exc}")
                continue

            index = 0
            while index < len(tokens):
                token = tokens[index]
                if token == "-f":
                    if index + 1 >= len(tokens):
                        self.errors.append(f"{filelist}:{line_no}: -f requires a path")
                        break
                    self.parse(self.expand(tokens[index + 1], base))
                    index += 2
                    continue
                if token.startswith("-f") and len(token) > 2:
                    self.parse(self.expand(token[2:], base))
                    index += 1
                    continue
                if token.startswith("+incdir+"):
                    directories = token[len("+incdir+") :].split("+")
                    resolved: list[str] = []
                    for directory in directories:
                        path = self.expand(directory, base)
                        if not path.is_dir():
                            self.errors.append(f"{filelist}:{line_no}: missing include dir: {path}")
                        resolved.append(str(path))
                    value = "+".join(resolved)
                    self.add("incdir", value, f"+incdir+{value}")
                    index += 1
                    continue
                if token in {"-y", "-v"}:
                    if index + 1 >= len(tokens):
                        self.errors.append(f"{filelist}:{line_no}: {token} requires a path")
                        break
                    path = self.expand(tokens[index + 1], base)
                    expected = path.is_dir() if token == "-y" else path.is_file()
                    if not expected:
                        self.errors.append(f"{filelist}:{line_no}: missing {token} path: {path}")
                    self.add(token, str(path), f"{token} {shlex.quote(str(path))}")
                    index += 2
                    continue
                if token.startswith(("+", "-")):
                    self.add("option", token, token)
                    index += 1
                    continue

                path = self.expand(token, base)
                if path.suffix.lower() in SOURCE_SUFFIXES or "." in path.name:
                    if not path.is_file():
                        self.errors.append(f"{filelist}:{line_no}: missing source: {path}")
                    self.add("source", str(path), shlex.quote(str(path)))
                else:
                    self.add("token", token, token)
                index += 1

        self.stack.pop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filelist", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    validator = FilelistValidator()
    validator.parse(args.filelist)

    for warning in validator.warnings:
        print(f"[FLIST] WARNING: {warning}", file=sys.stderr)
    if validator.errors:
        for error in validator.errors:
            print(f"[FLIST] ERROR: {error}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("// Auto-generated canonical filelist\n" + "\n".join(validator.output) + "\n")
    print(
        f"[FLIST] Validated {len(validator.visited)} filelist(s), "
        f"emitted {len(validator.output)} unique entries: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

