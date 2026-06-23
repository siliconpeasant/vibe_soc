#!/usr/bin/env python3
"""Validate simulation logs without synthetic PASS sentinels."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SUCCESS_PATTERNS = (
    re.compile(r"RESULT:\s*ALL TESTS PASS", re.I),
    re.compile(r"\bALL PASSED\b", re.I),
    re.compile(r"\bTOTAL=\d+\s+PASS=\d+\s+FAIL=0\b", re.I),
)
FAIL_PATTERNS = (
    re.compile(r"\[(?:ERROR|FAIL|FATAL)\]", re.I),
    re.compile(r"\bFATAL\b", re.I),
    re.compile(r"RESULT:\s*(?:FAIL|FAILED|TESTS FAILED)", re.I),
    re.compile(r"(?:ERRORS?|MISMATCH(?:ES)?)\s*[:=]\s*[1-9]\d*", re.I),
    re.compile(r"\bFAIL(?:ED)?\s*[:=]\s*[1-9]\d*", re.I),
)


def _resolve_logs(root: Path, requested: list[str]) -> list[Path]:
    if requested:
        logs = []
        for item in requested:
            path = Path(item).expanduser()
            path = path.resolve() if path.is_absolute() else (root / path).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"log must be inside workspace: {path}") from exc
            logs.append(path)
        return logs

    sim_dir = root / "dv" / "sim"
    candidates = [sim_dir / "sim.log"]
    candidates.extend(sorted(sim_dir.glob("tb_*.log")))
    candidates.extend(sorted((sim_dir / "regress").glob("**/*.log")))
    existing = [path for path in candidates if path.is_file()]
    return [max(existing, key=lambda path: path.stat().st_mtime)] if existing else []


def check(workspace: str, logs: list[str] | None = None) -> dict:
    root = Path(workspace).expanduser().resolve()
    requested = logs or []
    log_paths = _resolve_logs(root, requested)
    details = {"logs_checked": [], "success_markers": 0, "failures": []}
    issues = []
    if not log_paths:
        return {
            "passed": False,
            "details": details,
            "issues": ["no simulation log found under dv/sim"],
        }

    for log in log_paths:
        if not log.is_file():
            issues.append(f"simulation log not found: {log}")
            continue
        content = log.read_text(errors="replace")
        details["logs_checked"].append(str(log.relative_to(root)))
        successes = sum(len(pattern.findall(content)) for pattern in SUCCESS_PATTERNS)
        details["success_markers"] += successes
        for pattern in FAIL_PATTERNS:
            for match in pattern.finditer(content):
                failure = f"{log.name}: {match.group(0)}"
                details["failures"].append(failure)
                issues.append(failure)
        if successes == 0:
            issues.append(f"{log.name}: missing explicit simulation PASS result")

    return {"passed": not issues, "details": details, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("--log", action="append", default=[])
    args = parser.parse_args()
    result = check(args.workspace, args.log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
