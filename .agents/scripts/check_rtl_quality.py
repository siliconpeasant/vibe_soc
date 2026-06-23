#!/usr/bin/env python3
"""Validate canonical RTL layout, filelist integrity and basic module syntax."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
from pathlib import Path


RTL_SUFFIXES = {".v", ".sv"}


def _project_root(workspace: Path) -> Path:
    for candidate in (workspace, *workspace.parents):
        if (candidate / "chip").is_dir() and (candidate / "ip").is_dir():
            return candidate
    return workspace


def _resolve_source(token: str, filelist: Path, workspace: Path) -> Path:
    project_root = Path(os.environ.get("SOC", _project_root(workspace)))
    expanded = os.path.expandvars(token).replace("$SOC", str(project_root))
    path = Path(expanded).expanduser()
    return path.resolve() if path.is_absolute() else (filelist.parent / path).resolve()


def check(workspace: str, module: str = "") -> dict:
    root = Path(workspace).expanduser().resolve()
    rtl_dir = root / "de" / "rtl"
    filelist = rtl_dir / "filelist.f"
    details = {"filelist": str(filelist), "rtl_files": [], "modules": []}
    issues = []

    if not filelist.is_file():
        return {
            "passed": False,
            "details": details,
            "issues": ["missing canonical filelist: de/rtl/filelist.f"],
        }

    sources = []
    for line_no, raw in enumerate(filelist.read_text(errors="replace").splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "//", "+", "-")):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError as exc:
            issues.append(f"filelist.f:{line_no}: {exc}")
            continue
        for token in tokens:
            if Path(token).suffix.lower() not in RTL_SUFFIXES:
                continue
            source = _resolve_source(token, filelist, root)
            sources.append(source)
            exists = source.is_file()
            details["rtl_files"].append({"file": str(source), "exists": exists})
            if not exists:
                issues.append(f"missing RTL source from filelist: {source}")

    if not sources:
        issues.append("de/rtl/filelist.f contains no Verilog/SystemVerilog sources")

    declared_modules = []
    for source in sorted({path for path in sources if path.is_file()}):
        content = source.read_text(errors="replace")
        modules = re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", content)
        if not modules:
            issues.append(f"no module declaration found: {source}")
        declared_modules.extend(modules)
    details["modules"] = declared_modules

    if module and module not in declared_modules:
        issues.append(f"expected module '{module}' is not present in the filelist")

    misplaced_sdc = sorted(rtl_dir.rglob("*.sdc")) if rtl_dir.is_dir() else []
    for path in misplaced_sdc:
        issues.append(f"SDC must be under de/syn, not de/rtl: {path}")

    return {"passed": not issues, "details": details, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("--module", default="")
    args = parser.parse_args()
    result = check(args.workspace, args.module)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
