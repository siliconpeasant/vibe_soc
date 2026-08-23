#!/usr/bin/env python3
"""Closure checker for the integrate stage (filelist / extracted-map evidence)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def check(workspace: str, info: Optional[dict] = None) -> dict:
    root = Path(workspace).expanduser().resolve()
    artifacts = list((info or {}).get("artifacts") or [])
    issues: list[str] = []
    details = {"artifacts": artifacts, "filelists": []}

    has_filelist = False
    for rel in artifacts:
        path = (root / rel).resolve()
        if Path(rel).name in {"filelist.f", "filelist.mk"} and path.is_file() and path.stat().st_size > 0:
            has_filelist = True
            details["filelists"].append(rel)
        if rel.startswith("de/") and not path.is_file():
            issues.append(f"missing integrate artifact: {rel}")

    if not has_filelist:
        issues.append("integrate requires de/rtl/filelist.f or de/rtl/filelist.mk")

    return {
        "passed": not issues,
        "issues": issues,
        "details": details,
    }
