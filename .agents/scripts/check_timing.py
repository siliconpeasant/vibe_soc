#!/usr/bin/env python3
"""Validate a real STA timing report; estimated timing is never accepted."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


UNVERIFIED_MARKERS = re.compile(r"estimated|estimate|估算|generic\s+timing", re.I)


def check(workspace: str, report: str = "") -> dict:
    root = Path(workspace).expanduser().resolve()
    path = Path(report).expanduser() if report else root / "de" / "syn" / "timing.rpt"
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    details = {"report": str(path), "wns": None, "tns": None}
    issues = []
    if not path.is_file():
        return {"passed": False, "details": details, "issues": [f"timing report not found: {path}"]}

    content = path.read_text(errors="replace")
    if UNVERIFIED_MARKERS.search(content):
        issues.append("estimated/generic timing is not valid STA evidence")

    wns_match = re.search(r"WNS\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)", content, re.I)
    tns_match = re.search(r"TNS\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)", content, re.I)
    if wns_match:
        details["wns"] = float(wns_match.group(1))
    else:
        issues.append("WNS not found in timing report")
    if tns_match:
        details["tns"] = float(tns_match.group(1))
    else:
        issues.append("TNS not found in timing report")
    if details["wns"] is not None and details["wns"] < 0:
        issues.append(f"timing not met: WNS={details['wns']} ns")

    return {"passed": not issues, "details": details, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    result = check(args.workspace, args.report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
