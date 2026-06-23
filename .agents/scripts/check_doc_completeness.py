#!/usr/bin/env python3
"""Validate the canonical documentation deliverables for one module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_DOCS = (
    "design_spec.md",
    "interface_spec.md",
    "regmap.md",
    "verification_plan.md",
)


def check(workspace: str, module: str = "") -> dict:
    root = Path(workspace).expanduser().resolve()
    docs_dir = root / "docs" / module if module else root / "docs"
    results = {}
    issues = []
    for filename in REQUIRED_DOCS:
        path = docs_dir / filename
        exists = path.is_file()
        nonempty = exists and path.stat().st_size > 0
        has_heading = False
        if nonempty:
            first = next((line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()), "")
            has_heading = first.startswith("# ")
        rel = str(path.relative_to(root))
        results[filename] = {
            "path": rel,
            "exists": exists,
            "nonempty": nonempty,
            "has_heading": has_heading,
        }
        if not exists:
            issues.append(f"missing document: {rel}")
        elif not nonempty:
            issues.append(f"empty document: {rel}")
        elif not has_heading:
            issues.append(f"document must start with a Markdown heading: {rel}")
    return {"passed": not issues, "details": results, "issues": issues}


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
