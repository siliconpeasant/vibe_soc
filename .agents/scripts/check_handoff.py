#!/usr/bin/env python3
"""Validate frontend handoff artifacts. Does not accept timing-closure claims."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional


FILELIST_NAMES = {"filelist.f", "filelist.mk"}
FORMAL_NAMES = {
    "formality.log",
    "fm_shell.log",
    "verification_status.rpt",
    "match_status.rpt",
}
SUCCEEDED = re.compile(
    r"(?:VERIFICATION_STATUS\s*=\s*SUCCEEDED|Verification\s+SUCCEEDED)",
    re.I,
)
FAILED_STATUS = re.compile(r"VERIFICATION_STATUS\s*=\s*(FAILED|INCONCLUSIVE)", re.I)


def _rel_ok(rel: str, root: Path) -> tuple[bool, str]:
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False, f"artifact outside workspace: {rel}"
    if not path.is_file():
        return False, f"missing handoff artifact: {rel}"
    if path.stat().st_size == 0:
        return False, f"empty handoff artifact: {rel}"
    return True, ""


def _is_filelist(rel: str) -> bool:
    return rel.startswith("de/rtl/") and Path(rel).name in FILELIST_NAMES


def _is_netlist(rel: str) -> bool:
    name = Path(rel).name
    return rel.startswith("de/syn/") and (
        name.endswith("_netlist.v") or name.endswith("_netlist.sv")
    )


def _is_sdc(rel: str) -> bool:
    return rel.startswith("de/syn/") and Path(rel).name.endswith(".sdc")


def _is_formal(rel: str) -> bool:
    name = Path(rel).name
    return (
        rel.startswith("de/run/formality/")
        or "/formality/" in rel
        or name in FORMAL_NAMES
    )


def _is_note(rel: str) -> bool:
    name = Path(rel).name.lower()
    return (rel.startswith("docs/") and name.endswith(".md") and "handoff" in name) or (
        "handoff" in name and name.endswith((".md", ".txt"))
    )


def _discover(root: Path) -> list[str]:
    found: list[str] = []
    for name in ("filelist.f", "filelist.mk"):
        rel = f"de/rtl/{name}"
        if (root / rel).is_file():
            found.append(rel)
    syn = root / "de" / "syn"
    if syn.is_dir():
        preferred_netlists = [
            path
            for path in (
                syn / f"{root.name}_netlist.v",
                syn / f"{root.name}_netlist.sv",
            )
            if path.is_file()
        ]
        if preferred_netlists:
            found.extend(f"de/syn/{path.name}" for path in preferred_netlists)
        else:
            found.extend(
                f"de/syn/{path.name}"
                for path in sorted(list(syn.glob("*_netlist.v")) + list(syn.glob("*_netlist.sv")))
                if path.is_file()
            )
        preferred_sdc = syn / f"{root.name}.sdc"
        if preferred_sdc.is_file():
            found.append(f"de/syn/{preferred_sdc.name}")
        else:
            found.extend(
                f"de/syn/{path.name}"
                for path in sorted(syn.glob("*.sdc"))
                if path.is_file()
            )
    formal_dir = root / "de" / "run" / "formality"
    for name in ("verification_status.rpt", "formality.log", "match_status.rpt"):
        rel = f"de/run/formality/{name}"
        if (formal_dir / name).is_file():
            found.append(rel)
    docs = root / "docs"
    if docs.is_dir():
        found.extend(
            path.relative_to(root).as_posix()
            for path in sorted(docs.rglob("*handoff*.md"))
            if path.is_file()
        )
    return found


def _load_recorded_artifacts(root: Path) -> list[str]:
    state_path = root / "pipeline_state.json"
    if not state_path.is_file():
        return []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    containers = []
    if state.get("mode") == "multi_module":
        modules = state.get("modules") or {}
        containers.extend(modules.values())
    else:
        containers.append(state)
    for container in containers:
        artifacts = ((container.get("pipeline") or {}).get("handoff") or {}).get(
            "artifacts"
        ) or []
        if artifacts:
            return [str(item) for item in artifacts]
    return []


def check(workspace: str, info: Optional[dict] = None) -> dict:
    root = Path(workspace).expanduser().resolve()
    artifacts = [str(item) for item in ((info or {}).get("artifacts") or [])]
    discovered = False
    if not artifacts:
        artifacts = _load_recorded_artifacts(root) or _discover(root)
        discovered = True

    details = {
        "artifacts": artifacts,
        "discovered": discovered,
        "filelists": [],
        "netlists": [],
        "sdcs": [],
        "formal_reports": [],
        "notes": [],
        "formal_succeeded": False,
    }
    issues: list[str] = []

    filelists = [rel for rel in artifacts if _is_filelist(rel)]
    netlists = [rel for rel in artifacts if _is_netlist(rel)]
    sdcs = [rel for rel in artifacts if _is_sdc(rel)]
    formal = [rel for rel in artifacts if _is_formal(rel)]
    notes = [rel for rel in artifacts if _is_note(rel)]
    details.update(
        {
            "filelists": filelists,
            "netlists": netlists,
            "sdcs": sdcs,
            "formal_reports": formal,
            "notes": notes,
        }
    )

    if not filelists:
        issues.append("handoff requires de/rtl/filelist.f or de/rtl/filelist.mk")
    if not netlists:
        issues.append("handoff requires a de/syn/*_netlist.v artifact")
    if not sdcs:
        issues.append("handoff requires a de/syn/*.sdc artifact")
    if not formal:
        issues.append("handoff requires a Formality report under de/run/formality/")
    if not notes:
        issues.append("handoff requires a docs/*handoff*.md delivery note")

    for rel in filelists + netlists + sdcs + formal + notes:
        ok, message = _rel_ok(rel, root)
        if not ok:
            issues.append(message)

    succeeded = False
    for rel in formal:
        path = root / rel
        if not path.is_file() or path.stat().st_size == 0:
            continue
        text = path.read_text(errors="replace")
        if FAILED_STATUS.search(text):
            issues.append(f"{rel}: Formality status is not SUCCEEDED")
            continue
        if SUCCEEDED.search(text):
            succeeded = True
        elif Path(rel).name == "verification_status.rpt":
            issues.append(f"{rel}: Formality verification_status.rpt does not record SUCCEEDED")
    details["formal_succeeded"] = succeeded
    if formal and not succeeded:
        issues.append("formal report does not contain SUCCEEDED")

    return {"passed": not issues, "details": details, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    args = parser.parse_args()
    result = check(args.workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
